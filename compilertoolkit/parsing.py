from abc import ABC, abstractmethod
from collections.abc import MutableSequence
from typing import (
    TYPE_CHECKING,
    Any,
    Final,
    Generator,
    Literal,
    Self,
    Sequence,
    Type,
    overload,
)

from compilertoolkit.exceptions import ParserNotFound, ParsingError, UnexpectedToken
from compilertoolkit.tokens import TokenEnum, TokenType

if TYPE_CHECKING:
    from compilertoolkit.ast import AbstractAstNode


class TokenPattern[T](ABC):
    """A way to match an individual token"""

    __slots__ = "idx"

    idx: int
    """Index of the token in a parser pattern"""

    def __init__(self):
        self.idx = 0

    @abstractmethod
    def eval(
        self,
        token: TokenEnum,
        index: int,
        precedence,
        pattern_precedence=None,
        parser=None,
    ) -> bool:
        pass

    def __set_name__(self, owner, name):
        self.idx = owner._IDX
        owner._IDX += 1

    @overload
    def __get__(self, inst: "ParsingPattern", owner: Any) -> TokenEnum[T]: ...

    @overload
    def __get__(self, inst: Any, owner: Any) -> Self: ...

    def __get__(self, inst: "ParsingPattern | Any", owner: Any) -> TokenEnum[T] | Self:
        if inst is None:
            return self
        return inst._children[self.idx]

    def __set__(self, value, inst):
        inst._children[self.idx] = value


class TokenHasType(TokenPattern):
    __slots__ = "typ"

    def __init__(self, typ: TokenType):
        self.typ = typ

    def eval(
        self,
        token: TokenEnum,
        index: int,
        precedence,
        pattern_precedence=None,
        parser=None,
    ) -> bool:
        return token.typ == self.typ


class TokenValueIsInstance(TokenPattern):
    __slots__ = "typ"

    def __init__(self, typ: Type | tuple[Type]):
        self.typ = typ

    def eval(
        self,
        token: TokenEnum,
        index: int,
        precedence,
        pattern_precedence=None,
        parser=None,
    ) -> bool:
        return isinstance(token.typ, self.typ)


class TokenHasValue(TokenPattern):
    __slots__ = "val"

    def __init__(self, val: Any):
        self.val = val

    def eval(
        self,
        token: TokenEnum,
        index: int,
        precedence,
        pattern_precedence=None,
        parser=None,
    ) -> bool:
        return token.value == self.val


class ParseThenCheck(TokenPattern):
    __slots__ = "node", "err_on_false"

    node: TokenPattern
    err_on_false: Literal[False] | str

    def __init__(self, node: TokenPattern, err_on_false: Literal[False] | str = False):
        self.node = node
        self.err_on_false = err_on_false

    def eval(
        self,
        token: TokenEnum,
        index: int,
        precedence,
        pattern_precedence=None,
        parser=None,
    ) -> bool:
        if parser is None:
            raise ParserNotFound()
        out = self.node.eval(
            parser(self.idx, pattern_precedence)[index],
            precedence,
            pattern_precedence,
            parser,
        )
        if not out and self.err_on_false:
            raise UnexpectedToken(token.position, self.err_on_false)
        return out


class ParsingPatternMeta(type):
    _OWNER: Type

    def __set_name__(self, owner, name):
        self._OWNER = owner


class ParsingPattern(metaclass=ParsingPatternMeta):
    """Matching multiple tokens, acts similarly to a namedtuple"""

    __slots__ = "_children"

    # class attributes
    _PATTERNS: dict[str, TokenPattern]
    _IDX = 0
    _PATTERN_PRECEDENCE: int | None
    _TOKEN_TYPE: TokenType

    # instance variables
    _children: list[TokenEnum]

    def __init_subclass__(
        cls, *, token_type: TokenType, precedence: int | None = None
    ) -> None:
        cls._IDX = 0  # reset this tracking variable
        cls._TOKEN_TYPE = token_type
        cls._PATTERN_PRECEDENCE = precedence
        cls._PATTERNS = {
            name: value
            for name, value in cls.__dict__.items()
            if isinstance(value, TokenPattern)
        }

    def __init__(self, items: MutableSequence[TokenEnum]):
        self._children = list(items)

    @classmethod
    def eval(
        cls, tokens: MutableSequence[TokenEnum], index: int, precedence, parser
    ) -> bool:
        if cls._PATTERN_PRECEDENCE is not None and precedence > cls._PATTERN_PRECEDENCE:
            return False
        try:
            return all(
                child.eval(
                    token, c + index, precedence, cls._PATTERN_PRECEDENCE, parser
                )
                for c, (token, child) in enumerate(zip(tokens, cls._PATTERNS.values()))
            )
        except ParsingError as e:
            position = sum(tok.position for tok in tokens)
            if isinstance(position, int):
                raise ValueError(position)

            e.pattern_position = position
            raise e  # added information for reraise

    def __iter__(self) -> Generator[TokenEnum, None, None]:
        yield from self._children

    def set_parents(self, parent: "AbstractAstNode"):
        from compilertoolkit.ast import AbstractAstNode

        for child in self._children:
            if child.value is not None and isinstance(child.value, AbstractAstNode):
                child.value.set_parent(parent)


class Parser:
    __slots__ = ("rules", "eof")

    rules: list[Type[ParsingPattern]]
    eof: Final[TokenEnum[None]]

    def __init__(self, EOF_token: TokenEnum[None]):
        self.rules = []
        self.eof = EOF_token

    def add_rule(self, rule: Type[ParsingPattern]) -> Self:
        self.rules.append(rule)
        return self

    def add_rules(self, rules: list[Type[ParsingPattern]]) -> Self:
        self.rules += rules
        return self

    def get_tokens(self, tokens: MutableSequence[TokenEnum[Any]], start: int, end: int):
        if start > len(tokens):
            return [self.eof] * (end - start)
        return list(tokens[start : min(end, len(tokens))]) + (
            [self.eof] * ((end - start) - (min(end, len(tokens)) - start))
        )

    def parse(
        self, _tokens: Sequence[TokenEnum[Any]], offset: int, precedence: int
    ) -> list[TokenEnum[Any]]:
        """Notice: the tokens list will be edited"""
        # relies on editing a singular list instance-
        #  we must not reinstantiate the list
        if not isinstance(_tokens, list):
            tokens = list(_tokens)
        else:
            tokens = _tokens

        def parser(n_offset, n_precedence):
            return self.parse(tokens, offset + n_offset, n_precedence)

        for rule in self.rules:
            rule_tokens = self.get_tokens(tokens, offset, offset + len(rule._PATTERNS))
            if rule.eval(rule_tokens, offset, precedence, parser):
                tok = rule._OWNER(
                    rule(self.get_tokens(tokens, offset, offset + len(rule._PATTERNS)))
                )

                for _ in range(len(rule._PATTERNS) - 1):
                    del tokens[offset]

                tokens[offset] = rule._TOKEN_TYPE(tok.position, tok)
                self.parse(tokens, offset, precedence)
                break
        return tokens


__all__ = ["ParsingPattern", "TokenPattern"]
