from __future__ import annotations

import dataclasses

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

# https://cookiecutter.readthedocs.io/en/latest/advanced/hooks.html

logger = logging.getLogger(
    __name__ if __name__ != "__main__" else "hooks.post_gen_project"
)

SCRIPT_PATH = Path(__file__)

# {% endraw %}
# Using urlencode as jinja2 has no base64 builtin.
COPIER_ANSWERS_JSON_URLENCODED = """{{ _copier_answers | tojson('  ') | urlencode }}"""

# {% raw %}
COPIER_ANSWERS_JSON = urllib.parse.unquote(COPIER_ANSWERS_JSON_URLENCODED)
COPIER_ANSWERS = json.loads(urllib.parse.unquote(COPIER_ANSWERS_JSON))
assert isinstance(COPIER_ANSWERS, dict)


SCRIPT_PATH = Path(__file__)
TEMPLATE_PATH = SCRIPT_PATH.parent.parent


class Variants(enum.Enum):
    BASIC = "basic"
    MINIMAL = "minimal"


class BuildTool(enum.Enum):
    GNU_MAKE = "gnu-make"
    GO_TASK = "go-task"


# class GitAction(enum.Enum):
#     INIT = "init"
#     COMMIT = "commit"

#     @classmethod
#     def from_str(cls, value: Optional[str]) -> Optional[GitAction]:
#         if value is None:
#             return None
#         return cls(value)


build_tool_files = {
    BuildTool.GNU_MAKE: "Makefile",
    BuildTool.GO_TASK: "Taskfile.yml",
}


@dataclass
class CopierAnswers:
    python_package_fqname: str
    variant_str: str
    build_tool_str: str
    git_init: bool
    git_commit: bool

    def __post_init__(self) -> None:
        self.variant = Variants(self.variant_str)
        self.build_tool = BuildTool(self.build_tool_str)
        self.namespace_parts = self.python_package_fqname.split(".")

    @classmethod
    def from_mapping(cls, values: Mapping[str, Any]) -> CopierAnswers:
        field_names = set(f.name for f in dataclasses.fields(cls))
        filtered = dict(
            (key, value) for key, value in values.items() if key in field_names
        )
        return cls(**filtered)


def apply() -> None:
    logger.info("entry: ...")
    logger.debug("files = %s", "\n".join(f"{path}" for path in Path.cwd().glob("**/*")))
    logger.debug("os.getcwd() = %s", os.getcwd())
    logger.debug("SCRIPT_PATH = %s", SCRIPT_PATH.absolute())
    logger.debug("TEMPLATE_PATH = %s", TEMPLATE_PATH.absolute())
    logger.debug("COPIER_ANSWERS_JSON = %s", COPIER_ANSWERS_JSON)
    logger.debug("COPIER_ANSWERS = %s", COPIER_ANSWERS)

    copier_answers = CopierAnswers.from_mapping(COPIER_ANSWERS)

    cwd_path = Path.cwd()

    # namespace_parts: List[str] = COPIER_ANSWERS["python_package_fqname"].split(".")
    # variant = Variants(COPIER_ANSWERS["variant"])
    # build_tool = BuildTool(COPIER_ANSWERS["build_tool"])
    # git_action = GitAction.from_str(COPIER_ANSWERS["git_action"])
    # git_commit = GitAction
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

    # cookiecutter_input_path = cwd_path.joinpath("cookiecutter-input.yaml")
    # if not cookiecutter_input_path.exists():
    #     try:
    #         import yaml

    #         logger.info("Writing cookiecutter input to %s", cookiecutter_input_path)
    #         with open(cwd_path.joinpath("cookiecutter-input.yaml"), "w") as file_object:
    #             data = {"default_context": COOKIECUTTER.copy()}
    #             for key in ("_template", "_output_dir"):
    #                 if key in data["default_context"]:
    #                     del data["default_context"][key]
    #             yaml.safe_dump(data, file_object)
    #     except ImportError:
    #         logger.warning(
    #             "no yaml, %s will not be written - install pyyaml to fix",
    #             cookiecutter_input_path,
    #         )
    # else:
    #     logger.info("Not writing %s as it already exists", cookiecutter_input_path)

    remove_files = set(build_tool_files.values()) - {
        build_tool_files[copier_answers.build_tool]
    }
    logger.info("removing unused build files %s", remove_files)
    for remove_file in remove_files:
        logger.info("removing unused build file %s", remove_file)
        (cwd_path / remove_file).unlink()

    # # too slow, let users run this ...
    # # subprocess.run(["make", "-C", "devtools", "-B"])

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
