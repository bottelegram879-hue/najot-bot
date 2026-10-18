"""Database schema and session factory.

Tables: users, clients, masters, owners, cars, services, requests, request_history,
notifications, settings, invites. Works on SQLite (dev) and PostgreSQL (prod) via DATABASE_URL.
"""
from datetime import datetime

from sqlalchemy import (BigInteger, Boolean, DateTime, Float, ForeignKey, Integer, String, Text,
                        UniqueConstraint, inspect, select, text)
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from .config import DEFAULT_SETTINGS, SERVICES, config, now


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tg_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    username: Mapped[str | None] = mapped_column(String(64))
    full_name: Mapped[str] = mapped_column(String(128), default="")
    phone: Mapped[str | None] = mapped_column(String(32))
    lang: Mapped[str | None] = mapped_column(String(2))
    role: Mapped[str] = mapped_column(String(10), default="client", index=True)  # client|master|owner|blocked
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    last_seen: Mapped[datetime] = mapped_column(DateTime, default=now)


class Client(Base):
    __tablename__ = "clients"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), unique=True)
    name: Mapped[str] = mapped_column(String(128))
    phone: Mapped[str] = mapped_column(String(32), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class Master(Base):
    __tablename__ = "masters"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    name: Mapped[str] = mapped_column(String(128))
    specialization: Mapped[str] = mapped_column(String(128), default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    user: Mapped[User] = relationship(lazy="joined")


class Owner(Base):
    __tablename__ = "owners"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class Car(Base):
    __tablename__ = "cars"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    brand: Mapped[str] = mapped_column(String(64))
    model: Mapped[str] = mapped_column(String(64))
    year: Mapped[int | None] = mapped_column(Integer)
    body_type: Mapped[str | None] = mapped_column(String(16))
    plate: Mapped[str | None] = mapped_column(String(20))
    vin: Mapped[str | None] = mapped_column(String(32))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class Service(Base):
    __tablename__ = "services"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(32), unique=True)
    emoji: Mapped[str] = mapped_column(String(8))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    sort: Mapped[int] = mapped_column(Integer, default=0)


class Request(Base):
    __tablename__ = "requests"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    number: Mapped[str | None] = mapped_column(String(16), unique=True, index=True)
    idempotency_key: Mapped[str] = mapped_column(String(64), unique=True)
    client_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)
    client_id: Mapped[int | None] = mapped_column(ForeignKey("clients.id", ondelete="SET NULL"))
    car_id: Mapped[int | None] = mapped_column(ForeignKey("cars.id", ondelete="SET NULL"))
    created_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    master_id: Mapped[int | None] = mapped_column(ForeignKey("masters.id", ondelete="SET NULL"), index=True)
    # Snapshot of data at creation (car could be edited later)
    brand: Mapped[str] = mapped_column(String(64))
    model: Mapped[str] = mapped_column(String(64))
    year: Mapped[int | None] = mapped_column(Integer)
    plate: Mapped[str | None] = mapped_column(String(20))
    body_type: Mapped[str | None] = mapped_column(String(16))
    mobility: Mapped[str] = mapped_column(String(10), default="drive")  # drive|onsite|tow
    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)
    location_note: Mapped[str | None] = mapped_column(String(300))
    photo_id: Mapped[str | None] = mapped_column(String(256))
    photo_ids: Mapped[str | None] = mapped_column(Text)            # JSON list, up to 3 photos
    car_desc: Mapped[str | None] = mapped_column(Text)             # year, engine, mileage, plate — free text
    service_list: Mapped[str | None] = mapped_column(Text)         # JSON list of selected service codes
    desired_date: Mapped[datetime | None] = mapped_column(DateTime)
    service_code: Mapped[str] = mapped_column(String(32), index=True)
    problem: Mapped[str] = mapped_column(Text)
    client_name: Mapped[str] = mapped_column(String(128))
    client_phone: Mapped[str] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(16), default="new", index=True)
    ready_at: Mapped[datetime | None] = mapped_column(DateTime)
    master_accepted: Mapped[bool] = mapped_column(Boolean, default=False)
    source: Mapped[str] = mapped_column(String(16), default="telegram")  # telegram|owner|ai|site
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now, onupdate=now)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime)
    master: Mapped[Master | None] = relationship(lazy="joined")


