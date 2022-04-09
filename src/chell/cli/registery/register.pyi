import typing

from types import ModuleType
from typing import Callable, TypeVar

from click import Command, Group


ClickCmd = TypeVar("ClickCmd", Command, Group)
class ModuleCommand:
    """Command object specific to a module."""
    __cmd:    Command | Group
    __module: str
    __name:   str
    def __init__(self, cmd: ClickCmd, *, module: str = ..., name: str = ..., **kwds) -> None: ...
    @property
    def command(self) -> ClickCmd: ...
    @property
    def module(self) -> str: ...
    @property
    def name(self) -> str: ...

Namespace    = dict[str, ModuleCommand]
RegistryDict = dict[str, Namespace]

IT              = TypeVar("IT")
InstanceDict    = dict[type[IT], IT]
InstanceWrapper = Callable[[IT], IT]

GroupWrapper    = InstanceWrapper[Group]
ClickCmdWrapper = InstanceWrapper[ClickCmd]

class ModuleNamespace(ModuleType):
    """Alias for a module being used for command registration."""
    __commands__: Namespace
    @staticmethod
    def pre_command_load() -> None:
        """Executes prior to commands being loaded."""
    @staticmethod
    def post_command_load() -> None:
        """Executes after commands have been loaded."""

class RegistryMeta(type):
    """Creates a singleton for handling module command registration."""
    _registry_:  RegistryDict
    _instances_: InstanceDict["Registry"]
    @classmethod
    def _get_instance(cls, sub_cls: "Registry") -> "Registry": ...
    def __init__(cls, *args, **kwargs) -> None: ...
    def _get_namespace(cls, module_cmd: ModuleCommand) -> Namespace: ...
    def _update_namespace(cls, module_cmd: ModuleCommand) -> None: ...
    @property
    def namespaces(cls) -> RegistryDict: ...

class Registry(metaclass=RegistryMeta):
    """Singleton responsible for module command registration."""
    def __new__(cls) -> "Registry": ...
    def __str__(registry_cls) -> str: ...
    @classmethod
    def register(cls, module_cmd: ModuleCommand) -> None:
        """Upsert a `ModuleCommand` into this registry."""
    @classmethod
    def get(cls, module: ModuleNamespace | ModuleType | str) -> Namespace:
        """Retrieve the `Namespace` related to a module or module type."""

@typing.overload
def module_command(cmd: ClickCmd) -> ClickCmd: ...

@typing.overload
def module_command(*, module: str = ..., name: str = ..., registry: Registry = ...) -> ClickCmdWrapper: ...

@typing.overload
def module_command(cmd: ClickCmd = ..., *, module: str = ..., name: str = ..., registry: Registry = ...) -> ClickCmdWrapper | ClickCmd:
    """
    Register a `Command` or `Group` to it's
    parent module or target namespace.

    params:
    `module`: name of the module path.

    `name`: name designated to the command object.

    `registry`: designated Registry singleton commands
    are registered to.
    """

def load_namespace(module: str, *, package: str = ..., registry: Registry = ...) -> ModuleNamespace:
    """
    Imports a module as a `ModuleNamespace`
    allowing that we can expect specific hooks
    to be available, even if they were not defined
    in the module itself.
    """

def register_namespace(module: str, *, package: str = ..., registry: Registry = ..., **kwds) -> GroupWrapper:
    """
    Create a wrapper which registers commands
    from the target namespace on to the decorated
    `Group`.
    """
