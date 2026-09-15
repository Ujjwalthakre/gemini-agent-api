# app/db.py
from datetime import datetime
from typing import Optional, List
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Text, Float, DateTime, select

from app.config import settings

engine = create_async_engine(settings.database_url, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[str] = mapped_column(String(255), index=True)
    role: Mapped[str] = mapped_column(String(50))
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class ToolTrace(Base):
    __tablename__ = "tool_traces"
    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[str] = mapped_column(String(255), index=True)
    tool_name: Mapped[str] = mapped_column(String(255))
    arguments: Mapped[str] = mapped_column(Text)
    result: Mapped[str] = mapped_column(Text)
    latency: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def save_message(session_id: str, role: str, content: str):
    async with AsyncSessionLocal() as session:
        msg = ChatMessage(session_id=session_id, role=role, content=content)
        session.add(msg)
        await session.commit()

async def get_history(session_id: str) -> List[dict]:
    async with AsyncSessionLocal() as session:
        stmt = select(ChatMessage).where(ChatMessage.session_id == session_id).order_by(ChatMessage.created_at)
        result = await session.execute(stmt)
        messages = result.scalars().all()
        return [{"role": m.role, "content": m.content} for m in messages if m.content]

async def save_trace(session_id: str, tool_name: str, arguments: str, result: str, latency: float):
    async with AsyncSessionLocal() as session:
        trace = ToolTrace(session_id=session_id, tool_name=tool_name, 
                          arguments=arguments, result=result, latency=latency)
        session.add(trace)
        await session.commit()