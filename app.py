# app.py
import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="IntelliKnow KMS", page_icon="🧠", layout="wide")

# API地址
API_BASE = "http://localhost:8000"

# 初始化session state
if 'upload_status' not in st.session_state:
    st.session_state.upload_status = None

# 侧边栏导航
st.sidebar.title("🧠 IntelliKnow KMS")
st.sidebar.markdown("---")
page = st.sidebar.radio(
    "导航",
    ["仪表盘", "知识库管理", "意图配置", "分析"],
    index=0
)
st.sidebar.markdown("---")
st.sidebar.caption("v1.0.0")

# 检查API连接
try:
    health = requests.get(f"{API_BASE}/health", timeout=2)
    api_ok = health.status_code == 200
    if api_ok:
        data = health.json()
        kb_stats = data.get("kb_stats", {})
        query_stats = data.get("db_stats", {})
except:
    api_ok = False
    kb_stats = {}
    query_stats = {}

if not api_ok:
    st.sidebar.error("⚠️ API服务未连接")
else:
    st.sidebar.success("✅ API已连接")

# ---------- 仪表盘 ----------
if page == "仪表盘":
    st.title("🏠 仪表盘")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("文档总数", kb_stats.get("total_documents", 0))
    with col2:
        st.metric("知识块数量", kb_stats.get("total_chunks", 0))
    with col3:
        st.metric("总查询次数", query_stats.get("total_queries", 0))
    with col4:
        st.metric("平均置信度", f"{query_stats.get('avg_confidence', 0)*100:.1f}%")

    st.markdown("---")
    st.subheader("快速查询测试")

    col1, col2 = st.columns([3, 1])
    with col1:
        test_query = st.text_input("输入测试问题", placeholder="例如：年假有多少天？")
    with col2:
        if st.button("发送查询", type="primary"):
            if test_query:
                with st.spinner("处理中..."):
                    response = requests.post(
                        f"{API_BASE}/query",
                        json={"query": test_query, "platform": "streamlit"}
                    )
                    if response.status_code == 200:
                        result = response.json()
                        st.success(f"意图: {result['intent']['intent']} (置信度: {result['intent']['confidence']:.2f})")
                        st.info(f"回答: {result['response']}")
                        with st.expander("查看来源"):
                            for src in result['sources']:
                                st.caption(f"📄 {src['filename']} (相似度: {src['score']:.2f})")
                                st.text(src['text'][:200] + "...")
                    else:
                        st.error(f"查询失败: {response.text}")

# ---------- 知识库管理 ----------
elif page == "知识库管理":
    st.title("📚 知识库管理")

    # 上传区域
    with st.expander("📤 上传新文档", expanded=True):
        col1, col2 = st.columns([3, 1])
        with col1:
            uploaded_file = st.file_uploader(
                "选择文件 (支持 PDF, DOCX, TXT)",
                type=['pdf', 'docx', 'txt']
            )
        with col2:
            if uploaded_file and st.button("上传并处理", type="primary"):
                files = {"file": (uploaded_file.name, uploaded_file.getvalue())}
                with st.spinner("处理中..."):
                    response = requests.post(f"{API_BASE}/upload", files=files)
                    if response.status_code == 200:
                        result = response.json()
                        st.session_state.upload_status = f"✅ 成功: {result['filename']} (分块: {result['chunks']}, 意图: {result['intent']})"
                        st.rerun()
                    else:
                        st.session_state.upload_status = f"❌ 失败: {response.text}"

        if st.session_state.upload_status:
            st.info(st.session_state.upload_status)

    # 文档列表
    st.subheader("文档列表")
    try:
        docs_response = requests.get(f"{API_BASE}/documents")
        if docs_response.status_code == 200:
            docs = docs_response.json()
            if docs:
                df = pd.DataFrame(docs)
                st.dataframe(df, use_container_width=True)
            else:
                st.info("暂无文档，请上传")
    except:
        st.error("无法获取文档列表")

# ---------- 意图配置 ----------
elif page == "意图配置":
    st.title("🎯 意图空间配置")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("意图列表")
        intents = ["HR", "Legal", "Finance", "General"]

        for intent in intents:
            with st.container(border=True):
                cols = st.columns([2, 1, 1])
                with cols[0]:
                    st.markdown(f"**{intent}**")
                with cols[1]:
                    st.caption(f"阈值: 70%")
                with cols[2]:
                    if intent != "General":
                        st.button("编辑", key=f"edit_{intent}")

    with col2:
        st.subheader("最近分类日志")
        # 这里可以从API获取真实日志，现在用示例数据
        log_data = [
            {"时间": "14:32", "查询": "年假有多少天？", "意图": "HR", "置信度": 0.92},
            {"时间": "14:15", "查询": "报销流程", "意图": "Finance", "置信度": 0.88},
            {"时间": "13:50", "查询": "合同有效期", "意图": "Legal", "置信度": 0.76},
            {"时间": "13:22", "查询": "今天天气", "意图": "General", "置信度": 0.51},
        ]
        log_df = pd.DataFrame(log_data)
        st.dataframe(log_df, use_container_width=True)

