import asyncio
from collections import defaultdict
from contextlib import asynccontextmanager
from typing import AsyncIterator, Dict


class UserConcurrencyManager:
    def __init__(self, max_global_workers: int = 4) -> None:
        self._locks: Dict[int, asyncio.Lock] = defaultdict(asyncio.Lock)
        self._active: Dict[int, int] = {}
        self._global_semaphore = asyncio.Semaphore(max_global_workers)

    @asynccontextmanager
    async def global_guard(self) -> AsyncIterator[None]:
        async with self._global_semaphore:
            yield

    @asynccontextmanager
    async def user_guard(self, user_id: int) -> AsyncIterator[None]:
        lock = self._locks[user_id]
        self._active[user_id] = self._active.get(user_id, 0) + 1
        try:
            async with lock:
                yield
        finally:
            self._active[user_id] = max(0, self._active.get(user_id, 1) - 1)
            if self._active.get(user_id, 0) == 0:
                self._active.pop(user_id, None)

    def active_for_user(self, user_id: int) -> bool:
        return self._active.get(user_id, 0) > 0
