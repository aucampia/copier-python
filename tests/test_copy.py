from __future__ import annotations

import enum
import hashlib
import itertools
import json
import logging
import os
import pickle
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from shutil import rmtree
from typing import Any, Callable, Dict, Generator, Mapping, Set, Tuple, TypeVar

import pytest
import yaml
from _pytest.mark.structures import ParameterSet
from copier import run_copy
from frozendict import frozendict

from _scripts.task_post_generation import BuildTool

SCRIPT_PATH = Path(__file__)
PROJECT_PATH = SCRIPT_PATH.parent.parent
TEST_DATA_PATH = SCRIPT_PATH.parent / "data"


def load_answers(name: str) -> Dict[str, Any]:
    config = yaml.safe_load(
        (TEST_DATA_PATH / "copier-answers" / f"{name}.yaml").read_text()
    )
    # default_context = config["default_context"]
    assert isinstance(config, dict)
    logging.info("name = %s, config = %s", name, config)
    return config


def escape_venv(environ: Mapping[str, str]) -> Dict[str, str]:
    result = {**environ}
    virtual_env_path = Path(result["VIRTUAL_ENV"])
    ospath_parts = result["PATH"].split(os.pathsep)
    use_ospath_parts = []
    for ospath_part in ospath_parts:
        ospath_part_path = Path(ospath_part)
        if not ospath_part_path.is_relative_to(virtual_env_path):
            use_ospath_parts.append(ospath_part)
    use_ospath = os.pathsep.join(use_ospath_parts)
    logging.info("use_ospath = %s", use_ospath)
    result["PATH"] = use_ospath
    del result["VIRTUAL_ENV"]
    return result


@dataclass(frozen=True)
class CopyKey:
    template_path: Path
    template_hash: str
    data: frozendict[str, Any]


@dataclass(frozen=True)
class CopyResult(CopyKey):
    output_path: Path
    answers: Dict[str, Any]
    build_tool: BuildTool


AnyT = TypeVar("AnyT")

TEST_RAPID = json.loads(os.environ.get("TEST_RAPID", "true"))
assert isinstance(TEST_RAPID, bool)


def hash_path(
    root: Path,
    exclude_subdirs: Set[str],
    hash: Callable[[], "hashlib._Hash"] = hashlib.sha256,
) -> str:
    hasher = hash()
    for _dirpath, dirnames, filenames in os.walk(root):
        dirpath = Path(_dirpath)
        logging.info("exclude_subdirs = %s", exclude_subdirs)
        for dirname in list(dirnames):
            relative_dirname = (dirpath / dirname).relative_to(root)
            logging.debug("relative_dirname = %s", relative_dirname)
            if str(relative_dirname) in exclude_subdirs:
                dirnames.remove(dirname)
        dirnames.sort()
        filenames.sort()
        logging.info("dirpath = %s", dirpath)
        logging.info("dirnames = %s", dirnames)
        logging.info("filenames = %s", filenames)
        for dirname in dirnames:
            subdir_path = dirpath / dirname
            hasher.update(str(subdir_path).encode("utf-8"))
        for filename in filenames:
            file_path = dirpath / filename
            hasher.update(str(file_path).encode("utf-8"))
            hasher.update(file_path.read_bytes())

    return hasher.hexdigest()


def hash_object(
    object: Any, hash: Callable[[], "hashlib._Hash"] = hashlib.sha256
) -> str:
    pickled = pickle.dumps(object)
    hasher = hash()
    hasher.update(pickled)
    return hasher.hexdigest()


ESCAPED_ENV = escape_venv(os.environ)


