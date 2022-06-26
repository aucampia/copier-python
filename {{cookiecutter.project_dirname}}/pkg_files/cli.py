#!/usr/bin/env python3
import logging
import os
import sys
from typing import List, Optional

import typer

from ._version import __version__

# --{% if False %}
BARRIER = 1
# --{% endif %}

# --{% if cookiecutter.use_structlog == "y" %}
import structlog
from structlog.types import Processor

# --{% endif %}

# --{% if False %}
BARRIER = 1
# --{% endif %}


logger = logging.getLogger(__name__)

"""
https://click.palletsprojects.com/en/7.x/api/#parameters
https://click.palletsprojects.com/en/7.x/options/
https://click.palletsprojects.com/en/7.x/arguments/
https://typer.tiangolo.com/
https://typer.tiangolo.com/tutorial/options/
"""


cli = typer.Typer()
cli_sub = typer.Typer()
cli.add_typer(cli_sub, name="sub")


@cli.callback()
def cli_callback(
    ctx: typer.Context, verbosity: int = typer.Option(0, "--verbose", "-v", count=True)
) -> None:
    if verbosity is not None:
        root_logger = logging.getLogger("")
        root_logger.propagate = True
        new_level = (
            root_logger.getEffectiveLevel()
            - (min(1, verbosity)) * 10
            - min(max(0, verbosity - 1), 9) * 1
        )
        root_logger.setLevel(new_level)
    logger.debug(
        "entry: ctx.parent.params = %s, ctx.params = %s",
        ({} if ctx.parent is None else ctx.parent.params),
        ctx.params,
    )
    logger.debug(
        "logging.level = %s, LOGGER.level = %s",
        logging.getLogger("").getEffectiveLevel(),
        logger.getEffectiveLevel(),
    )


@cli.command("version")
def cli_version(ctx: typer.Context) -> None:
    sys.stderr.write(f"{__version__}\n")


@cli_sub.callback()
def cli_sub_callback(ctx: typer.Context) -> None:

    logger.debug(
        "entry: ctx.parent.params = %s, ctx.params = %s",
        ({} if ctx.parent is None else ctx.parent.params),
        ctx.params,
    )


@cli_sub.command("leaf")
def cli_sub_leaf(
    ctx: typer.Context,
    name: Optional[str] = typer.Option("fake", "--name", "-n", help="The name ..."),
    numbers: Optional[List[int]] = typer.Argument(None),
) -> None:

    logger.debug(
        "entry: ctx.parent.params = %s, ctx.params = %s",
        ({} if ctx.parent is None else ctx.parent.params),
        ctx.params,
    )


def main() -> None:
    setup_logging()
    cli()


# --{% if cookiecutter.use_structlog == "y" %}
def setup_logging(console: bool = False) -> None:
    shared_processors: List[Processor] = []
    structlog.configure(
        processors=shared_processors
        + [
            structlog.stdlib.filter_by_level,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    use_console: Optional[bool] = None
    console_env = os.environ.get("STRUCTLOG_CONSOLE")
    if console_env is not None:
        if console_env == "true":
            use_console = True
        elif console_env == "false":
            use_console = False
        else:
            raise ValueError(
                "invalid value for STRUCTLOG_CONSOLE - must be 'true' or 'false'"
            )
    if use_console is None:
        use_console = console

    renderer: Processor
    if use_console:
        renderer = structlog.dev.ConsoleRenderer()
    else:
        renderer = structlog.processors.JSONRenderer()
    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=[structlog.stdlib.ExtraAdder(), *shared_processors],
        keep_stack_info=True,
        processors=[
            structlog.processors.CallsiteParameterAdder(
                {
                    structlog.processors.CallsiteParameter.FUNC_NAME,
                    structlog.processors.CallsiteParameter.FILENAME,
                    structlog.processors.CallsiteParameter.LINENO,
                    structlog.processors.CallsiteParameter.THREAD,
                }
            ),
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )
    log_handler = logging.StreamHandler(stream=sys.stderr)
    log_handler.setFormatter(formatter)
    root_logger = logging.getLogger("")
    root_logger.propagate = True
    root_logger.setLevel(os.environ.get("PYLOGGING_LEVEL", logging.INFO))
    root_logger.addHandler(log_handler)


# --{% else %}
def setup_logging() -> None:
    logging.basicConfig(
        level=os.environ.get("PYLOGGING_LEVEL", logging.INFO),
        stream=sys.stderr,
        datefmt="%Y-%m-%dT%H:%M:%S",
        format=(
            "%(asctime)s.%(msecs)03d %(process)d %(thread)d %(levelno)03d:%(levelname)-8s "
            "%(name)-12s %(module)s:%(lineno)s:%(funcName)s %(message)s"
        ),
    )

    # _BLANK_LOGRECORD = logging.LogRecord("name", 0, "pathname", 0, "msg", tuple(), None)

    # def get_extra(record: logging.LogRecord) -> Dict[str, str]:
    #     extra: Dict[str, str] = {}
    #     for key, value in record.__dict__.items():
    #         if key not in _BLANK_LOGRECORD.__dict__:
    #             extra[key] = value
    #     return extra

    # class ExtraLogFormatter(logging.Formatter):
    #     def format(self, record: logging.LogRecord) -> str:
    #         record.__dict__["extra"] = get_extra(record)
    #         return super().format(record)

    # handler = logging.StreamHandler(sys.stderr)
    # formatter = ExtraLogFormatter(
    #     datefmt="%Y-%m-%dT%H:%M:%S",
    #     fmt=(
    #         "%(asctime)s %(process)d %(thread)x %(levelno)03d:%(levelname)-8s "
    #         "%(name)-12s %(module)s:%(lineno)s:%(funcName)s %(message)s %(extra)s"
    #     ),
    # )
    # handler.setFormatter(formatter)
    # root_logger = logging.getLogger("")
    # root_logger.propagate = True
    # root_logger.setLevel(os.environ.get("PYLOGGING_LEVEL", logging.INFO))
    # root_logger.addHandler(handler)


# --{% endif %}

if __name__ == "__main__":
    main()
