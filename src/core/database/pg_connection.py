"""
PostgreSQL 连接池封装（Supabase 直连）

提供：
- PgConnectionPool: 基于 psycopg2 的线程安全连接池
- getconn() / putconn(): 获取/归还连接
- RealDictCursor: 返回 dict 而非 tuple，与 SQLite dict_factory 行为一致
"""

import os

from psycopg2.pool import ThreadedConnectionPool
from psycopg2.extras import RealDictCursor


class PgConnectionPool:
    """psycopg2 线程安全连接池

    使用 ThreadedConnectionPool，每个线程获取独立连接。
    连接用完必须 putconn() 归还，否则池会耗尽。

    连接池大小：minconn=2, maxconn=10
    - 适合 gunicorn 2 workers x 4 threads = 8 并发上限
    """

    def __init__(self, db_url: str = "", minconn: int = 2, maxconn: int = 10):
        db_url = db_url or os.environ.get("SUPABASE_DB_URL", "")
        if not db_url:
            raise ValueError("SUPABASE_DB_URL 环境变量未设置")

        # 移除 psycopg2 不识别的查询参数（如 ?pgbouncer=true）
        if "?" in db_url:
            from urllib.parse import urlparse, urlunparse
            parsed = urlparse(db_url)
            db_url = urlunparse(parsed._replace(query=""))

        self.pool = ThreadedConnectionPool(
            minconn=minconn,
            maxconn=maxconn,
            dsn=db_url,
            cursor_factory=RealDictCursor,
        )

    def getconn(self):
        """获取一个数据库连接（dict cursor）"""
        return self.pool.getconn()

    def putconn(self, conn):
        """归还数据库连接到池中"""
        self.pool.putconn(conn)

    def closeall(self):
        """关闭所有连接"""
        self.pool.closeall()
