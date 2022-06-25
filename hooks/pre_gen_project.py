# {% raw %}

import json
import logging
import os
import os.path
import pathlib
import sys

# https://cookiecutter.readthedocs.io/en/latest/advanced/hooks.html

logger = logging.getLogger(
    __name__ if __name__ != "__main__" else "hooks.pre_gen_project"
)

SCRIPT_PATH = pathlib.Path(__file__)
COOKIE_PATH = SCRIPT_PATH.parent.parent


# {% endraw %}
COOKIECUTTER_JSON = """{{ cookiecutter | tojson('  ') }}"""
# {% raw %}
COOKIECUTTER = json.loads(COOKIECUTTER_JSON)


def apply() -> None:
    logger.info("entry: ...")
    logger.info("os.getcwd() = %s", os.getcwd())
    logger.info("__file__ = %s", __file__)
    logger.info("SCRIPT_PATH = %s", SCRIPT_PATH.absolute())
    logger.info("COOKIE_PATH = %s", COOKIE_PATH.absolute())
    logger.info("cookiecutter_json = %s", COOKIECUTTER_JSON)

    for key, value in os.environ.items():
        logger.info("os.environ[%s] -> %s", key, value)

    # env = jinja2.sandbox.SandboxedEnvironment(keep_trailing_newline=True)

    # license_template_url = COOKIECUTTER.setdefault(
    #     "license_template_url",
    #     (
    #         "https://gitlab.com/aucampia/license-info/raw/master"
    #         "/licenses/{license_code}/template-width_CANON.cc.j2"
    #     ).format(**COOKIECUTTER),
    # )
    # if COOKIECUTTER["license_code"] != "UNLICENSED":
    #     COOKIECUTTER.setdefault(
    #         "license_preamble", "{license_code} License\n\n".format(**COOKIECUTTER)
    #     )
    #     rights = ""
    # else:
    #     COOKIECUTTER.setdefault("license_preamble", "")
    #     rights = " - All rights reserved."

    # COOKIECUTTER.setdefault(
    #     "license_copyright_header",
    #     "Copyright (c) {current_year} {full_name}{rights}".format(
    #         **COOKIECUTTER,
    #         current_year=datetime.datetime.now().strftime("%Y"),
    #         rights=rights,
    #     ),
    # )

    # logger.info("license_template_url = %s", license_template_url)
    # request = urllib.request.Request(license_template_url)
    # with urllib.request.urlopen(request) as url:
    #     license_template_string = url.read().decode("utf-8")

    # logger.info("license_template_string = %s", license_template_string)
    # license_template = env.from_string(license_template_string)

    # with open("LICENSE.txt", "wb+") as file_handle:
    #     file_handle.write(
    #         license_template.render(cookiecutter=COOKIECUTTER).encode("utf-8")
    #     )


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


if __name__ == "__main__":
    main()

# {% endraw %}
