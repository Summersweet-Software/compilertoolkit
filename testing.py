from typing import Any
from compilertoolkit.ast import (
    AbstractAstNode,
    abstractcompilationstep,
    compilationstep,
)
from compilertoolkit.parsing import ParseThenCheck, Parser, ParsingPattern, TokenHasType
from compilertoolkit.tokens import (
    Ignore,
    Source,
    SourcePosition,
    TokenEnum,
    TokenType,
    create_lexer,
)


class Token[T](TokenEnum[T]):
    """Part of our own Stuff"""

    Comma: TokenType[str] = TokenType(pattern=r"\,")
    Number: TokenType[str] = TokenType(pattern=r"\d+")
    Keyword: TokenType[str] = TokenType(pattern=r"\w+")
    Plus: TokenType[str] = TokenType(pattern=r"\+")

    Expression: TokenType["ExpressionNode"] = TokenType()
    Statement: TokenType["AstNode"] = TokenType()
    EOF: TokenType[None] = TokenType()

    whitespace = Ignore(r"\s+")  # ignore all whitespace


class AstNode(AbstractAstNode):
    """Basic Ast Node"""

    __slots__ = ()

    @abstractcompilationstep(0)
    def analyze_types(self, ctx):
        pass

    @abstractcompilationstep(1)
    def compile(self, ctx) -> Any:
        pass


class ExpressionNode(AstNode):
    """Basic Ast Node"""

    __slots__ = "return_type"

    # instance variables
    return_type: None | type  # Your own type class


class NumberLiteral(ExpressionNode):
    """Basic Ast Node"""

    __slots__ = "value"

    class ParserPattern(ParsingPattern, token_type=Token.Expression):
        value = TokenHasType(Token.Number)

    # instance variables
    value: int

    def __init__(self, tokens: ParserPattern):
        super().__init__(tokens)
        self.value = int(tokens.value.value)

    @compilationstep
    def analyze_types(self, ctx):
        self.return_type = int

    @compilationstep
    def compile(self, ctx):
        return self.value


class SumNode(ExpressionNode):
    """Basic Ast Node"""

    __slots__ = ("lhs", "rhs")

    class ParserPattern(ParsingPattern, token_type=Token.Expression, precedence=1):
        lhs = TokenHasType(Token.Expression)
        operation = TokenHasType(Token.Plus)
        # Parses, then checks for the specified case, errors if the value of the token is unparsed
        rhs = ParseThenCheck(TokenHasType(Token.Expression))

    # instance variables
    lhs: ExpressionNode
    rhs: ExpressionNode

    def __init__(self, tokens: ParserPattern):
        super().__init__(tokens)
        self.rhs = tokens.rhs.value
        self.lhs = tokens.lhs.value

    @compilationstep
    def analyze_types(self, ctx):
        self.lhs.analyze_types(ctx)
        self.rhs.analyze_types(ctx)
        self.return_type = int

    @compilationstep
    def compile(self, ctx):
        return self.lhs.compile(ctx) + self.rhs.compile(ctx)


source = Source("8 + 12")

lexer = create_lexer(Token)
tokens = lexer.lex(source)
EOF = Token.EOF(SourcePosition(-1, -1, -1, -1, source), None)
parser = Parser(EOF)
parser.add_rule(NumberLiteral.ParserPattern).add_rule(SumNode.ParserPattern)
parsed_tokens = parser.parse(tokens, 0, 0)
print(parsed_tokens[0].value)

parsed_tokens[0].value.analyze_types({})
print(parsed_tokens[0].value.compile({}))
