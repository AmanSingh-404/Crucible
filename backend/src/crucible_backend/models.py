import uuid
from datetime import datetime

from sqlalchemy import JSON, ForeignKey, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Agent(Base):
    __tablename__ = "agents"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(unique=True)
    profile: Mapped[str]  # "support" | "coding" | "research"
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    runs: Mapped[list["AttackRun"]] = relationship(back_populates="agent")


class AttackRun(Base):
    __tablename__ = "attack_runs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    agent_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("agents.id"))
    status: Mapped[str] = mapped_column(default="pending")  # pending|running|completed|failed
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    agent: Mapped["Agent"] = relationship(back_populates="runs")
    results: Mapped[list["AttackResult"]] = relationship(back_populates="run")


class AttackResult(Base):
    __tablename__ = "attack_results"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("attack_runs.id"))
    attack_type: Mapped[str]
    payload: Mapped[str]
    result: Mapped[str]  # "success" | "failure" | "error"
    defense_verdict: Mapped[dict | None] = mapped_column(JSON, default=None)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    run: Mapped["AttackRun"] = relationship(back_populates="results")
