"""Generic repository base — implements the Repository pattern to keep
data-access logic out of services/routes (Clean Architecture / SOLID: SRP, DIP)."""
from typing import Generic, TypeVar

from sqlalchemy import delete as sa_delete
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    def __init__(self, model: type[ModelType], db: AsyncSession):
        self.model = model
        self.db = db

    async def get(self, id_: str) -> ModelType | None:
        result = await self.db.execute(select(self.model).where(self.model.id == id_))
        return result.scalar_one_or_none()

    async def list(self, limit: int = 100, offset: int = 0) -> list[ModelType]:
        result = await self.db.execute(select(self.model).limit(limit).offset(offset))
        return list(result.scalars().all())

    async def create(self, **kwargs) -> ModelType:
        instance = self.model(**kwargs)
        self.db.add(instance)
        await self.db.commit()
        await self.db.refresh(instance)
        return instance

    async def update(self, instance: ModelType, **kwargs) -> ModelType:
        for key, value in kwargs.items():
            if value is not None:
                setattr(instance, key, value)
        await self.db.commit()
        await self.db.refresh(instance)
        return instance

    async def delete(self, id_: str) -> bool:
        result = await self.db.execute(sa_delete(self.model).where(self.model.id == id_))
        await self.db.commit()
        return result.rowcount > 0
