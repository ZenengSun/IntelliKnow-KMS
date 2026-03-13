# utils/database.py
import sqlite3
import json
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any, Optional
from config import Config

class Database:
    """SQLite数据库管理（查询日志、意图配置、文档元数据）"""

    def __init__(self):
        self.db_path = Config.SQLITE_PATH
        self._init_tables()

    def _init_tables(self):
        """初始化数据库表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 查询日志表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS query_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT NOT NULL,
                intent TEXT,
                confidence REAL,
                response TEXT,
                source_docs TEXT,
                platform TEXT,
                response_time REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # 意图配置表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS intent_config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                description TEXT,
                keywords TEXT,
                confidence_threshold REAL DEFAULT 0.7,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # 文档元数据表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                doc_id TEXT UNIQUE NOT NULL,
                filename TEXT NOT NULL,
                title TEXT,
                intent TEXT,
                chunk_count INTEGER,
                file_size INTEGER,
                upload_time TIMESTAMP,
                metadata TEXT
            )
        ''')

        # 初始化默认意图
        default_intents = [
            ("HR", "人力资源相关问题", "请假,考勤,薪酬,培训,招聘,绩效,员工,年假,病假,产假,加班"),
            ("Legal", "法律相关问题", "合同,保密,协议,法律,合规,条款,违约,起诉,仲裁,知识产权"),
            ("Finance", "财务相关问题", "报销,发票,采购,预算,财务,差旅,住宿,补贴,付款,费用"),
            ("General", "其他通用问题", "你好,帮助,介绍,关于")
        ]

        for name, desc, keywords in default_intents:
            try:
                cursor.execute('''
                    INSERT OR IGNORE INTO intent_config (name, description, keywords)
                    VALUES (?, ?, ?)
                ''', (name, desc, keywords))
            except:
                pass

        conn.commit()
        conn.close()
        print("✅ 数据库初始化完成")

    # ---------- 查询日志 ----------
    def log_query(self, query: str, intent: str, confidence: float,
                  response: str, source_docs: List, platform: str, response_time: float):
        """记录查询"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO query_logs (query, intent, confidence, response, source_docs, platform, response_time)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (query, intent, confidence, response, json.dumps(source_docs, ensure_ascii=False),
              platform, response_time))
        conn.commit()
        conn.close()

    def get_query_logs(self, limit: int = 100) -> pd.DataFrame:
        """获取查询日志"""
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query(f'''
            SELECT id, query, intent, confidence, platform,
                   datetime(created_at) as created_at
            FROM query_logs
            ORDER BY created_at DESC
            LIMIT {limit}
        ''', conn)
        conn.close()
        return df

    def get_query_stats(self) -> Dict:
        """获取查询统计"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM query_logs")
        total = cursor.fetchone()[0] or 0

        cursor.execute("SELECT AVG(confidence) FROM query_logs WHERE confidence IS NOT NULL")
        avg_confidence = cursor.fetchone()[0] or 0

        cursor.execute('''
            SELECT intent, COUNT(*) as count
            FROM query_logs
            WHERE intent IS NOT NULL
            GROUP BY intent
            ORDER BY count DESC
        ''')
        intent_dist = dict(cursor.fetchall())

        conn.close()
        return {
            "total_queries": total,
            "avg_confidence": round(avg_confidence, 2),
            "intent_distribution": intent_dist
        }

    # ---------- 文档管理 ----------
    def add_document_meta(self, doc_id: str, filename: str, title: str,
                          intent: str, chunk_count: int, file_size: int, metadata: Dict):
        """添加文档元数据"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO documents
            (doc_id, filename, title, intent, chunk_count, file_size, upload_time, metadata)
            VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?)
        ''', (doc_id, filename, title, intent, chunk_count, file_size, json.dumps(metadata)))
        conn.commit()
        conn.close()

    def get_documents(self) -> List[Dict]:
        """获取文档列表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT doc_id, filename, title, intent, chunk_count,
                   file_size, datetime(upload_time) as upload_time
            FROM documents
            ORDER BY upload_time DESC
        ''')
        rows = cursor.fetchall()
        conn.close()
        
        documents = []
        for row in rows:
            documents.append({
                "doc_id": row[0],
                "filename": row[1],
                "title": row[2],
                "intent": row[3],
                "chunk_count": row[4],
                "file_size": row[5],
                "upload_time": row[6]
            })
        return documents