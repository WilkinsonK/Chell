# Handle traceback here
import inspect

from types import CodeType, FrameType, TracebackType


FRAME_OVERFLOW = "\t..."

NEWLINE = "\n"

TAB_SIZE = 4
TAB      = " " * TAB_SIZE

LINENO  = "\033[35m%s\033[0m"
ERRLINE = "%s \033[31m<<]\033[0m"


def indent_line(line: str, tab_count: int = None):
    tab_count = tab_count or 1
    return (TAB * tab_count) + line


def indent_lines(lines: list[str], *, predicate = None, tab_count: int = None):
    predicate = predicate or (lambda l: True)
    tab_count = tab_count or 1

    for ind, line in enumerate(lines):
        if not predicate(line):
            continue
        lines[ind] = indent_line(line, tab_count)
    
    return lines


class TracebackRender:
    __slots__ = ("__rendered", "__last_tb", "__error")

    __rendered: list[str]
    __last_tb:  TracebackType | None
    __error:    Exception

    def __init__(self) -> None:
        self.__rendered = []
        self.__last_tb  = None

    def __str__(self):
        return self.message

    @property
    def last(self):
        return self.__last_tb

    @last.setter
    def last(self, tb: TracebackType):
        self.__last_tb = tb

    @property
    def message(self):
        message = [
            NEWLINE.join(self.__rendered[::-1])
        ]

        tb_locals = self.__last_tb.tb_frame.f_locals
        message.extend(["locals:"] + indent_lines([
            f"{name}: {value}" for name,value in tb_locals.items()
        ]))
        return NEWLINE.join(message)

    @property
    def error(self):
        return self.__error

    @error.setter
    def error(self, error: Exception):
        self.__error = error


def render_tb(exc: Exception, tb: TracebackType):
    """
    Analyze a stack trace, returning a rendered string
    to output to the shell.
    """
    render = TracebackRender()
    render.error = exc

    def inner(tb: TracebackType):
        if tb.tb_next:
            inner(tb.tb_next)
        else:
            render.last = tb
        render_tb_frame(tb, render=render)

    inner(tb)
    return render


def render_tb_frame(tb: TracebackType, *, render: TracebackRender):
    """
    Render a single frame to display relevant
    traceback information. i.e. where at what line
    an error was traced in the frame.
    """
    frame   = tb.tb_frame
    co_code = frame.f_code

    frame_render = [
        f"from {co_code.co_filename}",
    ]

    frame_render.append(indent_line(
        f"in {co_code.co_name!r} @ line {frame.f_lineno}:"))
    frame_render.append(
        render_tb_source(frame, co_code))

    render.__rendered.append("\n".join(frame_render))


def render_tb_source(frame: FrameType, co_code: CodeType):
    linestart = co_code.co_firstlineno
    linestop  = frame.f_lineno - linestart

    source = inspect.getsource(co_code).split(NEWLINE)[:linestop + 1]
    source = indent_lines([
        FRAME_OVERFLOW,
        *source,
        FRAME_OVERFLOW], tab_count=1)

    for ind, line in enumerate(source):
        lineno = (linestart + ind - 1)
        if lineno == frame.f_lineno:
            line = ERRLINE % line
        linestr = LINENO % str(lineno).rjust(3, "0")
        source[ind] = f"|{linestr} {line}"

    return NEWLINE.join(source)
