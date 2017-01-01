# -*- coding:utf-8 -*-
import sys
import logging
import argparse
from magicalimport import import_symbol


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--driver", default="pyramid_swagger_router.driver:Driver")
    parser.add_argument("--logging", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
    parser.add_argument("file", default=None)
    args = parser.parse_args()

    # todo: option
    logging.basicConfig(
        format="%(levelname)5s:%(name)36s:%(message)s",
        level=logging._nameToLevel[args.logging]
    )

    driver_cls = args.driver
    if ":" not in driver_cls:
        driver_cls = "pyramid_swagger_router.driver:{}".format(driver_cls)
    driver = import_symbol(driver_cls)()

    if args.file is None:
        driver.run(sys.stdin, sys.stdout)
    else:
        with open(args.file) as rf:
            driver.run(rf, sys.stdout)
