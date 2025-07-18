from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, String, event


class Function(SQLModel, table=True):
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)
    module: str
    qualname: str
    filename: str
    lineno: int
    signature: str
    annotations: Optional[str] = None
    defaults: Optional[str] = None
    kwdefaults: Optional[str] = None
    closure_vars: Optional[str] = None
    source_code: Optional[str] = None

    calls: List["Call"] = Relationship(back_populates="function")


class Call(SQLModel, table=True):
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)
    function_id: int = Field(foreign_key="function.id")
    parent_call_id: Optional[int] = Field(default=None, foreign_key="call.id")
    timestamp: float
    duration_ms: Optional[float] = None
    thread_id: int
    is_coroutine: bool
    method_type: str
    class_name: Optional[str] = None
    return_value: Optional[str] = Field(
        default=None,
        sa_column=Column("return_value", String(1000))
    )
    exception_type: Optional[str] = None
    exception_message: Optional[str] = None
    tb: Optional[str] = None

    function: "Function" = Relationship(back_populates="calls")
    parent_call: Optional["Call"] = Relationship(
        back_populates="children",
        sa_relationship_kwargs={"remote_side": "Call.id"}
    )
    children: List["Call"] = Relationship(back_populates="parent_call")
    arguments: List["Argument"] = Relationship(back_populates="call")


class Argument(SQLModel, table=True):
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)
    call_id: int = Field(foreign_key="call.id")
    name: str
    value: str = Field(sa_column=Column("value", String(1000)))

    call: "Call" = Relationship(back_populates="arguments")


@event.listens_for(Argument, "before_insert")
def _truncate_value_before_insert(mapper, connection, target):
    if target.value and len(target.value) > 1000:
        target.value = target.value[:1000]


@event.listens_for(Argument, "before_update")
def _truncate_value_before_update(mapper, connection, target):
    if target.value and len(target.value) > 1000:
        target.value = target.value[:1000]


@event.listens_for(Call, "before_insert")
def _truncate_return_before_insert(mapper, connection, target):
    if target.return_value and len(target.return_value) > 1000:
        target.return_value = target.return_value[:1000]


@event.listens_for(Call, "before_update")
def _truncate_return_before_update(mapper, connection, target):
    if target.return_value and len(target.return_value) > 1000:
        target.return_value = target.return_value[:1000]
