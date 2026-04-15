from typing import Any, Never, Self, overload


class BaseBox(object):
    _attrs_: list[str] = []


class SourcePosition(object):
    idx: int
    lineno: int
    colno: int

    def __init__(self, idx: int, lineno: int, colno: int):
        ...

    def __repr__(self) -> str:
        ...


class Token[N: str, V](BaseBox):
    name: N
    value: V
    source_pos: SourcePosition | None

    def __init__(self, name: N, value: V, source_pos=None):
        ...

    def __repr__(self) -> str:
        ...

    @overload
    def __eq__(self, other: Self) -> bool:
        ...

    @overload
    def __eq__(self, other: Any) -> Never:
        ...

    def gettokentype(self) -> N:
        ...

    def getsourcepos(self) -> SourcePosition:
        ...

    def getstr(self) -> N:
        ...
