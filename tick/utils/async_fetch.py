"""
异步并发下载工具
"""
import asyncio
from typing import List, Callable, TypeVar, Any
from concurrent.futures import ThreadPoolExecutor
from tick.core.models import FetchConfig, FetchResult

T = TypeVar('T')


class AsyncFetcher:
    """异步下载器"""
    
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
    
    async def fetch_one(self, fetch_func: Callable[[FetchConfig], FetchResult], config: FetchConfig) -> FetchResult:
        """异步获取单个品种"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, fetch_func, config)
    
    async def fetch_many(
        self,
        fetch_func: Callable[[FetchConfig], FetchResult],
        configs: List[FetchConfig]
    ) -> List[FetchResult]:
        """并发获取多个品种"""
        tasks = [self.fetch_one(fetch_func, config) for config in configs]
        return await asyncio.gather(*tasks, return_exceptions=True)
    
    def fetch_sync(
        self,
        fetch_func: Callable[[FetchConfig], FetchResult],
        configs: List[FetchConfig]
    ) -> List[FetchResult]:
        """同步接口（用于 CLI）"""
        return asyncio.run(self.fetch_many(fetch_func, configs))
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.executor.shutdown(wait=True)


async def fetch_with_progress(
    configs: List[FetchConfig],
    fetch_func: Callable[[FetchConfig], FetchResult],
    max_workers: int = 4,
    progress_callback: Callable[[int, int], None] = None
) -> List[FetchResult]:
    """
    带进度回调的并发下载
    
    Args:
        configs: 配置列表
        fetch_func: 获取函数
        max_workers: 最大并发数
        progress_callback: 进度回调 (current, total)
    """
    results = []
    total = len(configs)
    
    semaphore = asyncio.Semaphore(max_workers)
    
    async def fetch_with_limit(config: FetchConfig) -> FetchResult:
        async with semaphore:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, fetch_func, config)
            return result
    
    # 创建任务
    tasks = [fetch_with_limit(config) for config in configs]
    
    # 逐个完成并报告进度
    for i, task in enumerate(asyncio.as_completed(tasks)):
        result = await task
        results.append(result)
        if progress_callback:
            progress_callback(i + 1, total)
    
    return results
