from __future__ import annotations

import argparse
import distutils.dir_util
import enum
import itertools
import json
import logging
import os
import os.path
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Set

import yaml

logger = logging.getLogger(
    __name__ if __name__ != "__main__" else "hooks.post_gen_project"
)

SCRIPT_PATH = Path(__file__)
TEMPLATE_PATH = SCRIPT_PATH.parent.parent


class Variant(str, enum.Enum):
    BASIC = "basic"
    MINIMAL = "minimal"
    MINIMAL_TYPER = "minimal_typer"


class BuildTool(str, enum.Enum):
    GNU_MAKE = "gnu-make"
    GO_TASK = "go-task"
    POE = "poe"


build_tool_files = {
    BuildTool.GNU_MAKE: {"Makefile"},
    BuildTool.GO_TASK: {"Taskfile.yml"},
}


@dataclass
class CopierAnswers:
    python_package_fqname: str
    variant: Variant
    build_tool: BuildTool
    git_init: bool
    git_commit: bool

    def __post_init__(self) -> None:
        self.namespace_parts = self.python_package_fqname.split(".")

    @classmethod
    def from_mapping(cls, values: Mapping[str, Any]) -> CopierAnswers:
        return cls(
            python_package_fqname=values["python_package_fqname"],
            variant=Variant(values["variant"]),
            build_tool=BuildTool(values["build_tool"]),
            git_init=values["git_init"],
            git_commit=values["git_commit"],
        )


def apply(copier_conf_json: str) -> None:
    logger.info("entry: os.cwd() = %s", os.getcwd())
    logger.debug("SCRIPT_PATH = %s", SCRIPT_PATH.absolute())
    logger.debug("TEMPLATE_PATH = %s", TEMPLATE_PATH.absolute())
    logger.debug("copier_conf_json = %s", copier_conf_json)

    copier_conf = json.loads(copier_conf_json)
    logger.debug("copier_conf = %s", copier_conf)
    assert isinstance(copier_conf, dict)
    copier_answers_file = Path(copier_conf["answers_file"])
    logger.debug("copier_answers_file = %s", copier_answers_file)
    with copier_answers_file.open("r") as io:
        copier_answers = yaml.safe_load(io)
    logger.debug("copier_answers = %s", copier_answers)
    assert isinstance(copier_answers, dict)

    copier_answers = CopierAnswers.from_mapping(copier_answers)

    cwd_path = Path.cwd()

    pkg_files_path = cwd_path.joinpath("pkg_files", copier_answers.variant.value)

    logger.debug("namespace_parts = %s", copier_answers.namespace_parts)
    namespace_path = cwd_path.joinpath("src", *copier_answers.namespace_parts)
    logger.debug("will make namespace_path.parent %s", namespace_path.parent)
    namespace_path.parent.mkdir(parents=True, exist_ok=True)
    logger.debug("will make namespace_path %s", namespace_path)
    namespace_path.mkdir(parents=True, exist_ok=True)
    logger.debug(
        "will copytree pkg_files_path %s to namespace_path %s",
        pkg_files_path,
        namespace_path,
    )
    distutils.dir_util.copy_tree(
        str(pkg_files_path),
        str(namespace_path),
        preserve_mode=0,
        preserve_times=0,
        preserve_symlinks=1,
        update=1,
        verbose=1,
    )
    logger.debug("will rmtree pkg_files_path %s", pkg_files_path.parent)
    shutil.rmtree(pkg_files_path.parent)

    remove_files: Set[str] = set(itertools.chain(*build_tool_files.values()))
    remove_files -= build_tool_files.get(copier_answers.build_tool, set())
    logger.info("removing unused build files %s", remove_files)
    for remove_file in remove_files:
        logger.info("removing unused build file %s", remove_file)
        (cwd_path / remove_file).unlink()

    if copier_answers.git_init:
        subprocess.run(["git", "init"])
        if copier_answers.git_commit:
            subprocess.run(["git", "add", "."])
            subprocess.run(["git", "commit", "-m", "baseline"])


def main() -> None:
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument(
        "--copier-conf",
        action="store",
        type=str,
        dest="copier_conf",
        help="the copier config as a JSON object",
        required=True,
    )
    parse_result = parser.parse_args(sys.argv[1:])
    logging.basicConfig(
        level=os.environ.get("PYLOGGING_LEVEL", logging.INFO),
        stream=sys.stderr,
        datefmt="%Y-%m-%dT%H:%M:%S",
        format=(
            "%(asctime)s.%(msecs)03d %(process)d %(thread)d %(levelno)03d:%(levelname)-8s "
            "%(name)-12s %(module)s:%(lineno)s:%(funcName)s %(message)s"
        ),
    )
    apply(parse_result.copier_conf)


if __name__ == "__main__":
    main()
