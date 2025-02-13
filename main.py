#!/usr/bin/env python3
import itertools
import operator
import sys
import argparse

import bundleloader
import localclient
from ready import check_ready,report_errors

import logging

from superseder import supersede
from validator import ValidationError

logger = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("previous_bundle_directory", type=str)
    parser.add_argument("delta_bundle_directory", type=str)
    parser.add_argument("-j", "--jaxa", action="store_true")
    parser.add_argument("-s", "--supersede", type=str)
    parser.add_argument("-d", "--debug", action="store_true")
    parser.add_argument("-l", "--logfile", type=str)
    parser.add_argument("-D", "--dry", action="store_true")

    args = parser.parse_args()

    logging.basicConfig(
        filename=args.logfile,
        format='%(asctime)s;%(levelname)s;%(name)s; %(message)s',
        level=logging.DEBUG if args.debug else logging.INFO)
    logger.info(f'Previous Bundle Directory: {args.previous_bundle_directory}')
    logger.info(f'Delta Bundle Directory: {args.delta_bundle_directory}')
    if args.supersede:
        logger.info(f'Merged Bundle Directory: {args.supersede}')

    previous_fullbundle = bundleloader.load_local_bundle(args.previous_bundle_directory)
    delta_fullbundle = bundleloader.load_local_bundle(args.delta_bundle_directory)

    issues = check_ready(previous_fullbundle, delta_fullbundle, args.jaxa)
    errors = [x for x in issues if x.severity == "error"]
    if not len(errors) and args.supersede:
        supersede(previous_fullbundle, delta_fullbundle, args.supersede, args.dry, args.jaxa)

    report_errors(issues, previous_fullbundle.path, delta_fullbundle.path)


if __name__ == "__main__":
    sys.exit(main())
