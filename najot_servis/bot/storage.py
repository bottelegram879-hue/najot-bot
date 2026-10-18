"""FSM storage in the main database, so half-filled requests survive bot restarts."""
import json
from typing import Any, Mapping

from aiogram.fsm.state import State
from aiogram.fsm.storage.base import BaseStorage, StateType, StorageKey
from sqlalchemy import String, Text, select
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base, Session


class FsmRecord(Base):
    __tablename__ = "fsm_states"
    key: Mapped[str] = mapped_column(String(128), primary_key=True)
    state: Mapped[str | None] = mapped_column(String(128))
    data: Mapped[str] = mapped_column(Text, default="{}")


def _key(k: StorageKey) -> str:
    return f"{k.bot_id}:{k.chat_id}:{k.user_id}:{k.thread_id or 0}:{k.destiny}"


class DbStorage(BaseStorage):
    async def _get(self, s, key: StorageKey) -> FsmRecord:
        rec = await s.get(FsmRecord, _key(key))
        if rec is None:
            rec = FsmRecord(key=_key(key), state=None, data="{}")
            s.add(rec)
        return rec

    async def set_state(self, key: StorageKey, state: StateType = None) -> None:
        async with Session() as s:
            rec = await self._get(s, key)
            rec.state = state.state if isinstance(state, State) else state
            await s.commit()

    async def get_state(self, key: StorageKey) -> str | None:
        async with Session() as s:
            rec = await s.get(FsmRecord, _key(key))
            return rec.state if rec else None

    async def set_data(self, key: StorageKey, data: Mapping[str, Any]) -> None:
        async with Session() as s:
            rec = await self._get(s, key)
            rec.data = json.dumps(dict(data), ensure_ascii=False, default=str)
            await s.commit()

    async def get_data(self, key: StorageKey) -> dict[str, Any]:
        async with Session() as s:
            rec = await s.get(FsmRecord, _key(key))
            return json.loads(rec.data) if rec and rec.data else {}

    async def close(self) -> None:
        return None