class RequestHistory(Base):
    __tablename__ = "request_history"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    request_id: Mapped[int] = mapped_column(ForeignKey("requests.id", ondelete="CASCADE"), index=True)
    at: Mapped[datetime] = mapped_column(DateTime, default=now)
    actor_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    actor_name: Mapped[str] = mapped_column(String(128), default="")
    actor_role: Mapped[str] = mapped_column(String(10), default="system")
    action: Mapped[str] = mapped_column(String(32))   # i18n key suffix: h_<action>
    details: Mapped[str] = mapped_column(Text, default="")


class Notification(Base):
    __tablename__ = "notifications"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    request_id: Mapped[int | None] = mapped_column(ForeignKey("requests.id", ondelete="SET NULL"), index=True)
    chat_id: Mapped[int] = mapped_column(BigInteger)
    kind: Mapped[str] = mapped_column(String(32))
    text: Mapped[str] = mapped_column(Text)
    ok: Mapped[bool] = mapped_column(Boolean, default=True)
    error: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class Setting(Base):
    __tablename__ = "settings"
    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[str] = mapped_column(Text)


class Invite(Base):
    """One-time deep-link invitation for a master: t.me/<bot>?start=m_<token>."""
    __tablename__ = "invites"
    __table_args__ = (UniqueConstraint("token"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    token: Mapped[str] = mapped_column(String(32))
    role: Mapped[str] = mapped_column(String(10), default="master")
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    used_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


engine = create_async_engine(config.database_url, echo=False, pool_pre_ping=True)
Session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


def _add_missing_columns(sync_conn) -> None:
    """Lightweight migration: add columns that exist in the models but not yet in the DB."""
    insp = inspect(sync_conn)
    for table in Base.metadata.sorted_tables:
        if not insp.has_table(table.name):
            continue
        existing = {c["name"] for c in insp.get_columns(table.name)}
        for col in table.columns:
            if col.name not in existing:
                ddl = col.type.compile(dialect=sync_conn.dialect)
                sync_conn.execute(text(f'ALTER TABLE {table.name} ADD COLUMN {col.name} {ddl}'))


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.run_sync(_add_missing_columns)
    async with Session() as s:
        existing = set((await s.scalars(select(Service.code))).all())
        for i, (code, emoji) in enumerate(SERVICES):
            if code not in existing:
                s.add(Service(code=code, emoji=emoji, sort=i))
        keys = set((await s.scalars(select(Setting.key))).all())
        for k, v in DEFAULT_SETTINGS.items():
            if k not in keys:
                s.add(Setting(key=k, value=v))
        await s.commit()


async def sync_config_roles() -> list[str]:
    """Apply OWNER_USERNAMES / MASTER_USERNAMES to accounts already in the DB (no /start needed)."""
    from sqlalchemy import func
    changes: list[str] = []
    async with Session() as s:
        for uname in config.master_usernames:
            u = await s.scalar(select(User).where(func.lower(User.username) == uname))
            if not u:
                continue
            m = await s.scalar(select(Master).where(Master.user_id == u.id))
            if m is None:
                s.add(Master(user_id=u.id, name=u.full_name or u.username))
                changes.append(f"@{u.username} -> mechanic")
            elif not m.is_active:
                m.is_active = True
                changes.append(f"@{u.username} -> mechanic re-activated")
        for uname in config.owner_usernames:
            u = await s.scalar(select(User).where(func.lower(User.username) == uname))
            if u and u.role != "owner":
                u.role = "owner"
                changes.append(f"@{u.username} -> owner")
            if u and not await s.scalar(select(Owner).where(Owner.user_id == u.id)):
                s.add(Owner(user_id=u.id))
        await s.commit()
    return changes


async def get_settings(s: AsyncSession) -> dict[str, str]:
    rows = (await s.scalars(select(Setting))).all()
    data = dict(DEFAULT_SETTINGS)
    data.update({r.key: r.value for r in rows})
    return data
