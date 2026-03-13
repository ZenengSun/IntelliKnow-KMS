# kb/vector_store.py
import os
import uuid
import hashlib
from typing import List, Dict, Any, Optional
from datetime import datetime
import chromadb
from chromadb.config import Settings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import DashScopeEmbeddings
from config import Config

class KnowledgeBase:
    """基于 ChromaDB 的知识库（完全避免 numpy 冲突）"""
    
    def __init__(self, collection_name: str = "intelliknow"):
        self.collection_name = collection_name
        self.persist_dir = os.path.join(Config.FAISS_INDEX_PATH, "chromadb")
        
        print(f"🔧 初始化知识库: {collection_name}")
        print(f"   持久化路径: {self.persist_dir}")
        
        # 初始化 ChromaDB 客户端
        self.client = chromadb.PersistentClient(
            path=self.persist_dir,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # 初始化 Embedding
        self.embeddings = DashScopeEmbeddings(
            model=Config.QWEN_EMBEDDING_MODEL,
            dashscope_api_key=Config.QWEN_API_KEY
        )
        
        # 测试 Embedding
        try:
            print("   测试Embedding连接...")
            test_embedding = self.embeddings.embed_query("测试")
            print(f"   ✅ Embedding测试成功，维度: {len(test_embedding)}")
        except Exception as e:
            print(f"   ❌ Embedding测试失败: {e}")
            raise
        
        # 文本分割器
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            separators=["\n\n", "\n", "。", "！", "？", "；", "，", " ", ""]
        )
        
        # 获取或创建集合
        try:
            self.collection = self.client.get_collection(collection_name)
            print(f"✅ 加载现有集合: {collection_name}")
        except:
            self.collection = self.client.create_collection(collection_name)
            print(f"✅ 创建新集合: {collection_name}")
        
        self.doc_metadata = {}
    
    def add_document(self, text: str, filename: str, intent: str = "General") -> Dict:
        """添加文档到知识库"""
        doc_id = hashlib.md5(f"{filename}_{datetime.now()}".encode()).hexdigest()[:8]
        print(f"\n📥 添加文档: {filename}")
        print(f"   文档ID: {doc_id}")
        print(f"   意图: {intent}")
        
        # 文本分块
        chunks = self.text_splitter.split_text(text)
        print(f"   分块数量: {len(chunks)}")
        
        # 为每个块生成 embedding 并添加到 chromadb
        for i, chunk in enumerate(chunks):
            chunk_id = f"{doc_id}_{i}"
            metadata = {
                "doc_id": doc_id,
                "filename": filename,
                "intent": intent,
                "chunk_index": i,
                "total_chunks": len(chunks),
                "upload_time": datetime.now().isoformat()
            }
            
            # 获取 embedding
            embedding = self.embeddings.embed_query(chunk)
            
            # 添加到 chromadb
            self.collection.add(
                ids=[chunk_id],
                embeddings=[embedding],
                documents=[chunk],
                metadatas=[metadata]
            )
        
        # 保存文档元数据
        self.doc_metadata[doc_id] = {
            "doc_id": doc_id,
            "filename": filename,
            "intent": intent,
            "chunks": len(chunks),
            "upload_time": datetime.now().isoformat()
        }
        
        print(f"   ✅ 添加完成")
        return {
            "doc_id": doc_id,
            "chunks": len(chunks),
            "intent": intent,
            "status": "success"
        }
    
    def search(self, query: str, k: int = 3, intent_filter: Optional[str] = None) -> List[Dict]:
        """语义搜索"""
        print(f"\n🔍 搜索: '{query}'")
        
        # 获取查询的 embedding
        query_embedding = self.embeddings.embed_query(query)
        
        # 构建查询条件
        where = {"intent": intent_filter} if intent_filter else None
        
        # 执行搜索
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=k * 2,
            where=where
        )
        
        # 整理结果
        search_results = []
        if results['ids']:
            for i in range(len(results['ids'][0])):
                search_results.append({
                    "text": results['documents'][0][i][:200] + "...",
                    "metadata": results['metadatas'][0][i],
                    "score": 1 - results['distances'][0][i] / 2,  # 归一化分数
                    "filename": results['metadatas'][0][i].get('filename', 'unknown')
                })
        
        print(f"   找到 {len(search_results)} 个结果")
        return search_results[:k]
    
    def get_stats(self) -> Dict:
        """获取知识库统计"""
        count = self.collection.count()
        
        # 获取所有文档的元数据（需要遍历）
        # 这里简化处理
        return {
            "total_documents": len(self.doc_metadata),
            "total_chunks": count,
            "intent_distribution": {}  # 可以从 chromadb 查询
        }