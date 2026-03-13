# api.py
import os
import uuid
import shutil
import time
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List

from config import Config
from kb.parser import DocumentParser
from kb.vector_store import KnowledgeBase
from orchestrator.classifier import IntentClassifier
from utils.database import Database

# 初始化FastAPI
app = FastAPI(title="IntelliKnow KMS API", description="AI驱动的知识管理系统", version="1.0.0")

# 允许跨域（供Streamlit前端调用）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化各模块
print("\n" + "="*50)
print("🚀 启动 IntelliKnow KMS API")
print("="*50)
kb = KnowledgeBase("intelliknow")
classifier = IntentClassifier()
parser = DocumentParser()
db = Database()
print("="*50 + "\n")

# 请求/响应模型
class QueryRequest(BaseModel):
    query: str
    platform: Optional[str] = "api"

class QueryResponse(BaseModel):
    query: str
    intent: dict
    response: str
    sources: list

class UploadResponse(BaseModel):
    filename: str
    doc_id: str
    chunks: int
    intent: str
    status: str

# API端点
@app.get("/")
async def root():
    return {"message": "IntelliKnow KMS API", "status": "running"}

@app.get("/health")
async def health():
    """健康检查接口"""
    return {
        "status": "healthy",
        "kb_stats": kb.get_stats(),
        "db_stats": db.get_query_stats()
    }

@app.post("/upload", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)):
    """上传并处理文档"""
    # 检查文件格式
    allowed_extensions = ['.pdf', '.docx', '.txt']
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in allowed_extensions:
        raise HTTPException(400, f"不支持的文件格式: {ext}")

    print(f"\n📤 收到上传请求: {file.filename}")

    # 保存文件
    doc_id = str(uuid.uuid4())[:8]
    safe_filename = f"{doc_id}{ext}"
    file_path = os.path.join(Config.DOCUMENTS_PATH, safe_filename)

    try:
        # 保存上传的文件
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        print(f"   文件已保存: {file_path}")

        # 解析文档
        parse_result = parser.parse(file_path)
        print(f"   解析完成: {len(parse_result['text'])} 字符")

        # 简单意图判断（基于文件名）
        intent = "General"
        filename_lower = file.filename.lower()
        if "hr" in filename_lower or "人力" in filename_lower or "员工" in filename_lower:
            intent = "HR"
        elif "finance" in filename_lower or "财务" in filename_lower or "报销" in filename_lower:
            intent = "Finance"
        elif "legal" in filename_lower or "法务" in filename_lower or "合同" in filename_lower:
            intent = "Legal"

        print(f"   意图分类: {intent}")

        # 添加到知识库
        result = kb.add_document(parse_result["text"], file.filename, intent)

        # 保存文档元数据到数据库
        db.add_document_meta(
            doc_id=result["doc_id"],
            filename=file.filename,
            title=file.filename,
            intent=intent,
            chunk_count=result["chunks"],
            file_size=parse_result["file_size"],
            metadata={"ext": ext}
        )

        print(f"✅ 文档处理成功: {result['chunks']} 个分块")

        return UploadResponse(
            filename=file.filename,
            doc_id=result["doc_id"],
            chunks=result["chunks"],
            intent=intent,
            status="success"
        )

    except Exception as e:
        # 清理失败的文件
        if os.path.exists(file_path):
            os.remove(file_path)
        print(f"❌ 处理失败: {str(e)}")
        raise HTTPException(500, f"处理失败: {str(e)}")

