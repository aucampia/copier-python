# {% raw %}

import distutils.dir_util
import json
import logging
import os
import os.path
import shutil
import sys
from pathlib import Path
from typing import List


# https://cookiecutter.readthedocs.io/en/latest/advanced/hooks.html

# logging.basicConfig(
#     level=os.environ.get("PYLOGGING_LEVEL", logging.INFO),
#     stream=sys.stderr,
#     datefmt="%Y-%m-%dT%H:%M:%S",
#     format=(
#         "%(asctime)s.%(msecs)03d %(process)d %(thread)d %(levelno)03d:%(levelname)-8s "
#         "%(name)-12s %(module)s:%(lineno)s:%(funcName)s %(message)s"
#     ),
# )

logger = logging.getLogger(
    __name__ if __name__ != "__main__" else "hooks.post_gen_project"
)

SCRIPT_PATH = Path(__file__)

# {% endraw %}
COOKIECUTTER_JSON = """{{ cookiecutter | tojson('  ') }}"""
# {% raw %}
COOKIECUTTER = json.loads(COOKIECUTTER_JSON)

# namespace_init = '''#!/usr/bin/env python3
# # https://setuptools.readthedocs.io/en/latest/pkg_resources.html#id5
# # https://www.python.org/dev/peps/pep-0420/#namespace-packages-today
# """
# This is a namespace package in line with PEP-0420.
# """

# __path__ = __import__('pkgutil').extend_path(__path__, __name__)
# '''


SCRIPT_PATH = Path(__file__)
COOKIE_PATH = SCRIPT_PATH.parent.parent

def apply() -> None:
    logger.info("entry: ...")
    logger.info("os.getcwd() = %s", os.getcwd())
    logger.info("SCRIPT_PATH = %s", SCRIPT_PATH.absolute())
    logger.info("COOKIE_PATH = %s", COOKIE_PATH.absolute())
    logger.info("cookiecutter_json = %s", COOKIECUTTER_JSON)

    cwd_path = Path.cwd()

    pkg_files_path = cwd_path.joinpath("pkg_files")
    namespace_parts: List[str] = COOKIECUTTER["python_package_fqname"].split(".")
    logger.info("namespace_parts = %s", namespace_parts)
    namespace_path = cwd_path.joinpath("src", *namespace_parts)
    logger.info("will make namespace_path.parent %s", namespace_path.parent)
    namespace_path.parent.mkdir(parents=True, exist_ok=True)
    logger.info("will make namespace_path %s", namespace_path)
    namespace_path.mkdir(parents=True, exist_ok=True)
    logger.info(
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
    logger.info("will rmtree pkg_files_path %s", pkg_files_path)
    shutil.rmtree(pkg_files_path)

    cookiecutter_input_path = cwd_path.joinpath("cookiecutter-input.yaml")
    if not cookiecutter_input_path.exists():
        try:
            import yaml

            logger.info("Writing cookiecutter input to %s", cookiecutter_input_path)
            with open(cwd_path.joinpath("cookiecutter-input.yaml"), "w") as file_object:
                data = {"default_context": COOKIECUTTER.copy()}
                del data["default_context"]["_template"]
                del data["default_context"]["_output_dir"]
                # json.dump(data, file_object, indent=2, sort_keys=True)
                yaml.safe_dump(data, file_object)
                # file_object.write('\n')
        except ImportError:
            logger.warning(
                "no yaml, %s will not be written - install pyyaml to fix",
                cookiecutter_input_path,
            )
    else:
        logger.info("Not writing %s as it already exists", cookiecutter_input_path)

    # for index, _ in enumerate(namespace_parts[0:-1]):
    #     namespace_path = Path("src").joinpath(
    #         *namespace_parts[0 : index + 1], "__init__.py"
    #     )
    #     logger.info("namespace_path = %s", namespace_path)
    #     with open(namespace_path, "wb+") as file_object:
    #         file_object.write(namespace_init.encode("utf-8"))

    # subprocess.run(["versioneer", "install"])
    # subprocess.run(["make", "versioneer"])


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
