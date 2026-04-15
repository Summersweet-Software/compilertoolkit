from typing import Any

from compilertoolkit.ntree import NTree


class ModuleName:
    """Refer to module name, used simply for matching. Basically a speculation on a module we hope exists"""

    def __init__(self, name: str):
        self.name = name

    def matches(self, name: object) -> bool:
        """Match this node based on some input param. Useful for module name resolution"""
        if not isinstance(name, (ModuleName, Module)):
            return self.name == name
        return self.name == name.name

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, ModuleName):
            return self.name == other.name
        return self is other

    def __str__(self) -> str:
        return self.name


class Module:

    def __init__(self, name: str):
        self.name = name

    def matches(self, name: object) -> bool:
        """Match this node based on some input param. Useful for module name resolution"""
        if not isinstance(name, (Module, ModuleName)):
            return self.name == name
        return self.name == name.name

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, ModuleName):
            return self.name == other.name
        return self is other

    def __str__(self) -> str:
        return f"<MODULE {self.name}>"


imports = NTree[Module, str](
    identifier="base",
    leaves=[
        Module("main"),
        Module("other_mod"),
        NTree(
            identifier="lib",
            leaves=[
                Module("math"),
                Module("system"),
                Module("err"),
                NTree(
                    identifier="ui", leaves=[Module("application"), Module("widgets")]
                ),
            ],
        ),
    ],
)

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

print(imports.overlaps(trying_to_import))  # should be true
print(imports.overlaps(trying_to_import_2))  # should be true
print(imports.overlaps(trying_to_import_partial))  # should be false
print()
print(imports & trying_to_import)
print(imports & trying_to_import_2)
print(imports & trying_to_import_partial)

print()

trying_to_import_resolved = imports & trying_to_import

trying_to_import_2_resolved = imports & trying_to_import_2

trying_to_import_partial_resolved = NTree[Module, str](
    identifier="base",
    leaves=[NTree(identifier="lib", leaves=[Module("something_that_does_not_exist")])],
)

print(imports | trying_to_import_resolved)
print(imports | trying_to_import_2_resolved)
print(imports | trying_to_import_partial_resolved)


print()

lib_pkg = imports["lib"]
print(lib_pkg)

main_mod = imports[ModuleName("main")]
print(main_mod)
