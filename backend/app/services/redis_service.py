import json
from typing import Optional, Dict, Any, List
from loguru import logger
from app.config import get_settings

settings = get_settings()


class RedisService:
    """Redis-backed storage for batch jobs, candidate data, and caching."""

    def __init__(self):
        self._redis = None
        self._initialized = False
        self._fallback = {}  # In-memory fallback if Redis unavailable

    async def _ensure_connected(self):
        if self._initialized:
            return
        self._initialized = True
        try:
            import redis.asyncio as aioredis
            self._redis = aioredis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
            )
            await self._redis.ping()
            logger.info(f"Redis connected: {settings.REDIS_URL}")
        except Exception as e:
            logger.warning(f"Redis not available ({e}). Using in-memory fallback.")
            self._redis = None

    # ─── Generic key-value ───

    async def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Store a JSON-serializable value."""
        await self._ensure_connected()
        payload = json.dumps(value, default=str)
        if self._redis:
            try:
                await self._redis.set(key, payload, ex=ttl)
                return
            except Exception as e:
                logger.error(f"Redis SET failed: {e}")
        self._fallback[key] = payload

    async def get(self, key: str) -> Optional[Any]:
        """Retrieve a value by key."""
        await self._ensure_connected()
        if self._redis:
            try:
                val = await self._redis.get(key)
                return json.loads(val) if val else None
            except Exception as e:
                logger.error(f"Redis GET failed: {e}")
        raw = self._fallback.get(key)
        return json.loads(raw) if raw else None

    async def delete(self, key: str):
        """Delete a key."""
        await self._ensure_connected()
        if self._redis:
            try:
                await self._redis.delete(key)
                return
            except Exception as e:
                logger.error(f"Redis DELETE failed: {e}")
        self._fallback.pop(key, None)

    async def keys(self, pattern: str) -> List[str]:
        """List keys matching a pattern."""
        await self._ensure_connected()
        if self._redis:
            try:
                return await self._redis.keys(pattern)
            except Exception as e:
                logger.error(f"Redis KEYS failed: {e}")
        import fnmatch
        return [k for k in self._fallback if fnmatch.fnmatch(k, pattern)]

    # ─── Candidate store ───

    async def store_candidate(self, candidate_id: str, data: Dict):
        """Store parsed candidate data."""
        await self.set(f"candidate:{candidate_id}", data, ttl=86400)  # 24h TTL

    async def get_candidate(self, candidate_id: str) -> Optional[Dict]:
        """Retrieve candidate data."""
        return await self.get(f"candidate:{candidate_id}")

    async def list_candidates(self) -> List[Dict]:
        """List all stored candidates."""
        candidate_keys = await self.keys("candidate:*")
        candidates = []
        for key in candidate_keys:
            data = await self.get(key)
            if data:
                cid = key.replace("candidate:", "")
                candidates.append({"candidate_id": cid, **data})
        return candidates

    # ─── Batch job store ───

    async def store_batch_job(self, batch_id: str, data: Dict):
        """Store batch job state."""
        await self.set(f"batch:{batch_id}", data, ttl=172800)  # 48h TTL

    async def get_batch_job(self, batch_id: str) -> Optional[Dict]:
        """Retrieve batch job state."""
        return await self.get(f"batch:{batch_id}")

    async def update_batch_job(self, batch_id: str, updates: Dict):
        """Update specific fields of a batch job."""
        existing = await self.get_batch_job(batch_id)
        if existing:
            existing.update(updates)
            await self.store_batch_job(batch_id, existing)

    # ─── Job description store ───

    async def store_job(self, job_id: str, data: Dict):
        """Store a job description."""
        await self.set(f"job:{job_id}", data, ttl=86400)

    async def get_job(self, job_id: str) -> Optional[Dict]:
        """Retrieve a job description."""
        return await self.get(f"job:{job_id}")

    async def list_jobs(self) -> List[Dict]:
        """List all stored jobs."""
        job_keys = await self.keys("job:*")
        jobs = []
        for key in job_keys:
            data = await self.get(key)
            if data:
                jid = key.replace("job:", "")
                jobs.append({"job_id": jid, **data})
        return jobs

    # ─── Cache helpers ───

    async def cache_skill_embedding(self, skill: str, embedding: list, ttl: int = 3600):
        """Cache a skill embedding."""
        await self.set(f"embedding:{skill.lower()}", embedding, ttl=ttl)

    async def get_cached_embedding(self, skill: str) -> Optional[list]:
        """Get cached skill embedding."""
        return await self.get(f"embedding:{skill.lower()}")

    async def close(self):
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()


# Singleton
_redis_service = None


def get_redis_service() -> RedisService:
    global _redis_service
    if _redis_service is None:
        _redis_service = RedisService()
    return _redis_service
