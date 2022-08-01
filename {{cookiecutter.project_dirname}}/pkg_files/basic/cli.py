#!/usr/bin/env python3
import logging
import os
import sys
from typing import List, Optional

import structlog
import typer
from structlog.types import Processor

from ._version import __version__

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


if __name__ == "__main__":
    main()