class Copier:
    def __init__(self) -> None:
        self._copied: Dict[CopyKey, CopyResult] = {}

    def copy(self, template_path: Path, data: Dict[str, Any]) -> CopyResult:
        if TEST_RAPID:
            template_path_hash = hash_object(template_path)
        else:
            template_path_hash = hash_path(
                template_path,
                exclude_subdirs={
                    ".mypy_cache",
                    ".pytest_cache",
                    ".venv",
                    ".git",
                    "var",
                    "tests",
                },
            )

        key = CopyKey(template_path, template_path_hash, frozendict(data))

        key_hash = hash_object(key)

        # dirkey = "".join(random.choices(string.ascii_uppercase + string.digits, k=8))

        if key in self._copied:
            return self._copied[key]

        output_path = Path(tempfile.gettempdir()) / f"copied-{key_hash}" / "project"
        output_answers_path = output_path.parent / f"{output_path.name}-answers.json"
        logging.info(
            "output_path = %s, output_answers_path = %s",
            output_path,
            output_answers_path,
        )

        # output_project_path = output_path.parent / f"{output_path.name}-project.json"

        if (
            output_path.exists()
            and (next(output_path.glob("*"), None) is not None)
            and TEST_RAPID
        ):
            answers = json.loads(output_answers_path.read_text())
            build_tool = BuildTool(answers["build_tool"])
            # output_project = json.loads(output_project_path.read_text())
            copied = CopyResult(
                template_path,
                template_path_hash,
                frozendict(data),
                output_path,
                answers,
                build_tool,
            )
            return copied

        output_path.parent.mkdir(exist_ok=True, parents=True)

        rmtree(
            output_path,
            ignore_errors=True,
            onerror=lambda function, path, excinfo: logging.info(
                "rmtree error: function = %s, path = %s, excinfo = %s",
                function,
                path,
                excinfo,
            ),
        )

        run_copy(
            f"{template_path}",
            f"{output_path}",
            data=data,
            defaults=True,
            vcs_ref="HEAD",
        )

        answers_file = output_path / ".copier-answers.yml"
        with answers_file.open("r") as _io:
            answers = yaml.safe_load(_io)
        # project_path = Path(project_dir)

        output_answers_path.write_text(json.dumps(answers))
        # output_project_path.write_text(json.dumps(str(project_path)))
        build_tool = BuildTool(answers["build_tool"])
        copied = CopyResult(
            template_path,
            template_path_hash,
            frozendict(data),
            output_path,
            answers,
            build_tool,
        )

        if copied.build_tool == BuildTool.GNU_MAKE:
            configure_commands = """
make configure
make validate-fix
"""
        elif copied.build_tool == BuildTool.GO_TASK:
            configure_commands = """
task configure
task validate:fix
"""
        elif copied.build_tool == BuildTool.POE:
            configure_commands = """
poetry install
poetry run poe validate:fix
"""
        try:
            subprocess.run(
                cwd=copied.output_path,
                env=ESCAPED_ENV,
                check=True,
                args=[
                    "bash",
                    "-c",
                    f"""
    set -x
    set -eo pipefail
    # env | sort
    {configure_commands}
    """,
                ],
            )
        except Exception:
            rmtree(
                output_path,
                ignore_errors=True,
                onerror=lambda function, path, excinfo: logging.info(
                    "rmtree error: function = %s, path = %s, excinfo = %s",
                    function,
                    path,
                    excinfo,
                ),
            )
            raise
        return copied


COPIER = Copier()


class WorkflowAction(enum.Enum):
    VALIDATE = "validate"
    CLI = "cli"


WORKFLOW_ACTION_FACTORIES: Dict[
    Tuple[WorkflowAction, BuildTool], Callable[[CopyResult], str]
] = {
    (WorkflowAction.VALIDATE, BuildTool.GNU_MAKE): lambda result: "make validate",
    (WorkflowAction.VALIDATE, BuildTool.GO_TASK): lambda result: "task validate",
    (WorkflowAction.VALIDATE, BuildTool.POE): lambda result: "poetry run poe validate",
    (
        WorkflowAction.CLI,
        BuildTool.GNU_MAKE,
    ): lambda result: f'poetry run {result.answers["cli_name"]} -vvvv sub leaf',
    (
        WorkflowAction.CLI,
        BuildTool.GO_TASK,
    ): lambda result: f'task venv:run -- {result.answers["cli_name"]} -vvvv sub leaf',
    (
        WorkflowAction.CLI,
        BuildTool.POE,
    ): lambda result: f'poetry run {result.answers["cli_name"]} -vvvv sub leaf',
}

# def get_command(self, result: CopyResult) -> None:
#     if build_tool == BuildTool.GNU_MAKE:


def make_copied_cmd_cases() -> Generator[ParameterSet, None, None]:
    config_names = {"minimal", "basic", "poe-minimal"}
    for config_name, workflow_action in itertools.product(
        config_names,
        WorkflowAction,
    ):
        data = load_answers(config_name)
        if config_name == "everything":
            data["init_git"] = "y"
        yield pytest.param(data, workflow_action, id=f"{config_name}-{workflow_action}")


@pytest.mark.parametrize(["data", "workflow_action"], make_copied_cmd_cases())
def test_copied_cmd(
    data: Dict[str, Any],
    workflow_action: WorkflowAction,
    tmp_path: Path,
) -> None:
    result = COPIER.copy(template_path=PROJECT_PATH, data=data)
    # result = run_copy(f"{PROJECT_PATH}", f"{tmp_path}", data=data, defaults=True, vcs_ref="HEAD")
    # output_path = tmp_path
    output_path = result.output_path
    logging.info("result = %s, output_path = %s", result, output_path)

    # subprocess.run(
    #     cwd=output_path,
    #     env=ESCAPED_ENV,
    #     check=True,
    #     args=[
    #         "bash",
    #         "-c",
    #         """
    #     set -x
    #     set -eo pipefail
    #     # env | sort
    #     task configure
    #     task validate:fix
    # """,
    #     ],
    # )

    subprocess.run(
        cwd=output_path,
        env=ESCAPED_ENV,
        check=True,
        args=[
            "bash",
            "-c",
            f"""
set -eo pipefail
set -x
{WORKFLOW_ACTION_FACTORIES[(workflow_action, result.build_tool)](result)}
    """,
        ],
    )