# ---------- 分析 ----------
elif page == "分析":
    st.title("📊 分析")

    # 意图分布
    st.subheader("意图分布")
    intent_dist = query_stats.get("intent_distribution", {})
    if intent_dist:
        intent_df = pd.DataFrame([
            {"意图": k, "查询数": v} for k, v in intent_dist.items()
        ])
        fig = px.bar(intent_df, x="意图", y="查询数", color="意图")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("暂无查询数据")

    # 知识库统计
    st.subheader("知识库统计")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("文档总数", kb_stats.get("total_documents", 0))
    with col2:
        st.metric("知识块数量", kb_stats.get("total_chunks", 0))
    with col3:
        st.metric("总查询", query_stats.get("total_queries", 0))



# # app.py
# import streamlit as st
# import requests
# import pandas as pd
# import plotly.express as px
# from datetime import datetime
# import time

# # 页面配置
# st.set_page_config(
#     page_title="IntelliKnow KMS",
#     page_icon="🧠",
#     layout="wide"
# )

# # API地址
# API_BASE = "http://localhost:8000"

# # 初始化session state
# if 'upload_status' not in st.session_state:
#     st.session_state.upload_status = None

# # 侧边栏导航
# st.sidebar.title("🧠 IntelliKnow KMS")
# st.sidebar.markdown("---")
# page = st.sidebar.radio(
#     "导航",
#     ["仪表盘", "知识库管理", "意图配置", "前端集成", "分析"],
#     index=0
# )
# st.sidebar.markdown("---")
# st.sidebar.caption("v1.0.0 | Tech Lead Interview Project")

# # 检查API连接
# try:
#     health = requests.get(f"{API_BASE}/health", timeout=2)
#     api_ok = health.status_code == 200
#     kb_stats = health.json().get("kb_stats", {}) if api_ok else {}
# except:
#     api_ok = False
#     kb_stats = {}

# if not api_ok:
#     st.sidebar.error("⚠️ API服务未连接")
# else:
#     st.sidebar.success("✅ API已连接")

# # ---------- 页面内容 ----------
# if page == "仪表盘":
#     st.title("🏠 仪表盘")

#     col1, col2, col3, col4 = st.columns(4)
#     with col1:
#         st.metric("文档总数", kb_stats.get("total_documents", 0))
#     with col2:
#         st.metric("知识块数量", kb_stats.get("total_chunks", 0))
#     with col3:
#         st.metric("API状态", "正常" if api_ok else "异常")
#     with col4:
#         st.metric("当前时间", datetime.now().strftime("%H:%M"))

#     st.markdown("---")
#     st.subheader("快速查询测试")

#     col1, col2 = st.columns([3, 1])
#     with col1:
#         test_query = st.text_input("输入测试问题", placeholder="例如：年假有多少天？")
#     with col2:
#         if st.button("发送查询", type="primary"):
#             if test_query:
#                 with st.spinner("处理中..."):
#                     response = requests.post(
#                         f"{API_BASE}/query",
#                         json={"query": test_query}
#                     )
#                     if response.status_code == 200:
#                         result = response.json()
#                         st.success(f"意图: {result['intent']['intent']} (置信度: {result['intent']['confidence']:.2f})")
#                         st.info(f"回答: {result['response']}")
#                         with st.expander("查看来源"):
#                             for src in result['sources']:
#                                 st.caption(f"📄 {src['filename']} (相似度: {src['score']:.2f})")
#                                 st.text(src['text'])
#                     else:
#                         st.error(f"查询失败: {response.text}")

# elif page == "知识库管理":
#     st.title("📚 知识库管理")

#     # 上传区域
#     with st.expander("📤 上传新文档", expanded=True):
#         col1, col2 = st.columns([3, 1])
#         with col1:
#             uploaded_file = st.file_uploader(
#                 "选择文件 (支持 PDF, DOCX, TXT)",
#                 type=['pdf', 'docx', 'txt']
#             )
#         with col2:
#             if uploaded_file and st.button("上传并处理", type="primary"):
#                 files = {"file": (uploaded_file.name, uploaded_file.getvalue())}
#                 with st.spinner("处理中..."):
#                     response = requests.post(f"{API_BASE}/upload", files=files)
#                     if response.status_code == 200:
#                         result = response.json()
#                         st.session_state.upload_status = f"✅ 成功: {result['filename']} (分块: {result['chunks']})"
#                         st.rerun()
#                     else:
#                         st.session_state.upload_status = f"❌ 失败: {response.text}"

#         if st.session_state.upload_status:
#             st.info(st.session_state.upload_status)

