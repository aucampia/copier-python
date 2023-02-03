from __future__ import annotations

# {% raw %}
import distutils.dir_util
import enum
import json
import logging
import os
import os.path
import shutil
import subprocess
import sys
import urllib.parse
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

import yaml

# https://cookiecutter.readthedocs.io/en/latest/advanced/hooks.html

logger = logging.getLogger(
    __name__ if __name__ != "__main__" else "hooks.post_gen_project"
)

SCRIPT_PATH = Path(__file__)

# {% endraw %}
COPIER_ANSWERS_FILE = """{{ _copier_conf.answers_file }}"""
# {% raw %}
COPIER_ANSWERS_YAML_PATH = Path(COPIER_ANSWERS_FILE)
with COPIER_ANSWERS_YAML_PATH.open("r") as io:
    COPIER_ANSWERS = yaml.safe_load(io)
assert isinstance(COPIER_ANSWERS, dict)


SCRIPT_PATH = Path(__file__)
TEMPLATE_PATH = SCRIPT_PATH.parent.parent


class Variant(enum.Enum):
    BASIC = "basic"
    MINIMAL = "minimal"


class BuildTool(enum.Enum):
    GNU_MAKE = "gnu-make"
    GO_TASK = "go-task"


build_tool_files = {
    BuildTool.GNU_MAKE: "Makefile",
    BuildTool.GO_TASK: "Taskfile.yml",
}


@dataclass
class CopierAnswers:
    python_package_fqname: str
    variant: Variant
    build_tool: BuildTool
    git_init: bool
    git_commit: bool

    def __post_init__(self) -> None:
        # self.variant = Variants(self.variant)
        # self.build_tool = BuildTool(self.build_tool)
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


def apply() -> None:
    logger.info("entry: ...")
    logger.debug("SCRIPT_PATH = %s", SCRIPT_PATH.absolute())
    logger.debug("TEMPLATE_PATH = %s", TEMPLATE_PATH.absolute())
    logger.debug("COPIER_ANSWERS_FILE = %s", COPIER_ANSWERS_FILE)
    logger.debug("COPIER_ANSWERS = %s", COPIER_ANSWERS)

    copier_answers = CopierAnswers.from_mapping(COPIER_ANSWERS)

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

    remove_files = set(build_tool_files.values()) - {
        build_tool_files[copier_answers.build_tool]
    }
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
    logging.basicConfig(
        level=os.environ.get("PYLOGGING_LEVEL", logging.INFO),
        stream=sys.stderr,
        datefmt="%Y-%m-%dT%H:%M:%S",
        format=(
            "%(asctime)s.%(msecs)03d %(process)d %(thread)d %(levelno)03d:%(levelname)-8s "
            "%(name)-12s %(module)s:%(lineno)s:%(funcName)s %(message)s"
        ),
    )
    apply()


if __name__ == "__main__":
    main()

# {% endraw %}
