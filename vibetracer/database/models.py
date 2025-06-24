from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship


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
    return_value: Optional[str] = None
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
    value: str

    call: "Call" = Relationship(back_populates="arguments")