@app.post("/query", response_model=QueryResponse)
async def query_knowledge(request: QueryRequest):
    """处理查询请求"""
    start_time = time.time()
    query = request.query
    platform = request.platform

    print(f"\n📝 收到查询: '{query}' (平台: {platform})")

    # 1. 意图分类
    intent_result = classifier.classify(query)
    print(f"   意图: {intent_result['intent']} (置信度: {intent_result['confidence']:.2f})")

    # 2. 知识库检索
    search_results = kb.search(
        query,
        k=3,
        intent_filter=intent_result["intent"] if intent_result["intent"] != "General" else None
    )
    print(f"   找到 {len(search_results)} 个相关文档块")

    # 3. 构建上下文
    context = "\n\n".join([r["text"] for r in search_results]) if search_results else "未找到相关信息。"

    # 4. 调用Qwen生成回答
    client = Config.get_qwen_client()
    prompt = f"""基于以下背景知识，回答用户的问题。如果背景知识中没有相关信息，请如实说明。

背景知识：
{context}

用户问题：{query}
意图类别：{intent_result['intent']}

请提供准确、简洁的回答："""

    try:
        response = client.chat.completions.create(
            model=Config.QWEN_CHAT_MODEL,
            messages=[
                {"role": "system", "content": "你是一个专业的知识库助手，基于提供的信息回答问题。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        answer = response.choices[0].message.content
        print(f"   回答生成完成 ({len(answer)} 字符)")
    except Exception as e:
        answer = f"生成回答失败: {str(e)}"
        print(f"   ⚠️ 回答生成失败: {e}")

    response_time = time.time() - start_time

    # 5. 记录日志
    db.log_query(
        query=query,
        intent=intent_result["intent"],
        confidence=intent_result["confidence"],
        response=answer,
        source_docs=[s["filename"] for s in search_results],
        platform=platform,
        response_time=response_time
    )
    print(f"   处理完成，耗时: {response_time:.2f}秒")

    return QueryResponse(
        query=query,
        intent=intent_result,
        response=answer,
        sources=search_results
    )

@app.get("/documents")
async def get_documents():
    """获取文档列表"""
    return db.get_documents()

@app.get("/stats")
async def get_stats():
    """获取统计信息"""
    return {
        "kb_stats": kb.get_stats(),
        "query_stats": db.get_query_stats()
    }

# 如果直接运行此文件，启动服务器
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)





# # api.py
# from fastapi import FastAPI, UploadFile, File, HTTPException
# from fastapi.middleware.cors import CORSMiddleware
# from pydantic import BaseModel
# import shutil
# import os
# import uuid
# from datetime import datetime
# from typing import Optional

# from config import Config
# from kb.parser import DocumentParser
# from kb.vector_store import VectorKnowledgeBase
# from orchestrator.classifier import IntentClassifier

# # 初始化
# app = FastAPI(title="IntelliKnow KMS API")

# # 允许跨域请求（供Streamlit前端调用）
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # 初始化各模块
# kb = VectorKnowledgeBase("intelliknow")
# classifier = IntentClassifier()
# parser = DocumentParser()

# # 请求/响应模型
# class QueryRequest(BaseModel):
#     query: str

# class QueryResponse(BaseModel):
#     query: str
#     intent: dict
#     response: str
#     sources: list

# class UploadResponse(BaseModel):
#     filename: str
#     doc_id: str
#     chunks: int
#     status: str

# # API端点
# @app.get("/")
# async def root():
#     return {"message": "IntelliKnow KMS API", "status": "running"}

# @app.get("/health")
# async def health():
#     return {"status": "healthy", "kb_stats": kb.get_stats()}

# @app.post("/upload", response_model=UploadResponse)
# async def upload_document(file: UploadFile = File(...)):
#     """上传并处理文档"""
#     # 检查文件格式
#     allowed_extensions = ['.pdf', '.docx', '.txt']
#     ext = os.path.splitext(file.filename)[1].lower()
#     if ext not in allowed_extensions:
#         raise HTTPException(400, f"不支持的文件格式: {ext}")

#     # 保存文件
#     doc_id = str(uuid.uuid4())
#     safe_filename = f"{doc_id}{ext}"
#     file_path = os.path.join(Config.DOCUMENTS_DIR, safe_filename)

#     try:
#         with open(file_path, "wb") as buffer:
#             shutil.copyfileobj(file.file, buffer)

#         # 解析文档
#         text = parser.parse(file_path)

#         # 添加到知识库
#         metadata = {
#             "doc_id": doc_id,
#             "filename": file.filename,
#             "upload_time": datetime.now().isoformat(),
#             "file_type": ext
#         }
#         chunks = kb.add_document(text, metadata)

#         return UploadResponse(
#             filename=file.filename,
#             doc_id=doc_id,
#             chunks=chunks,
#             status="success"
#         )

#     except Exception as e:
#         # 清理失败的文件
#         if os.path.exists(file_path):
#             os.remove(file_path)
#         raise HTTPException(500, f"处理失败: {str(e)}")

# @app.post("/query", response_model=QueryResponse)
# async def query_knowledge(request: QueryRequest):
#     """处理查询请求"""
#     query = request.query

#     # 1. 意图分类
#     intent_result = classifier.classify(query)

#     # 2. 知识库检索
#     search_results = kb.search(query, top_k=3)

#     # 3. 构建上下文
#     context = "\n\n".join([r["text"] for r in search_results]) if search_results else "未找到相关信息。"

#     # 4. 调用Qwen生成回答
#     client = Config.get_qwen_client()
#     prompt = f"""基于以下背景知识，回答用户的问题。如果背景知识中没有相关信息，请如实说明。

# 背景知识：
# {context}

# 用户问题：{query}
# 分类意图：{intent_result['intent']}

# 请提供准确、简洁的回答："""

#     try:
#         response = client.chat.completions.create(
#             model=Config.QWEN_CHAT_MODEL,
#             messages=[
#                 {"role": "system", "content": "你是一个专业的知识库助手，基于提供的信息回答问题。"},
#                 {"role": "user", "content": prompt}
#             ],
#             temperature=0.3
#         )
#         answer = response.choices[0].message.content
#     except Exception as e:
#         answer = f"生成回答失败: {str(e)}"

#     return QueryResponse(
#         query=query,
#         intent=intent_result,
#         response=answer,
#         sources=[{
#             "text": r["text"][:200],
#             "filename": r["metadata"].get("filename", "unknown"),
#             "score": r["score"]
#         } for r in search_results]
#     )

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000)