#     # 文档列表（模拟数据）
#     st.subheader("文档列表")
#     docs_data = [
#         {"文件名": "员工手册.pdf", "上传时间": "2024-01-15", "格式": "PDF", "状态": "已处理", "意图": "HR"},
#         {"文件名": "财务报销制度.docx", "上传时间": "2024-01-14", "格式": "DOCX", "状态": "已处理", "意图": "Finance"},
#         {"文件名": "合同模板.pdf", "上传时间": "2024-01-13", "格式": "PDF", "状态": "已处理", "意图": "Legal"},
#         {"文件名": "公司介绍.txt", "上传时间": "2024-01-12", "格式": "TXT", "状态": "已处理", "意图": "General"},
#     ]
#     df = pd.DataFrame(docs_data)
#     st.dataframe(df, use_container_width=True)

#     # 搜索过滤
#     st.subheader("🔍 搜索")
#     col1, col2 = st.columns(2)
#     with col1:
#         search_term = st.text_input("关键词搜索")
#     with col2:
#         filter_intent = st.selectbox("意图过滤", ["全部", "HR", "Legal", "Finance", "General"])

# elif page == "意图配置":
#     st.title("🎯 意图空间配置")

#     col1, col2 = st.columns([1, 1])

#     with col1:
#         st.subheader("意图列表")
#         intents = ["HR", "Legal", "Finance", "General"]

#         for intent in intents:
#             with st.container(border=True):
#                 cols = st.columns([2, 1, 1])
#                 with cols[0]:
#                     st.markdown(f"**{intent}**")
#                 with cols[1]:
#                     st.caption(f"文档: {3 if intent!='General' else 1}")
#                 with cols[2]:
#                     if intent != "General":
#                         st.button("编辑", key=f"edit_{intent}")

#         st.button("➕ 新建意图空间")

#     with col2:
#         st.subheader("最近分类日志")
#         log_data = [
#             {"时间": "14:32", "查询": "年假有多少天？", "意图": "HR", "置信度": 0.92},
#             {"时间": "14:15", "查询": "报销流程", "意图": "Finance", "置信度": 0.88},
#             {"时间": "13:50", "查询": "合同有效期", "意图": "Legal", "置信度": 0.76},
#             {"时间": "13:22", "查询": "今天天气", "意图": "General", "置信度": 0.51},
#         ]
#         log_df = pd.DataFrame(log_data)
#         st.dataframe(log_df, use_container_width=True)

# elif page == "前端集成":
#     st.title("🔌 前端集成")

#     col1, col2 = st.columns(2)

#     with col1:
#         with st.container(border=True):
#             st.subheader("🤖 Telegram Bot")
#             st.markdown("状态: 🟢 **已连接**")
#             token = st.text_input("Bot Token", value="1234567890:ABCdefGHIjklMNOpqrsTUVwxyz", type="password")
#             st.caption("Token格式: 数字:字母组合")
#             if st.button("测试连接", key="test_tg"):
#                 st.success("✅ 测试成功! Bot正常运行")

#     with col2:
#         with st.container(border=True):
#             st.subheader("💬 Microsoft Teams")
#             st.markdown("状态: 🔴 **未连接**")
#             app_id = st.text_input("App ID", value="")
#             app_pass = st.text_input("App Password", type="password")
#             if st.button("配置", key="config_teams"):
#                 st.info("Teams集成配置已保存")

#     st.markdown("---")
#     st.subheader("集成指南")
#     with st.expander("如何创建Telegram Bot?"):
#         st.markdown("""
#         1. 在Telegram中搜索 **@BotFather**
#         2. 发送 `/newbot` 命令
#         3. 设置bot名称和用户名
#         4. 复制得到的API Token
#         5. 在左侧输入框中粘贴Token
#         """)

# elif page == "分析":
#     st.title("📊 分析")

#     col1, col2, col3 = st.columns(3)
#     with col1:
#         st.metric("总查询次数", "1,234", "+12.3%")
#     with col2:
#         st.metric("平均置信度", "87.5%", "+2.1%")
#     with col3:
#         st.metric("分类准确率", "94.2%", "+0.8%")

#     st.subheader("意图分布")
#     intent_data = pd.DataFrame({
#         "意图": ["HR", "Legal", "Finance", "General"],
#         "查询数": [450, 320, 280, 184]
#     })
#     fig = px.bar(intent_data, x="意图", y="查询数", color="意图")
#     st.plotly_chart(fig, use_container_width=True)

#     st.subheader("近7天查询趋势")
#     trend_data = pd.DataFrame({
#         "日期": ["01/15", "01/16", "01/17", "01/18", "01/19", "01/20", "01/21"],
#         "查询量": [65, 72, 78, 85, 92, 88, 95]
#     })
#     fig2 = px.line(trend_data, x="日期", y="查询量")
#     st.plotly_chart(fig2, use_container_width=True)