"""A module to help with creation of your Ast"""

from abc import ABC, ABCMeta, abstractmethod
from functools import wraps
from types import FunctionType
from typing import Any, Callable, Self, Type

from compilertoolkit.parsing import ParsingPattern


def abstractcompilationstep(order: int):
    """An abstract version of @compilation step"""

    def decorator(func):
        func.__is_compilationstep__ = True
        func.__compilationstep_order__ = order

        @wraps(func)
        @abstractmethod
        def wrapper(self, *args, **kwargs):
            return func(self, *args, **kwargs)

        return wrapper

    return decorator


def compilationstep(func):
    """documentation of compilation steps. Required"""
    func.__is_compilationstep__ = True
    return func


class AbstractAstNodeMeta(ABCMeta):
    _compilationsteps: list[FunctionType]

    def __new__(
        mcls,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, Any],
        /,
        **kwargs: Any,
    ):
        cls = super().__new__(mcls, name, bases, namespace, **kwargs)

        compilationsteps: list[tuple[int, FunctionType]] = [
            (c, step) for c, step in enumerate(getattr(cls, "_compilationsteps", []))
        ]

        for name, item in namespace.items():
            if not isinstance(item, FunctionType):
                continue
            if hasattr(item, "__is_compilationstep__") and hasattr(
                item, "__compilationstep_order__"
            ):
                compilationsteps.append((item.__compilationstep_order__, item))

        compilationsteps.sort(key=lambda x: x[0])
        cls._compilationsteps = [item[1] for item in compilationsteps]

        return cls


class AbstractAstNode[T: ParsingPattern](ABC, metaclass=AbstractAstNodeMeta):
    __slots__ = ("_tokens", "parent")

    # Subclasses
    ParserPattern: Type[T] | list[Type[ParsingPattern]]
    _missing_steps: list

    # instance variables
    parent: Self
    _tokens: T

    def __init_subclass__(cls, *args, **kwargs):
        super().__init_subclass__(*args, **kwargs)
        cls._missing_steps = []

        # ensure all compilation steps exist
        functions = [
            value
            for value in cls.__dict__.values()
            if hasattr(value, "__is_compilationstep__")
        ]
        for step in cls._compilationsteps:
            if any((step.__name__ == func.__name__ for func in functions)):
                continue

            cls._missing_steps.append(step.__name__)

    def __new__(cls, *args, **kwargs):
        if len(cls._missing_steps) > 0:
            raise Exception(f"Undefined Compilation steps: {cls._missing_steps}")
        return super().__new__(cls)

    def __init__(self, tokens: T):
        self._tokens = tokens
        self._tokens.set_parents(self)

    def set_parent(self, parent: Self):
        self.parent = parent

    def walk[S](self, func: Callable[["AbstractAstNode"], S]) -> list[S]:
        """Walk the syntax tree and run a function"""
        return [
            func(self),
            *(
                item
                for token in self._tokens
                if isinstance(token.value, AbstractAstNode)
                for item in token.value.walk(func)
                if item is not None
            ),
        ]

    def collect[S](self, typ: Type[S]) -> list[S]:
        '''Walk the syntax tree and collect all instances of "typ"'''
        output = [self] if isinstance(self, typ) else []
        return output + [
            item
            for token in self._tokens
            if isinstance(token.value, AbstractAstNode)
            for item in token.value.collect(typ)
        ]

    @property
    def position(self):
        return sum((token.position for token in self._tokens))


__all__ = ["AbstractAstNode", "abstractcompilationstep", "compilationstep"]
