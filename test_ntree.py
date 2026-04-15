from typing import TYPE_CHECKING, Any, Self, Sequence, Union, overload, override

from compilertoolkit.ntree import Leaf, NTree


class PrivateImportExc(Exception):
    pass


class ModuleName:
    """Refer to module name, used simply for matching. Basically a speculation on a module we hope exists"""

    def __init__(self, name: str, parent=None):
        self.name = name
        self.parent: Package | None = parent

    def matches(self, name: object) -> bool:
        """Match this node based on some input param. Useful for module name resolution"""
        if not isinstance(name, (ModuleName, Module)):
            return self.name == name
        return self.name == name.name

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, ModuleName):
            return self.name == other.name
        if isinstance(other, ModuleView):
            return other == self
        return self is other

    def __str__(self) -> str:
        return self.name


def has_common_parent(
    pkg: "Package | ModuleView | None", other_pkg: "Package | ModuleView | None"
) -> bool:
    if isinstance(pkg, ModuleView):
        pkg = pkg.parent

    if isinstance(other_pkg, ModuleView):
        other_pkg = other_pkg.parent

    if pkg is None or other_pkg is None:
        return pkg is None and other_pkg is None

    if pkg.identifier == other_pkg.identifier and pkg.parent == other_pkg.parent:
        return True

    return other_pkg.parent is not None and has_common_parent(pkg, other_pkg.parent)


class Module:
    name: str
    private: bool

    def __init__(self, name: str, private=False):
        self.name = name
        self.private = private

    def matches(self, name: object) -> bool:
        """Match this node based on some input param. Useful for module name resolution"""
        if not isinstance(name, (Module, ModuleName)):
            return self.name == name
        return self.name == name.name

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, ModuleName):
            return self.name == other.name
        if isinstance(other, ModuleView):
            return self.name == other.mod.name
        return self is other

    def __str__(self) -> str:
        return f"<MODULE {self.name}>"


class ModuleView:
    mod: "Module"
    parent: "Package | None"  # Never want to modify the parent of the original package! So we use a view instead!

    def __init__(self, mod: "Module", parent: "Package | None" = None):
        self.parent = parent
        self.mod = mod

    def copy(self):
        return self.__class__(self.mod, self.parent)

    def matches(self, name: object) -> bool:
        """Match this node based on some input param. Useful for module name resolution"""
        if not self.mod.matches(name):
            return False
        if self.mod.private:
            if isinstance(name, (ModuleView, ModuleName)) and not has_common_parent(
                self.parent, name.parent
            ):
                raise PrivateImportExc(f"Module: {name} is private!")

        return True

    def __eq__(self, other: Any) -> bool:
        return self.mod == other

    def __str__(self) -> str:
        return f"<MODULE {self.mod.name}>"


class Package(NTree[ModuleView, str]):
    """An example of an extension of NTree"""

    __slots__ = "parent"

    parent: "Package | None"

    def __init__(
        self,
        parent: Self | None = None,
        leaves: Sequence[ModuleView | Module | Self] | None = None,
        identifier: str = "",
    ):
        self.parent = parent
        self.children = []
        self.identifier = identifier

        if leaves is not None:
            self.add_leaves(leaves)

    def copy(self):
        copy = super().copy()
        copy.parent = self.parent
        return copy

    def deep_copy(self):
        copy = super().copy()
        copy.parent = self.parent
        self.children = [
            child.deep_copy() if isinstance(child, self.__class__) else child.copy()
            for child in self.children
        ]
        return copy

    def __eq__(self, other):
        return (
            isinstance(other, Package)
            and (
                (self.parent is None and other.parent is None)
                or (
                    self.parent is not None
                    and other.parent is not None
                    and self.parent.identifier == other.parent.identifier
                )
            )
            and super().__eq__(other)
        )

    def add_leaf(self, leaf: ModuleView | Module | Self):
        if isinstance(leaf, Module):
            leaf = ModuleView(leaf, parent=self)
        if isinstance(leaf, (self.__class__, ModuleView)):
            leaf.parent = self
        return super().add_leaf(leaf)

    # only override the stubs to make our IDE happy. if not type-checking, don't worry about it.
    if TYPE_CHECKING:

        def add_leaves(self, leaves: Sequence[ModuleView | Module | Self]) -> Self: ...

        def set_leaves(self, leaves: Sequence[ModuleView | Module | Self]) -> Self: ...


# Our global list of packages and modules we might have.
imports = Package(
    identifier="base",
    leaves=[
        Module("main", private=True),
        Module("other_mod"),
        Package(
            identifier="lib",
            leaves=[
                Module("math"),
                Module("system"),
                Module("err"),
                Package(
                    identifier="ui",
                    leaves=[
                        Module("application"),
                        Module("widgets"),
                        Module("internal_stuff", private=True),
                        Package(
                            identifier="bindings",
                            leaves=[
                                Module("application", private=True),
                                Module("widgets", private=True),
                            ],
                        ),
                    ],
                ),
            ],
        ),
    ],
)


