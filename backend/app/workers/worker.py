"""Arq worker runner."""

from __future__ import annotations

import asyncio
from arq import cron
from arq.connections import RedisSettings

from app.core.config import get_settings
from app.workers.tasks import recompute_ratings_task

settings = get_settings()


class WorkerSettings:
    functions = [recompute_ratings_task]
    cron_jobs = [
        cron(
            recompute_ratings_task,
            minute={f"*/{settings.rating_recompute_interval_minutes}"},
        )
    ]
    redis_settings = RedisSettings.from_dsn(settings.redis_url)


async def main():
    """Alternative standalone runner if arq CLI is not used."""
    from arq.worker import run_worker
    await run_worker(WorkerSettings)


if __name__ == "__main__":
    asyncio.run(main())

