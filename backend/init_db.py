import asyncio

import app.models  # noqa: F401
from app.db.base import Base
from app.db.session import async_engine


async def init_db() -> None:
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Tables créées avec succès !")


if __name__ == "__main__":
    asyncio.run(init_db())
