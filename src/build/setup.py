import contextlib
import dataclasses
import pathlib

from io import StringIO
from os import PathLike
from typing import Any, Callable, IO, Iterable, Mapping, Optional
from typing import Protocol, TypeVar
from typing import runtime_checkable

import setuptools #type: ignore[import]
import yaml

from setuptools import setup, find_packages


ExitStack = TypeVar("ExitStack", bound=contextlib.ExitStack)
Path      = pathlib.Path

OT = TypeVar("OT") # Optional Type
OK = TypeVar("OK") # Optional Key
OV = TypeVar("OV") # Optional Value

CommandOptions = Optional[Mapping[str, setuptools.Command]]
Directories    = Optional[Mapping[str, str]]
SetupOptions   = Optional[dict[str, Any]]

OptionalStr    = Optional[str]
OptionalList   = Optional[list[OT]]
OptionalMap    = Optional[Mapping[OK, OV]]
OptionalDist   = Optional[setuptools.Distribution]

# Determines the root of the project directory
PROJECT_ROOT: Path = pathlib.Path(__file__).parents[0]

# Build file is the expected location, name, and
# format used to determine distribution metadata.
# The below determines different potential search
# paths our build script should suspect a build
# schema.
BUILD_FILENAME: str = "build.yaml"

BUILD_FILES: tuple[Path, ...] = (
    PROJECT_ROOT / BUILD_FILENAME,
    PROJECT_ROOT.parents[0] / BUILD_FILENAME,
    PROJECT_ROOT.parents[1] / BUILD_FILENAME
)

# Requirements file location allows for us to
# determine where the project requirements might
# be annotated. We should alway expect this file
# to be at the root of the project.
REQUIREMENTS_FILE = PROJECT_ROOT.parents[1] / "requirements.txt"


@dataclasses.dataclass
class ConfigBuild:
    """
    Representational Parameter Object.
    used to identify keyword values for
    `setuptools.setup` function.

    visit the below for referrence:
    https://setuptools.pypa.io/en/latest/references/keywords.html
    """

    # Project specifics.
    name:             OptionalStr           = None
    download_url:     OptionalStr           = None
    entry_points:     OptionalMap[str, str] = None
    install_requires: OptionalList[str]     = None
    url:              OptionalStr           = None
    python_requires:  OptionalStr           = None

    # Author and other Personnel.
    author:           OptionalStr = None
    author_email:     OptionalStr = None
    maintainer:       OptionalStr = None
    maintainer_email: OptionalStr = None

    # Description and description meta.
    description:                   OptionalStr = None
    long_description:              OptionalStr = None
    long_description_content_type: str         = "text/markdown"

    # Build
    version:              OptionalStr                       = None
    scripts:              OptionalList[str]                 = None
    packages:             OptionalList[str]                 = None
    package_dir:          Directories                       = None
    package_data:         OptionalMap[str, list[str]]       = None
    py_modules:           OptionalList[str]                 = None
    ext_package:          OptionalStr                       = None
    ext_modules:          OptionalList[str]                 = None
    extras_require:       OptionalMap[str, str | list[str]] = None
    include_package_data: bool                              = True
    exclude_package_data: OptionalMap[str, list[str]]       = None
    namespace_packages:   OptionalList[str]                 = None

    # Build Meta
    classifiers: OptionalList[str] = None
    distclass:   OptionalDist      = None
    script_name: OptionalStr       = None
    script_args: OptionalList[str] = None
    options:     SetupOptions      = None
    platforms:   OptionalList[str] = None
    keywords:    OptionalList[str] = None
    cmdclass:    CommandOptions    = None
    zip_safe:    bool              = True

    # Licensing
    license:       OptionalStr       = None
    license_files: OptionalList[str] = None


# Objects which contain distribution metadata
# will be marked with this `ConfigDict` annotation.
ConfigDict = dict[str, Any]

SETUP_MANIFEST: ConfigDict  = {}
SETUP_BUILD:    ConfigBuild


@runtime_checkable
class DataLoader(Protocol):

    @staticmethod
    def __call__(stream: IO, data: Iterable) -> Iterable:
        """Load data from a list of `IO` objects."""


def data_loader(func: Callable) -> DataLoader:
    """Mark some function as a `DataLoader`."""
    assert isinstance(func, DataLoader)
    return func


@data_loader
def yaml_loader(stream: IO, data: dict[str, Any]):
    data.update(yaml.load(stream, yaml.FullLoader))
    return data


@data_loader
def read_loader(stream: IO, data: list[str]):
    data.extend(stream.readlines())
    return data


def read_file_data(data: Iterable, files: list[IO], data_loader: DataLoader):
    """
    Given a list of `IO` objects, read and
    parse from these streams according to
    their respective `DataLoader` factory.
    """
    for file in files:
        data = data_loader(file, data)
    return data


def attempt_open_file(loc: str | PathLike, mode: str = None):
    """
    Safely attempt to open a file in the
    desired mode. If the file is not found,
    return a `StringIO` object.
    """
    try:
        return open(loc, mode or "r")
    except FileNotFoundError:
        return StringIO()


def safe_enter_context(loc: str | PathLike, stack: ExitStack, *,
    mode: str = None):
    """
    Enter the context an `IO` object safely
    handle gracefully a `FileNotFoundError`.
    """
    return stack.enter_context(
        attempt_open_file(loc, mode))


def read_build_file():
    with contextlib.ExitStack() as es:
        files = [
            safe_enter_context(loc, es) for loc in BUILD_FILES]
        data = read_file_data({}, files, yaml_loader)
    return data


def read_requirements_file():
    with contextlib.ExitStack() as es:
        files = [es.enter_context(open(REQUIREMENTS_FILE))]
        data = read_file_data([], files, read_loader)
    return "\n".join(set(data))


def install():
    global SETUP_MANIFEST
    global SETUP_BUILD

    manifest = read_build_file()
    SETUP_MANIFEST |= manifest["project"]

    SETUP_BUILD |= manifest["project_build"]
    SETUP_BUILD["install_requires"] = read_requirements_file()
    SETUP_BUILD["packages"] = find_packages()

    SETUP_MANIFEST |= SETUP_BUILD

    setup(**SETUP_MANIFEST)


if __name__ == "__main__":
    install()
