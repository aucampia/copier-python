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
from typing import Any, Callable, Dict, Generator, Mapping, Set, TypeVar

import pytest
import yaml
from _pytest.mark.structures import ParameterSet
from copier import run_copy
from frozendict import frozendict

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


AnyT = TypeVar("AnyT")

TEST_RAPID = json.loads(os.environ.get("TEST_RAPID", "false"))
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
            # output_project = json.loads(output_project_path.read_text())
            copied = CopyResult(
                template_path,
                template_path_hash,
                frozendict(data),
                output_path,
                answers,
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

        copied = CopyResult(
            template_path,
            template_path_hash,
            frozendict(data),
            output_path,
            answers,
        )

        subprocess.run(
            cwd=copied.output_path,
            env=ESCAPED_ENV,
            check=True,
            args=[
                "bash",
                "-c",
                """
            set -x
            set -eo pipefail
            # env | sort
            task configure
            task validate:fix
        """,
            ],
        )

        return copied


COPIER = Copier()


def make_copied_cmd_cases() -> Generator[ParameterSet, None, None]:
    config_names = {"minimal", "basic"}
    # config_names = {
    #     "minimal",
    # }
    for config_name, (cmd_name, cmd) in itertools.product(
        config_names,
        [
            (
                "validate",
                lambda result: "task validate",
            ),
            (
                "cli",
                lambda result: f'task venv:run -- {result.answers["cli_name"]} -vvvv sub leaf',
            ),
        ],
    ):
        data = load_answers(config_name)
        if config_name == "everything":
            data["init_git"] = "y"
        yield pytest.param(data, cmd, id=f"{config_name}-{cmd_name}")


@pytest.mark.parametrize(["data", "cmd"], make_copied_cmd_cases())
def test_copied_cmd(
    data: Dict[str, Any],
    cmd: Callable[[CopyResult], str],
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
{cmd(result)}
    """,
        ],
    )
