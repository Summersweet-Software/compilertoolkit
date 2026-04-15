from typing import Any
from .lexer import Lexer
from .token import SourcePosition


class Rule[N: str](object):
    _attrs_ = ['name', 'flags', '_pattern']
    name: N
    pattern: str
    flags: int

    def __init__(self, name: N, pattern: str, flags=0):
        ...

    def _freeze_(self) -> bool:
        ...

    def matches(self, s: str, pos: SourcePosition):
        ...


class Match(object):
    start: int
    end: int

    def __init__(self, start: int, end: int):
        ...


class LexerGenerator(object):
    rules: list[Rule]
    ignore_rules: list[Rule]

    def __init__(self):
        ...

    def add(self, name: str | Any, pattern: str, flags: int = 0):
        ...

    def ignore(self, pattern: str, flags: int = 0):
        ...

    def build(self) -> Lexer:
        ...
