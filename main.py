#!/usr/bin/env python3
import sys
import argparse

import bundleloader
import localclient
from ready import check_ready

import logging

from superseder import supersede

logger = logging.getLogger(__name__)





def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("previous_bundle_directory", type=str)
    parser.add_argument("new_bundle_directory", type=str)
    parser.add_argument("-s", "--supersede", type=str)
    parser.add_argument("-d", "--debug", action="store_true")
    parser.add_argument("-l", "--logfile", type=str)

    args = parser.parse_args()

    logging.basicConfig(filename=args.logfile, level=logging.DEBUG if args.debug else logging.INFO)
    logger.info(f'Previous Bundle Directory: {args.previous_bundle_directory}')
    logger.info(f'New Bundle Directory: {args.new_bundle_directory}')
    if args.supersede:
        logger.info(f'Merged Bundle Directory: {args.supersede}')

    previous_fullbundle = bundleloader.load_local_bundle(args.previous_bundle_directory)
    new_fullbundle = bundleloader.load_local_bundle(args.new_bundle_directory)

    check_ready(previous_fullbundle, new_fullbundle)

    if args.supersede:
        supersede(previous_fullbundle, new_fullbundle, args.supersede)








if __name__ == "__main__":
    sys.exit(main())
