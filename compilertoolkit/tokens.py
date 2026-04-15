from typing import NamedTuple, Type, Callable

from rply import LexerGenerator
from rply.lexer import Lexer as rplyLexer
from rply.token import Token as rplyToken
from rply.token import SourcePosition as rplySourcePosition


class Source:
    """Represents a source file"""

    __slots__ = ("filename", "path", "contents")

    def __init__(self, contents: str, *, filename="", path=None):
        self.contents = contents
        self.filename = filename
        self.path = path


class SourcePosition(NamedTuple):
    """Source position of a token"""

    line: int
    """The line number of a token's position"""
    column: int
    """Start index of the tokens position on a line"""

    end_line: int
    """The line the token ends on"""
    end_column: int
    """The ending index of the last character of the token \
    on the last line of the position"""

    source: Source

    def __add__(self, other):
        line = min(self.line, other.line)
        end_line = max(self.end_line, other.end_line)
        column = min(self.column, other.column)
        if other.end_line > self.line:
            end_column = other.end_column
        elif self.end_line > other.line:
            end_column = other.end_column
        else:
            end_column = max(self.end_column, other.end_column)

        return SourcePosition(line, column, end_line, end_column, self.source)

    def __radd__(self, other):
        if isinstance(other, int):
            return self
        return self + other


class TokenType[S]:
    """A descriptor for a token type. Allows you to fetch a particular token"""

    __slots__ = ("pattern", "owner", "name", "initializer")

    pattern: str | None
    owner: Type["TokenEnum[S]"]
    name: str
    initializer: Callable[[str], S]

    def __init__(self, /, pattern: str | None = None,
                 initializer: Callable[[str], S] | None = None):
        self.pattern = pattern
        if initializer is None:
            self.initializer = (lambda x: x)  # type: ignore
        else:
            self.initializer = initializer

    def __set_name__(self, owner: Type["TokenEnum[S]"], name: str):
        self.owner = owner
        self.name = name

    def __call__(self, position, value: S) -> "TokenEnum[S]":
        return self.owner(position, self, value)

    def __eq__(self, other):
        return isinstance(other, TokenType) and other.owner == self.owner and self.name == other.name


class Ignore:
    """A descriptor for a token type. Allows you to fetch a particular token"""

    __slots__ = "pattern"

    pattern: str

    def __init__(self, pattern: str):
        self.pattern = pattern


class TokenEnum[T]():
    """Have to redo enum implementation :("""

    __slots__ = ("position", "value", "typ")

    # instance variables
    value: T
    position: SourcePosition
    typ: TokenType

    def __init__(self, position: SourcePosition, typ: TokenType[T], value: T):
        self.position = position
        self.typ = typ
        self.value = value

    def __repr__(self) -> str:
        return f"{self.typ.name}({self.position}, {repr(self.value)})"


class Lexer[T: TokenEnum]():
    """A wrapper around the rply lexer.
    Returns your custom Token types when lexing"""

    __slots__ = "_TokenType", "inner_lexer"

    _TokenType: Type[T]
    inner_lexer: rplyLexer
    '''Internal rply lexer used'''

    def __init__(self, rules, ignore_rules, token_type):
        self._TokenType = token_type
        self.inner_lexer = rplyLexer(rules, ignore_rules)

    def _fix_position(
        self, source: Source, position: rplySourcePosition, value
    ) -> SourcePosition:
        return SourcePosition(
            position.lineno, position.colno, 1, position.colno + len(value), source
        )

    def _fix_token(self, source: Source, token: rplyToken) -> T:
        if token.source_pos is None:
            raise ValueError(token.source_pos)
        return self._TokenType(
            self._fix_position(source, token.source_pos, token.value),
            token.name,
            token.name.initializer(token.value),
        )

    def lex(self, source: Source) -> list[T]:
        output = self.inner_lexer.lex(source.contents)
        return [self._fix_token(source, token) for token in output]


def create_lexer[T: TokenEnum](token_types: Type[T]) -> Lexer[T]:
    '''Create a lexer using your token'''
    lg = LexerGenerator()
    for attr in token_types.__dict__.values():
        if isinstance(attr, TokenType) and attr.pattern is not None:
            lg.add(attr, attr.pattern)
        if isinstance(attr, Ignore):
            lg.ignore(attr.pattern)

    return Lexer(lg.rules, lg.ignore_rules, token_types)


__all__ = ["TokenEnum", "TokenType", "SourcePosition", "Lexer", "create_lexer"]
