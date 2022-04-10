import enum
import typing

from typing import Any, Protocol


class InputCaller(Protocol):
    """Retrieves input from the user via stdin."""

    @typing.overload
    @staticmethod
    def __call__(prompt: object, /) -> str:
        ...

    @typing.overload
    @staticmethod
    def __call__(prompt: object, *args, **kwargs) -> str:
        ...


class OutputCaller(Protocol):
    """Sends output to the user via stdout."""

    @typing.overload
    @staticmethod
    def __call__(*values: object) -> None:
        ...

    @typing.overload
    @staticmethod
    def __call__(*values: object, **kwds: Any) -> None:
        ...


class InputTokens(str, enum.Enum):
    """Basic tokens for parsing inputs."""
    UNKNOWN = "unknown"
    EXIT    = "exit"


SHELL_PROMPT1 = "\033[35m%\033[0m {prompt}"
SHELL_PROMPT2 = "\033[35m...\033[0m {prompt}"


def shellin(prompt: str, input_caller: InputCaller = None):
    """Retrieve input from the user."""
    caller = input_caller or input
    prompt = SHELL_PROMPT1.format(prompt=prompt)

    response = caller(prompt)
    try:
        return InputTokens(response), response
    except ValueError:
        return InputTokens("unknown"), response


def shellout(*values: str, output_caller: OutputCaller = None, **kwds):
    """Send output to the user."""
    caller = output_caller or print
    caller(*values, **kwds)


def main_shell_loop():
    token, response = InputTokens("unknown"), None
    while token is not InputTokens.EXIT:
        token, response = shellin("")


if __name__ == "__main__":
    exit(main_shell_loop())
