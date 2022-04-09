"""
Command registration module.

Use this module to register commands
from another particular module.
"""

import importlib
import importlib.util

from types import ModuleType
from typing import Callable, TypeVar

from click import Command, Group


ClickCmd = TypeVar("ClickCmd", Command, Group)


class ModuleCommand:
    __slots__ = ("__cmd", "__module", "__name")

    __cmd:    Command | Group
    __module: str
    __name:   str | None

    def __init__(self, cmd: ClickCmd, *,
        module: str = None, name: str = None, **kwds):

        self.__cmd    = cmd
        self.__module = module or cmd.callback.__module__
        self.__name   = name or cmd.name

    @property
    def command(self):
        return self.__cmd

    @property
    def module(self):
        return self.__module

    @property
    def name(self):
        return self.__name


Namespace    = dict[str, ModuleCommand]
RegistryDict = dict[str, Namespace]

IT              = TypeVar("IT")
InstanceDict    = dict[type[IT], IT]
InstanceWrapper = Callable[[IT], IT]

GroupWrapper    = InstanceWrapper[Group]
ClickCmdWrapper = InstanceWrapper[ClickCmd]


class ModuleNamespace(ModuleType):
    __commands__: Namespace

    @staticmethod
    def pre_command_load() -> None:
        ...

    @staticmethod
    def post_command_load() -> None:
        ...


class RegistryMeta(type):
    _registry_:  RegistryDict
    _instances_: InstanceDict["Registry"] = {}

    @classmethod
    def _get_instance(cls, sub_cls: type["Registry"]):
        if sub_cls not in cls._instances_:
            cls._instances_[sub_cls] = object.__new__(sub_cls)
        return cls._instances_[sub_cls]

    def __init__(cls, *args, **kwargs):
        cls._registry_  = {}

    def _get_namespace(cls, module_cmd: ModuleCommand) -> Namespace:
        return cls._registry_.get(module_cmd.module, {})

    def _update_namespace(cls, module_cmd: ModuleCommand, namespace: dict):
        cls._registry_[module_cmd.module] = namespace

    @property
    def namespaces(cls):
        return cls._registry_


class Registry(metaclass=RegistryMeta):

    def __new__(cls):
        return cls._get_instance(cls)

    def __str__(self):
        return f"{type(self).__name__}({self._registry_})"

    @classmethod
    def register(cls, module_cmd: ModuleCommand):
        namespace = cls._get_namespace(module_cmd)
        namespace |= {module_cmd.name: module_cmd}

        cls._update_namespace(module_cmd, namespace)

    @classmethod
    def get(cls, module: ModuleNamespace | ModuleType | str):
        if isinstance(module, (ModuleNamespace, ModuleType)):
            module = module.__name__
        return cls.namespaces.get(module, {})


def module_command(cmd: ClickCmd = None, *,
        module: str = None, name: str = None, registry: Registry = None):

    _registry = registry or Registry()

    def inner(cmd: ClickCmd):
        _registry.register(
            ModuleCommand(cmd, module=module, name=name))
        return cmd

    if not cmd:
        return inner
    return inner(cmd)


def load_namespace(module: str, *,
        package: str = None, registry: Registry = None) -> ModuleNamespace:

    module   = ".".join([i for i in (package, module) if i])
    registry = registry or Registry()

    mod = importlib.import_module(module)
    mdn = ModuleNamespace(mod.__name__, mod.__doc__)

    body = {} #type: ignore[var-annotated]
    for base in (mdn, mod):
        body |= base.__dict__

    mdn.__dict__.update(body)
    setattr(mdn, "__commands__", registry.get(mod))

    return mdn


def register_namespace(module: str, *,
        package: str = None, registry: Registry = None, **kwds):

    namespace = load_namespace(module,
        package=package, registry=registry)

    def wrapper(group: Group):
        namespace.pre_command_load()

        for _, command in namespace.__commands__.items():
            group.add_command(command.command)

        namespace.post_command_load()
        return group

    return wrapper
