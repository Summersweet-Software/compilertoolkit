"""Utilities for creation and use for arbitrarily sized tree structures.
The intent is for use in module/package trees"""

from typing import Any, Literal, Never, Protocol, Self, Sequence, overload


class Leaf(Protocol):
    """All things a leaf node MUST have."""

    def matches(self, name: object) -> bool:
        """Match this node based on some input param. Useful for module name resolution"""
        ...

    def __eq__(self, other: Any) -> bool: ...


class NTree[L: Leaf, I: str]():
    """
    NTree[L: Leaf, I: str]
    ======
    A tree structure with the ability to hold N# of "leaf" objects

    L - The leaf type
    I - The type of the tree indentifier

    Note
    #####

    You *should* subclass this if you want to add more details or change how matching works.

    """

    __slots__ = "children", "identifier"

    children: list["L | NTree[L, I]"]
    identifier: I | None
    """An identifiable "name" of some kind. Useful for tree matching/comparison"""

    def __init__(
        self, leaves: Sequence[L | Self] | None = None, identifier: I | None = None
    ):
        if leaves is None:
            self.children = []
        else:
            self.children = list(leaves)
        self.identifier = identifier

    def add_leaf(self, leaf: "L | NTree[L, I]") -> Self:
        """Append a single leaf"""
        self.children.append(leaf)
        return self

    def add_leaves(self, leaves: list["L | NTree[L, I]"]) -> Self:
        """Append a single leaf"""
        self.children += leaves
        return self

    def matches(self, name: object) -> bool:
        """Match against this node based on some input "name". Useful for package name resolution.
        defaults to using __eq__ method
        """
        if isinstance(name, NTree):
            return self.identifier == name.identifier
        return self.identifier == name

    # overwrite to make your life easier!
    def copy(self) -> Self:
        return self.__class__(leaves=list(self.children), identifier=self.identifier)

    @overload
    def overlaps(self, other_tree: "NTree") -> bool: ...

    @overload
    def overlaps(self, other_tree: Any) -> Never: ...

    def overlaps(self, other_tree: "NTree | Any") -> bool | Never:
        """Check for overlapping trees"""
        if not isinstance(other_tree, NTree):
            raise TypeError(other_tree)

        return other_tree.matches(self.identifier) and len(
            [
                child  # get overlap of subtrees
                for child in self.children
                for other_child in other_tree.children
                if isinstance(child, NTree)
                and isinstance(other_child, NTree)
                and (child.overlaps(other_child))
            ]
            + [
                child  # get overlap of leaves
                for other_child in other_tree.children
                for child in self.children
                if not isinstance(child, NTree)
                and not isinstance(other_child, NTree)
                and (child == other_child)
            ]
        ) == len(other_tree.children)

    def _combine(self, other: "NTree[L, I]") -> "list[L | NTree[L, I]]":
        """combine two trees- including sub-trees by identifying intersections"""

        output = list(self.children)
        for other_child in other.children:
            for c, child in enumerate(output):
                if not isinstance(other_child, NTree) or not isinstance(child, NTree):
                    if child == other_child:
                        break  # we had a match- this element is already in our child list
                    continue  # no match- move to next item
                if child.matches(other_child):
                    output[c] = (
                        child | other_child
                    )  # do a combine of these trees since they are the SAME tree
                    break
            else:  # use no-break to detect if there were ZERO MATCHES
                output.append(
                    other_child
                )  # do typical appending since this element isnt found in our own child list
        return output

    def _intersect(self, other: "NTree[L, I]") -> "list[L | NTree[L, I]]":
        output = []
        for other_child in other.children:
            for child in self.children:
                if child in output:
                    continue
                if not isinstance(other_child, NTree) or not isinstance(child, NTree):
                    if child == other_child:
                        output.append(child)  # append child that had a match
                elif child.matches(
                    other_child
                ):  # both are children are trees and are the same tree
                    output.append(
                        child & other_child
                    )  # get overlap of these trees since they are the SAME tree
        return output

    def __or__(self, other: "NTree[L, I]") -> "NTree[L, I]":
        """Calculate the combined tree"""
        if not isinstance(other, NTree):
            raise TypeError(other)

        return self.__class__(leaves=self._combine(other), identifier=self.identifier)

    def __ior__(self, other: "NTree[L, I] | object"):
        """Calculate the combined tree"""
        if not isinstance(other, NTree):
            raise TypeError(other)

        self.children = self._combine(other)

    def __add__(self, other: "NTree[L, I] | L | Sequence[NTree[L, I] | L]") -> Self:
        if isinstance(other, Sequence):
            return self.__class__(
                leaves=self.children + list(other), identifier=self.identifier
            )
        return self.__class__(
            leaves=self.children + [other], identifier=self.identifier
        )

    def __iadd__(self, other: "NTree[L, I] | L | Sequence[NTree[L, I] | L]"):
        if isinstance(other, Sequence):
            self.children = self.children + list(other)
            return
        self.children = self.children + [other]

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, NTree):
            return False
        return other.identifier == self.identifier and other.children == self.children

    def __and__(self, other: "NTree[Any, I] | object") -> "NTree[Any, I] | Never":
        """Get overlap/intersection of trees (Useful for module/package resolution!)"""
        if not isinstance(other, NTree):
            raise TypeError(other)

        return self.__class__(leaves=self._intersect(other), identifier=self.identifier)

    def __iand__(self, other: "NTree[Any, I] | object"):
        """Get overlap/intersection of trees (Useful for module/package resolution!)"""
        if not isinstance(other, NTree):
            raise TypeError(other)

        self.children = self._intersect(other)

    @overload
    def __getitem__(self, key: I) -> "NTree[L, I]":
        """Get a tree based on a tree identifier/matching"""
        ...

    @overload
    def __getitem__(self, key: object) -> L:
        """Get Any leaf node based on arbitrary key (will use .matches defined in Leaf protocol)"""
        ...

    def __getitem__(self, key: I | object) -> "L | NTree[L, I]":
        """Get a subtree or leaf node based on a key: I | Any"""
        for child in self.children:
            if child.matches(key):
                return child
        raise KeyError(key)

    @overload
    def __setitem__(self, key: I, value: "NTree[L, I]"):
        """Set a subtree item based on a tree identifier/matching"""
        ...

    @overload
    def __setitem__(self, key: object, value: L):
        """set a leaf node based on arbitrary key (will use .matches defined in Leaf protocol)"""
        ...

    def __setitem__(self, key: I | object, value: "NTree[L, I] | L"):
        """Get a subtree or leaf node based on a key: I | Any"""
        for c, child in enumerate(self.children):
            if child.matches(key):
                self.children[c] = value
                return
        raise KeyError(key)

    def __delitem__(self, key: I | object):
        """Deletes the *first* matching item"""
        for c, child in enumerate(self.children):
            if child.matches(key):
                del self.children[c]
                return
        raise KeyError(key)

    def __str__(self) -> str:
        return f"(Tree: {self.identifier} | [{', '.join(str(child) for child in self.children)}])"
