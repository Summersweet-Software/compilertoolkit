# from abc import ABC, abstractmethod
# from functools import wraps
from typing import Any

from compilertoolkit.ast import (AbstractAstNode, abstractcompilationstep,
                                 compilationstep)
from compilertoolkit.parsing import (Parser, ParseThenCheck, ParsingPattern,
                                     TokenHasType)
from compilertoolkit.tokens import (Ignore, Source, SourcePosition, TokenEnum,
                                    TokenType, create_lexer)

# How the user defines stuff (Example)


class Token[T](TokenEnum[T]):
    """Define all available token types to be used."""

    Comma: TokenType[str] = TokenType(pattern=r"\,")
    Plus: TokenType[str] = TokenType(pattern=r"\+")
    Minus: TokenType[str] = TokenType(pattern=r"\-")
    Mult: TokenType[str] = TokenType(pattern=r"\*")
    Div: TokenType[str] = TokenType(pattern=r"\/")
    Number: TokenType[int] = TokenType(pattern=r"\w+", initializer=int)
    '''integer token example'''
    Keyword: TokenType[str] = TokenType(pattern=r"\d+")

    # Ast Tokens
    # ============
    Expression: TokenType["ExpressionNode"] = TokenType()
    Statement: TokenType["AstNode"] = TokenType()

    # Special and ignore
    whitespace = Ignore(r"\s+")
    EOF: TokenType[None] = TokenType()


class AstNode(AbstractAstNode):
    """Basic Ast Node"""

    __slots__ = ()

    @abstractcompilationstep(0)
    def analyze_types(self, ctx) -> type:
        ...

    @abstractcompilationstep(1)
    def compile(self, ctx) -> Any:
        ...


class ExpressionNode(AstNode):
    """Basic Ast Node"""

    __slots__ = "return_type"

    # instance variables
    return_type: type | None  # Your own type class


class NumberLiteral(ExpressionNode):
    """Basic Ast Node"""

    __slots__ = "value"

    class ParserPattern(ParsingPattern, token_type=Token.Expression):
        value = TokenHasType(Token.Number)

    # instance variables
    value: int

    def __init__(self, tokens: ParserPattern):
        super().__init__(tokens)
        self.value = tokens.value.value

    @compilationstep
    def analyze_types(self, ctx):
        self.return_type = int

    @compilationstep
    def compile(self, ctx):
        return self.value


class SumNode(ExpressionNode):
    """Basic Ast Node"""

    __slots__ = ("lhs", "rhs")

    class ParserPattern(ParsingPattern,
                        token_type=Token.Expression,
                        precedence=1):
        lhs = TokenHasType(Token.Expression)
        operation = TokenHasType(Token.Plus)
        # Parses, then checks for the specified case,
        # errors if the value of the token is unparsed
        rhs = ParseThenCheck(TokenHasType(Token.Expression))

    # instance variables
    lhs: ExpressionNode
    rhs: ExpressionNode

    def __init__(self, tokens: ParserPattern):
        super().__init__(tokens)
        self.lhs = tokens.lhs.value
        self.rhs = tokens.rhs.value

    @compilationstep
    def analyze_types(self, ctx):
        self.lhs.analyze_types(ctx)
        self.rhs.analyze_types(ctx)
        self.return_type = int

    @compilationstep
    def compile(self, ctx):
        return self.lhs.compile(ctx) + self.rhs.compile(ctx)


# Testing
source = Source("9 + 10")
lexer = create_lexer(Token)
lexed_data = lexer.lex(source)
EOF = Token.EOF(SourcePosition(-1, -1, -1, -1, source), None)
parser = Parser(EOF).\
            add_rule(NumberLiteral.ParserPattern).\
            add_rule(SumNode.ParserPattern)

parsed = parser.parse(lexed_data, 0, 0)

if len(parsed) != 1:
    raise Exception()


ast = parsed[0].value

ctx = None

ast.analyze_types(ctx)
print(ast.return_type)
print(ast.compile(ctx))
