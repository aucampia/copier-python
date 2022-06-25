import logging

from pytest_cookies.plugin import Cookies, Result


def test_bake_project(cookies: Cookies) -> None:
    result: Result = cookies.bake(extra_context={"project_name": "something.nice"})
    logging.info("result = %s", result)
    assert result.exit_code == 0
    assert result.exception is None
