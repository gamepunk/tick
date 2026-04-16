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
        self._conn: Optional[sqlite3.Connection] = None
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        """获取数据库连接（懒加载）"""
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path)
        return self._conn

    def _init_db(self):
        """初始化数据库"""
        conn = self._get_conn()
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
        conn.commit()

    def close(self):
        """显式关闭数据库连接"""
        if self._conn is not None:
            try:
                self._conn.close()
            except Exception:
                pass
            self._conn = None

    def __del__(self):
        """析构时关闭连接"""
        self.close()

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

        conn = self._get_conn()
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
                conn.commit()
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

            conn = self._get_conn()
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
            conn.commit()
        except Exception:
            # 缓存失败不阻止主流程
            pass

    def clear(self, symbol: Optional[str] = None):
        """清理缓存"""
        conn = self._get_conn()
        if symbol:
            conn.execute("DELETE FROM cache WHERE symbol = ?", (symbol,))
        else:
            conn.execute("DELETE FROM cache")
        conn.commit()

    def cleanup_expired(self):
        """清理过期数据"""
        conn = self._get_conn()
        conn.execute(
            "DELETE FROM cache WHERE expires_at < ?", (datetime.now().isoformat(),)
        )
        conn.commit()

    def list_entries(self, symbol: Optional[str] = None) -> list[dict[str, str | int | float | None]]:
        """列出缓存条目（不加载数据内容）"""
        conn = self._get_conn()
        sql = """
            SELECT symbol, start, end, interval, created_at, expires_at, LENGTH(data) as size
            FROM cache
        """
        params: tuple = ()
        if symbol:
            sql += " WHERE symbol = ?"
            params = (symbol,)
        sql += " ORDER BY symbol, created_at DESC"

        cursor = conn.execute(sql, params)
        rows = cursor.fetchall()

        results: list[dict[str, str | int | float | None]] = []
        for row in rows:
            symbol_val, start, end, interval, created_at, expires_at, size = row
            size_kb = round(size / 1024, 2) if size else 0.0
            results.append({
                "symbol": symbol_val,
                "start": start,
                "end": end,
                "interval": interval,
                "created_at": created_at,
                "expires_at": expires_at,
                "size_kb": size_kb,
            })
        return results

    def get_stats(self) -> dict[str, int | float]:
        """获取缓存统计信息"""
        conn = self._get_conn()
        cursor = conn.execute(
            "SELECT COUNT(*), COALESCE(SUM(LENGTH(data)), 0) FROM cache"
        )
        count, total_size = cursor.fetchone()
        return {
            "entries": count,
            "total_size_kb": round(total_size / 1024, 2),
        }


# 全局缓存实例
_cache: Optional[DataCache] = None


def get_cache() -> DataCache:
    """获取全局缓存实例"""
    global _cache
    if _cache is None:
        _cache = DataCache()
    return _cache
