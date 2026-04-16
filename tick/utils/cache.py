"""
数据缓存系统 - SQLite 缓存
"""

import hashlib
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import pandas as pd

from tick.core.config import get_config


class DataCache:
    """数据缓存管理器"""

    def __init__(self, cache_dir: Optional[Path] = None):
        config = get_config()
        self.cache_dir = cache_dir or config.get_cache_dir()
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.cache_dir / "tick_cache.db"
        self.ttl = config.cache.ttl
        self._init_db()

    def _init_db(self):
        """初始化数据库"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cache (
                    key TEXT PRIMARY KEY,
                    symbol TEXT NOT NULL,
                    start TEXT,
                    end TEXT,
                    interval TEXT,
                    data BLOB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_symbol ON cache(symbol)
            """)

    def _make_key(
        self, symbol: str, start: str, end: str, interval: str, source: str = ""
    ) -> str:
        """生成缓存键"""
        key_str = f"{symbol}:{source}:{start}:{end}:{interval}"
        return hashlib.md5(key_str.encode()).hexdigest()

    def get(
        self, symbol: str, start: str, end: str, interval: str, source: str = ""
    ) -> Optional[pd.DataFrame]:
        """获取缓存数据"""
        key = self._make_key(symbol, start, end, interval, source)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT data, expires_at FROM cache WHERE key = ?", (key,)
            )
            row = cursor.fetchone()

            if row is None:
                return None

            data_blob, expires_at = row

            # 检查是否过期
            if expires_at:
                expires = datetime.fromisoformat(expires_at)
                if datetime.now() > expires:
                    # 删除过期数据
                    conn.execute("DELETE FROM cache WHERE key = ?", (key,))
                    return None

            # 反序列化
            try:
                import pickle

                df = pickle.loads(data_blob)
                return df
            except Exception:
                return None

    def set(
        self,
        symbol: str,
        start: str,
        end: str,
        interval: str,
        df: pd.DataFrame,
        ttl: Optional[int] = None,
        source: str = "",
    ):
        """设置缓存数据"""
        key = self._make_key(symbol, start, end, interval, source)
        ttl = ttl or self.ttl
        expires_at = datetime.now() + timedelta(seconds=ttl)

        try:
            import pickle

            data_blob = pickle.dumps(df)

            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO cache
                    (key, symbol, start, end, interval, data, expires_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        key,
                        symbol,
                        start,
                        end,
                        interval,
                        data_blob,
                        expires_at.isoformat(),
                    ),
                )
        except Exception:
            pass  # 缓存失败不阻止主流程

    def clear(self, symbol: Optional[str] = None):
        """清理缓存"""
        with sqlite3.connect(self.db_path) as conn:
            if symbol:
                conn.execute("DELETE FROM cache WHERE symbol = ?", (symbol,))
            else:
                conn.execute("DELETE FROM cache")

    def cleanup_expired(self):
        """清理过期数据"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "DELETE FROM cache WHERE expires_at < ?", (datetime.now().isoformat(),)
            )


# 全局缓存实例
_cache: Optional[DataCache] = None


def get_cache() -> DataCache:
    """获取全局缓存实例"""
    global _cache
    if _cache is None:
        _cache = DataCache()
    return _cache
