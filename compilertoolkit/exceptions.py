"""Compilation Exceptions.
You pass a source position to these kind of exceptions"""

from compilertoolkit.tokens import SourcePosition


class CompilerError(Exception):
    def __init__(self, positions: list[SourcePosition] | SourcePosition, msg: str):
        self.msg = ...
        super().__init__(msg)


class ParserError(Exception):
    """Errors in parser construction or execution \
    related to internal failure"""

    pass


class ParserNotFound(ParserError):
    """Parser not found"""

    def __init__(self):
        super().__init__("Parser Not Found")


__all__ = ["CompilerError"]
