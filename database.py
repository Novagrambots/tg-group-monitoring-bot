from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import DateTime, Integer, String, Float, func, select
from datetime import datetime
from typing import Optional

from config import config


class Base(DeclarativeBase):
    """Базовый класс для моделей"""
    pass


class User(Base):
    """Таблица пользователей"""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_id: Mapped[int] = mapped_column(Integer, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    username: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    joined_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    left_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    duration_in_group: Mapped[Optional[float]] = mapped_column(Float, nullable=True)


class HourlyStat(Base):
    """Таблица почасовой статистики"""
    __tablename__ = "hourly_stats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    hour: Mapped[int] = mapped_column(Integer, nullable=False)
    joins_count: Mapped[int] = mapped_column(Integer, default=0)


class Database:
    """Класс для работы с базой данных"""
    def __init__(self):
        self.engine = None
        self.async_session = None

    async def init(self):
        """Инициализация базы данных"""
        self.engine = create_async_engine(config.DB_URL, echo=False)
        self.async_session = async_sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )

        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        print("База данных инициализирована")

    async def add_user(self, telegram_id: int, full_name: str, username: str = None):
        """Добавление пользователя в базу"""
        async with self.async_session() as session:
            # Проверяем, есть ли пользователь
            stmt = select(User).where(
                User.telegram_id == telegram_id,
                User.left_at.is_(None)
            )
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()

            if user:
                # Если пользователь уже есть (user == True) и не вышел - ничего не делаем
                return user

            # Добавляем нового пользователя
            user = User(
                telegram_id=telegram_id,
                full_name=full_name,
                username=username,
                joined_at=datetime.now()
            )
            session.add(user)
            await session.commit()

            # Обновляем статистику
            await self.update_hourly_stats()

            return user

    async def user_left(self, telegram_id: int):
        """Отметить выход пользователя"""
        async with self.async_session() as session:
            stmt = select(User).where(
                User.telegram_id == telegram_id,
                User.left_at.is_(None)
            )
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()

            if user:
                left_time = datetime.now()
                user.left_at = left_time
                user.duration_in_group = (left_time - user.joined_at).total_seconds()
                await session.commit()
                return user

            return None

    async def update_hourly_stats(self):
        """Обновление почасовой статистики"""
        async with self.async_session() as session:
            now = datetime.now()
            hour = now.hour
            date = now.date()

            # Находим запись за текущий час
            stmt = select(HourlyStat).where(
                func.date(HourlyStat.date) == date,
                HourlyStat.hour == hour
            )
            result = await session.execute(stmt)
            stat = result.scalar_one_or_none()

            if stat:
                stat.joins_count += 1
            else:
                stat = HourlyStat(
                    date=now,
                    hour=hour,
                    joins_count=1
                )
                session.add(stat)

            await session.commit()

    async def get_daily_stats(self, date: datetime = None):
        """Получение статистики за день"""
        if date is None:
            date = datetime.now()

        async with self.async_session() as session:
            # Общее количество вступлений за день
            joins_stmt = select(func.sum(HourlyStat.joins_count)).where(
                func.date(HourlyStat.date) == date.date()
            )
            result = await session.execute(joins_stmt)
            total_joins = result.scalar() or 0

            # Час с максимальным количеством вступлений
            max_hour_stmt = select(HourlyStat).where(
                func.date(HourlyStat.date) == date.date()
            ).order_by(HourlyStat.joins_count.desc()).limit(1)

            result = await session.execute(max_hour_stmt)
            max_hour = result.scalar_one_or_none()

            # Час с минимальным количеством вступлений
            min_hour_stmt = select(HourlyStat).where(
                func.date(HourlyStat.date) == date.date()
            ).order_by(HourlyStat.joins_count).limit(1)

            result = await session.execute(min_hour_stmt)
            min_hour = result.scalar_one_or_none()

            # Количество вышедших за день
            left_stmt = select(func.count(User.id)).where(
                func.date(User.left_at) == date.date()
            )
            result = await session.execute(left_stmt)
            left_count = result.scalar() or 0

            # Количество оставшихся в группе
            in_group_stmt = select(func.count(User.id)).where(
                User.left_at.is_(None)
            )
            result = await session.execute(in_group_stmt)
            in_group = result.scalar() or 0

            return {
                "date": date.date(),
                "total_joins": total_joins,
                "max_hour": {
                    "hour": max_hour.hour if max_hour else 0,
                    "joins": max_hour.joins_count if max_hour else 0
                },
                "min_hour": {
                    "hour": min_hour.hour if min_hour else 0,
                    "joins": min_hour.joins_count if min_hour else 0
                },
                "left_today": left_count,
                "in_group": in_group
            }


db = Database()
