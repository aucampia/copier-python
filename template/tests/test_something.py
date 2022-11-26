import logging


from {{python_package_fqname}} import package_function


def test_something() -> None:
    logging.info("entry: ...")
    assert package_function() == "value"
