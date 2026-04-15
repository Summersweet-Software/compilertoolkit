from typing import Self
from .token import Token
from .lexergenerator import Rule, Match


class Lexer(object):
    rules: list[Rule]
    ignore_rules: list[Rule]

    def __init__(self, rules: list[Rule], ignore_rules: list[Rule]):
        ...

    def lex(self, s: str) -> "LexerStream":
        ...


class LexerStream(object):
    lexer: Lexer
    s: str
    idx: int

    _lineno: int
    _colno: int

    def __init__(self, lexer: Lexer, s: str):
        ...

    def __iter__(self) -> Self:
        ...

    def _update_pos(self, match: Match) -> int:
        ...

    def next(self) -> Token:
        ...

    def __next__(self) -> Token:
        ...
