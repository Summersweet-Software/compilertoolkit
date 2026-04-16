"""Compilation Exceptions.
You pass a source position to these kind of exceptions"""

from compilertoolkit.tokens import SourcePosition


class CompilerError(Exception):
    """An error that happens during compilation. Meant to be extended into user-created errors"""

    positions: list[SourcePosition]
    """Positions of tokens that are CAUSING the error"""

    pattern_position: SourcePosition
    """The encapsulating position of all tokens in the parsing rule that has resulted in a parsing or compiler error"""

    def __init__(
        self,
        positions: list[SourcePosition] | SourcePosition,
        msg: str,
        pattern_position: (
            SourcePosition | None
        ) = None,  # includes all tokens in the pattern being matched against
    ):
        self.msg = msg
        self.positions = positions if isinstance(positions, list) else [positions]
        self.pattern_position = pattern_position or sum(
            self.positions, start=self.positions[0]
        )
        super().__init__(msg)


class ParsingError(CompilerError):
    """Error during the actual parsing of data"""


class UnexpectedToken(ParsingError):
    """An Unexpected Token when parsing has caused an exception to be raised"""


# =======


class ParserError(Exception):
    """Errors in parser construction or execution \
    related to internal failure"""

    pass


class ParserNotFound(ParserError):
    """Parser not found"""

    def __init__(self):
        super().__init__("Parser Not Found")


# * Utilities
# * ==========


def create_underline(
    line: str, problem_pos: list[SourcePosition], pattern_pos: SourcePosition
) -> str:
    """Create a highlight on a SINGLE line. Does not work on multiple lines"""
    underline = " " * (pattern_pos.column - 1)
    underline += "~" * (problem_pos[0].column - pattern_pos.column)

    for c, pos in enumerate(problem_pos):
        underline += "^" * (pos.end_column - pos.column)

        if c < len(problem_pos) - 1:
            underline += "~" * (problem_pos[c + 1].column - pos.end_column)
        elif c == len(problem_pos) - 1:
            underline += "~" * (pattern_pos.end_column - pos.end_column)

    return underline


def format_file_position(e: SourcePosition, /):
    """Format a source position into a string that lets you click in your IDE to that specific file line/col"""
    return f"{e.source.path + "/" if e.source.path else "./"}{e.source.filename}:{e.line-1}:{e.column-1}"


__all__ = ["CompilerError"]
