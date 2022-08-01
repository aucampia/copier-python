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
from pathlib import Path
from typing import List

# https://cookiecutter.readthedocs.io/en/latest/advanced/hooks.html

logger = logging.getLogger(
    __name__ if __name__ != "__main__" else "hooks.post_gen_project"
)

SCRIPT_PATH = Path(__file__)

# {% endraw %}
COOKIECUTTER_JSON = """{{ cookiecutter | tojson('  ') }}"""
# {% raw %}
COOKIECUTTER = json.loads(COOKIECUTTER_JSON)
assert isinstance(COOKIECUTTER, dict)


SCRIPT_PATH = Path(__file__)
COOKIE_PATH = SCRIPT_PATH.parent.parent


class Variants(enum.Enum):
    BASIC = "basic"
    MINIMAL = "minimal"


def apply() -> None:
    logger.info("entry: ...")
    logger.debug("os.getcwd() = %s", os.getcwd())
    logger.debug("SCRIPT_PATH = %s", SCRIPT_PATH.absolute())
    logger.debug("COOKIE_PATH = %s", COOKIE_PATH.absolute())
    logger.debug("cookiecutter_json = %s", COOKIECUTTER_JSON)

    cwd_path = Path.cwd()

    namespace_parts: List[str] = COOKIECUTTER["python_package_fqname"].split(".")
    variant = Variants(COOKIECUTTER["variant"])
    pkg_files_path = cwd_path.joinpath("pkg_files", variant.value)

    logger.debug("namespace_parts = %s", namespace_parts)
    namespace_path = cwd_path.joinpath("src", *namespace_parts)
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
    logger.debug("will rmtree pkg_files_path %s", pkg_files_path)
    shutil.rmtree(pkg_files_path)

    cookiecutter_input_path = cwd_path.joinpath("cookiecutter-input.yaml")
    if not cookiecutter_input_path.exists():
        try:
            import yaml

            logger.info("Writing cookiecutter input to %s", cookiecutter_input_path)
            with open(cwd_path.joinpath("cookiecutter-input.yaml"), "w") as file_object:
                data = {"default_context": COOKIECUTTER.copy()}
                for key in ("_template", "_output_dir"):
                    if key in data["default_context"]:
                        del data["default_context"][key]
                yaml.safe_dump(data, file_object)
        except ImportError:
            logger.warning(
                "no yaml, %s will not be written - install pyyaml to fix",
                cookiecutter_input_path,
            )
    else:
        logger.info("Not writing %s as it already exists", cookiecutter_input_path)

    init_git = COOKIECUTTER.get("init_git", "n") == "y"
    if init_git:
        subprocess.run(["git", "init"])


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
