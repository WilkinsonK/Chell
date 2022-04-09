"""
Project distribution setup file.

Expected to run as setup.py, this module
tries to load dist information from a manifest
file, then execute the loaded values in the `setup`
call. (see `install` function defined in this
module.)
"""

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
REQUIREMENTS_FILES: tuple[Path, ...] = (
    PROJECT_ROOT.parents[1] / "requirements.txt",
)


@dataclasses.dataclass
class ConfigBuild:
    """
    Representational Parameter Object.
    used to identify keyword values for
    `setuptools.setup` function.

    NOTE: not all params are implemented
    in this class. Either due to deprecation
    or does not fit the potential scope
    of this project's needs.

    visit the below for referrence:
    https://setuptools.pypa.io/en/latest/references/keywords.html
    """

    # Project specifics.
    name:             OptionalStr           = None
    download_url:     OptionalStr           = None
    entry_points:     OptionalMap[str, str] = None
    install_requires: OptionalList[str]     = None
    url:              OptionalStr           = None
    project_urls:     OptionalList[str]     = None
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

    def copy(self):
        """Return a shallow copy of this `ConfigBuild`"""
        cls, temp = type(self), dataclasses.asdict(self)
        return cls(**temp)


# Objects which contain distribution metadata
# will be marked with this `ConfigDict` annotation.
ConfigDict = dict[str, Any]

SETUP_MANIFEST: ConfigDict  = {}
SETUP_BUILD:    ConfigBuild

# Manifest keys are expected sections of
# the build file. These values should
# correspond with the notation given to
# our `ConfigBuild` class.
SETUP_MANIFEST_KEYS = (
    "project",
    "personnel",
    "description",
    "build",
    "build-meta",
    "licensing"
)

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
    loaded = yaml.load(stream, yaml.FullLoader)
    if loaded:
        data.update(loaded)
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


def safe_open_files(stack: ExitStack, locations: Iterable[str | PathLike]):
    """
    Given an iterable of pathlike files,
    open each file in the `ExitStack`.
    """
    files = []
    for loc in locations:
        files.append(safe_enter_context(loc, stack))
    return files


def load_build_manifest() -> dict[str, Any]:
    """
    Load data for for the build manifest
    from the target files.
    """
    with contextlib.ExitStack() as es:
        files = safe_open_files(es, BUILD_FILES)
        data  = read_file_data({}, files, yaml_loader)
    return data


def load_requirements() -> set[str]:
    """
    Load the project requirements data from
    the target files.
    """
    with contextlib.ExitStack() as es:
        files = safe_open_files(es, REQUIREMENTS_FILES)
        data = read_file_data([], files, read_loader)
    return set(data)


def load_build_from_manifest():
    global SETUP_MANIFEST
    global SETUP_BUILD

    SETUP_MANIFEST = load_build_manifest()

    build_params = {}
    for section in SETUP_MANIFEST_KEYS:
        if not SETUP_MANIFEST[section]:
            continue
        build_params |= SETUP_MANIFEST[section]

    SETUP_BUILD = ConfigBuild(**build_params)


def parse_build():
    global SETUP_BUILD

    # Use shallow copy to refrain from
    # corrupting previously loaded data.
    setup_build = SETUP_BUILD.copy()

    # Merge all requirements
    install_requires = load_requirements()
    if setup_build.install_requires:
        for required in setup_build.install_requires:
            install_requires.add(required)
    setup_build.install_requires = list(install_requires)

    # Ensure packages are obtained and utilized
    packages = set(find_packages())
    if setup_build.packages:
        for package in setup_build.packages:
            packages.add(package)
    setup_build.packages = list(packages)

    # Remove any keys unused in manifest
    build  = dataclasses.asdict(SETUP_BUILD)
    unused = [k for k in build if not build[k]]
    for key in unused:
        build.pop(key)
    return build


def install():
    load_build_from_manifest()
    setup(**parse_build())


if __name__ == "__main__":
    install()
