"""
日期工具函数
"""

from datetime import datetime, timedelta
from typing import Optional


def resolve_date_range(
    start: Optional[str], end: Optional[str], default_days: int = 365
) -> tuple[str, str]:
    """
    解析并补全日期的开始/结束值

    Args:
        start: 开始日期字符串，为空时自动计算默认值
        end: 结束日期字符串，为空时自动计算默认值
        default_days: 当 start 为空时，向前推多少天

    Returns:
        (start, end) 两个格式化后的日期字符串 (YYYY-MM-DD)
    """
    if not end:
        end = datetime.today().strftime("%Y-%m-%d")
    if not start:
        start = (datetime.today() - timedelta(days=default_days)).strftime("%Y-%m-%d")
    return start, end
