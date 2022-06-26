from encodings import utf_8, utf_8_sig
import hashlib
import json
import logging
import os
import pickle
import random
import string
import subprocess
from dataclasses import asdict, dataclass, field
from pathlib import Path, PurePath
from tempfile import mkdtemp
import tempfile
from typing import Any, Callable, Dict, List, Mapping, Set, TypeVar

from cookiecutter.generate import generate_context
from cookiecutter.main import cookiecutter
from cookiecutter.prompt import prompt_for_config
from frozendict import frozendict
from libcst import Call
import pytest
from pytest_cookies.plugin import Cookies, Result

# @dataclass
# class OSPath:
#     parts: List[str]

#     @classmethod
#     def from_str(cls, input: str) -> "OSPath":
#         parts = input.split(os.pathsep)
#         return cls(parts)


# def split_os_path(path: str) -> List[str]:
#     return path.split(os.pathsep)


SCRIPT_PATH = Path(__file__)
PROJECT_PATH = SCRIPT_PATH.parent.parent


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
class BakeKey:
    template_path: Path
    template_hash: str
    extra_context: frozendict[str, Any]


@dataclass(frozen=True)
class BakeResult(BakeKey):
    project_path: Path
    context: Dict[str, Any]


AnyT = TypeVar("AnyT")


# class HashableDict(dict[AnyT, AnyT]):
#     def __hash__(self) -> int:
#         return hash(tuple(sorted(self.items())))


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
        # for exclude_subdir in exclude_subdirs:
        #     if exclude_subdir in dirnames:
        #         dirnames.remove(exclude_subdir)
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
    # with file_path.open("rb") as bytes_io:
    #     hasher.update(bytes_io)


def hash_object(
    object: Any, hash: Callable[[], "hashlib._Hash"] = hashlib.sha256
) -> str:
    pickled = pickle.dumps(object)
    hasher = hash()
    hasher.update(pickled)
    return hasher.hexdigest()


ESCAPED_ENV = escape_venv(os.environ)


class Baker:
    def __init__(self) -> None:
        # self._counter = 0
        # self._tmp_path = Path(mkdtemp(prefix=f"Baker-{__name__}-"))
        self._baked: Dict[BakeKey, BakeResult] = {}

    def bake(self, extra_context: Dict[str, Any], template_path: Path) -> BakeResult:
        context_file = template_path / "cookiecutter.json"

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

        key = BakeKey(template_path, template_path_hash, frozendict(extra_context))

        key_hash = hash_object(key)

        # dirkey = "".join(random.choices(string.ascii_uppercase + string.digits, k=8))

        if key in self._baked:
            return self._baked[key]

        output_path = Path(tempfile.gettempdir()) / f"baked-cookie-{key_hash}"
        output_context_path = output_path.parent / f"{output_path.name}-context.json"
        output_project_path = output_path.parent / f"{output_path.name}-project.json"

        if output_path.exists():

            output_context = json.loads(output_context_path.read_text())
            output_project = json.loads(output_project_path.read_text())
            baked = BakeResult(
                template_path,
                template_path_hash,
                frozendict(extra_context),
                Path(output_project),
                output_context,
            )
            return baked

        output_path.mkdir(exist_ok=True, parents=True)

        # Render the context, so that we can store it on the Result
        context: Dict[str, Any] = prompt_for_config(
            generate_context(
                context_file=str(context_file), extra_context=extra_context
            ),
            no_input=True,
        )

        # Run cookiecutter to generate a new project
        project_dir = cookiecutter(
            str(template_path),
            no_input=True,
            extra_context=extra_context,
            output_dir=str(output_path),
            # config_file=str(self._config_file),
        )
        project_path = Path(project_dir)

        output_context_path.write_text(json.dumps(context))
        output_project_path.write_text(json.dumps(str(project_path)))

        baked = BakeResult(
            template_path,
            template_path_hash,
            frozendict(extra_context),
            project_path,
            context,
        )

        subprocess.run(
            cwd=baked.project_path,
            env=ESCAPED_ENV,
            args=[
                "bash",
                "-c",
                """
            set -x
            set -eo pipefail
            env | sort
            task configure
        """,
            ],
        )

        subprocess.run(cwd=baked.project_path, args=["bash", "-xc", "pwd"])
        logging.info("running task validate in %s", baked.project_path)
        subprocess.run(cwd=baked.project_path, args=["task", "validate"])

        return baked


BAKER = Baker()


# def baked() -> None:
#     # Render the context, so that we can store it on the Result
#     context = prompt_for_config(
#         generate_context(context_file=str(context_file), extra_context=extra_context),
#         no_input=True,
#     )

#     # Run cookiecutter to generate a new project
#     project_dir = cookiecutter(
#         template,
#         no_input=True,
#         extra_context=extra_context,
#         output_dir=str(self._new_output_dir()),
#         config_file=str(self._config_file),
#     )


CONTEXTS = [{"project_name": "example.project.name"}]


@pytest.mark.parametrize("context", CONTEXTS)
def test_bake_validates(context: Dict[str, Any]) -> None:
    # @dataclass
    # class ExtraContext:
    #     project_name: str = "example.project.name"

    # extra_context = ExtraContext()
    # logging.info("extra_context = %s", extra_context)
    # result = BAKER.bake(asdict(extra_context), template_path=PROJECT_PATH)
    result = BAKER.bake(context, template_path=PROJECT_PATH)
    logging.info("result = %s", result)
    subprocess.run(cwd=result.project_path, env=ESCAPED_ENV, args=["task", "validate"])

    # result: Result = cookies.bake(extra_context=asdict(extra_context))
    # logging.info("result = %s", result)
    # assert result.exit_code == 0
    # assert result.exception is None

    # assert result.project_path.name == extra_context.project_name
    # assert result.project_path.is_dir()

    # logging.info("running poetry install in %s", result.output_path)

    # env = escape_venv(os.environ)

    # env = {**os.environ}
    # virtual_env_path = Path(env["VIRTUAL_ENV"])
    # del env["VIRTUAL_ENV"]
    # ospath_parts = split_os_path(env["PATH"])
    # use_ospath_parts = []
    # for ospath_part in ospath_parts:
    #     ospath_part_path = Path(ospath_part)
    #     if not ospath_part_path.is_relative_to(virtual_env_path):
    #         use_ospath_parts.append(ospath_part)
    # use_ospath = os.pathsep.join(use_ospath_parts)
    # logging.info("use_ospath = %s", use_ospath)
    # env["PATH"] = use_ospath

    # subprocess.run(
    #     cwd=result.output_path,
    #     env=env,
    #     args=[
    #         "bash",
    #         "-c",
    #         """
    #     set -x
    #     set -eo pipefail
    #     env | sort
    #     # ls -ald
    #     # pwd
    #     # which python
    #     # python --version
    #     # python -m poetry --version
    #     task configure
    #     # find .
    #     task validate
    # """,
    #     ],
    # )

    # subprocess.run(cwd=result.project_path, args=["bash", "-xc", "pwd"])
    # logging.info("running task validate in %s", result.project_path)
    # subprocess.run(cwd=result.project_path, args=["task", "validate"])