# Setup trees to do testing against
# ===================================

trying_to_import = NTree[ModuleName, str](
    identifier="base", leaves=[ModuleName("other_mod")]
)

trying_to_import_2 = NTree[ModuleName, str](
    identifier="base",
    leaves=[NTree(identifier="lib", leaves=[ModuleName("math")])],
)

trying_to_import_partial = NTree[ModuleName, str](
    identifier="base",
    leaves=[
        NTree(identifier="lib", leaves=[ModuleName("something_that_does_not_exist")])
    ],
)
# Test Basic overlapping
# ========================
print(imports.overlaps(trying_to_import))  # should be true
print(imports.overlaps(trying_to_import_2))  # should be true
print(imports.overlaps(trying_to_import_partial))  # should be false

assert imports.overlaps(trying_to_import)
assert imports.overlaps(trying_to_import_2)
assert not imports.overlaps(trying_to_import_partial)


# Test Basic intersection
# =========================

print()
print(imports & trying_to_import)
print(imports & trying_to_import_2)
print(imports & trying_to_import_partial)

assert (imports & trying_to_import).children == [imports[ModuleName("other_mod")]]
assert (imports & trying_to_import_2).children == [
    imports["lib"].copy().set_leaves((imports["lib"]["math"],))
]
assert (imports & trying_to_import_partial).children == [
    imports["lib"].copy().set_leaves([])
]

# Test Basic combining
# ======================
print()

trying_to_import_resolved = imports & trying_to_import
trying_to_import_2_resolved = imports & trying_to_import_2
trying_to_import_partial_resolved = Package(
    identifier="base",
    leaves=[
        Package(identifier="lib", leaves=[Module("something_that_does_not_exist")])
    ],
)

print(imports | trying_to_import_resolved)
print(imports | trying_to_import_2_resolved)
print(imports | trying_to_import_partial_resolved)

assert (imports | trying_to_import_resolved) == imports
assert (imports | trying_to_import_2_resolved) == imports
changed_tree = imports.copy()
changed_tree["lib"] = (
    changed_tree["lib"]
    .copy()
    .add_leaf(
        trying_to_import_partial_resolved["lib"][
            ModuleName("something_that_does_not_exist")
        ]
    )
)
assert (imports | trying_to_import_partial_resolved) == changed_tree

# Test Basic tree indexing
# ==========================
print()

lib_pkg = imports["lib"]
print(lib_pkg)
assert isinstance(lib_pkg, Package) and lib_pkg.identifier == "lib"

# Test private imports
# ######################
try:
    imports[ModuleName("main")]  # should not work
    raise Exception("Expect an error")
except PrivateImportExc:
    main_mod = imports[ModuleName("main", parent=imports)]
    print(main_mod)
    assert isinstance(main_mod, ModuleView) and main_mod.mod.name == "main"


# Test private (more) imports
# ############################
try:
    imports["lib"]["ui"][ModuleName("internal_stuff")]  # should not work
    raise Exception("Expect an error")
except PrivateImportExc:
    # Access from same pkg
    private_mod = imports["lib"]["ui"][
        ModuleName("internal_stuff", parent=imports["lib"]["ui"])
    ]
    print(private_mod)
    assert (
        isinstance(private_mod, ModuleView) and private_mod.mod.name == "internal_stuff"
    )

    # Access from module in same pkg
    private_mod = imports["lib"]["ui"][
        ModuleName("internal_stuff", parent=imports["lib"]["ui"][ModuleName("widgets")])
    ]
    print(private_mod)
    assert (
        isinstance(private_mod, ModuleView) and private_mod.mod.name == "internal_stuff"
    )

    # Access from 1 pkg further
    private_mod = imports["lib"]["ui"][
        ModuleName("internal_stuff", parent=imports["lib"]["ui"]["bindings"])
    ]
    print(private_mod)
    assert (
        isinstance(private_mod, ModuleView) and private_mod.mod.name == "internal_stuff"
    )

    # Access from module in 1 pkg further
    private_mod = imports["lib"]["ui"][
        ModuleName(
            "internal_stuff",
            parent=imports["lib"]["ui"]["bindings"][
                ModuleName("application", parent=imports["lib"]["ui"]["bindings"])
            ],
        )
    ]
    print(private_mod)
    assert (
        isinstance(private_mod, ModuleView) and private_mod.mod.name == "internal_stuff"
    )


# Test Tree comparison
# ======================
print()

assert imports != imports | trying_to_import_partial_resolved

assert imports == imports
assert imports == imports.copy()
