#!/usr/bin/env python3
import sys
from dataclasses import dataclass

import pds4
import validator
import localclient

from typing import Iterable, List
from pds4 import BundleProduct, CollectionProduct, BasicProduct
import argparse
import logging

logger = logging.getLogger(__name__)

@dataclass
class FullBundle:
    bundles: List[BundleProduct]
    superseded_bundles: List[BundleProduct]
    collections: List[CollectionProduct]
    superseded_collections: List[CollectionProduct]
    products: List[BasicProduct]
    superseded_products: List[BasicProduct]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("previous_bundle_directory", type=str)
    parser.add_argument("new_bundle_directory", type=str)
    parser.add_argument("-s", "--supersede", type=str)

    logging.basicConfig(level=logging.INFO)
    args = parser.parse_args()
    logger.info(f'Previous Bundle Directory: {args.previous_bundle_directory}')
    logger.info(f'New Bundle Directory: {args.new_bundle_directory}')
    if args.supersede:
        logger.info(f'Merged Bundle Directory: {args.supersede}')

    check_ready(args.previous_bundle_directory, args.new_bundle_directory)

    if args.supersede:
        supersede(args.previous_bundle_directory, args.new_bundle_directory, args.supersede)


def supersede(previous_bundle_directory, new_bundle_directory, merged_bundle_directory):
    logger.info(f"TODO: Supersede {previous_bundle_directory} with new data from {new_bundle_directory} into {merged_bundle_directory}")
    previous_fullbundle = load_local_bundle(previous_bundle_directory)
    new_fullbundle = load_local_bundle(new_bundle_directory)

    previous_bundles_to_keep, previous_bundles_to_supersede = find_superseded(previous_fullbundle.bundles, new_fullbundle.bundles)

    logger.info(f"Bundles to supersede: {[str(x.label.identification_area.lidvid) for x in previous_bundles_to_supersede]}")
    logger.info(f"Bundles to keep: {[str(x.label.identification_area.lidvid) for x in previous_bundles_to_keep]}")
    logger.info(f"New bundles: {[str(x.label.identification_area.lidvid) for x in new_fullbundle.bundles]}")

    previous_collections_to_keep, previous_collections_to_supersede = find_superseded(previous_fullbundle.collections, new_fullbundle.collections)
    logger.info(f"Collections to supersede: {[str(x.label.identification_area.lidvid) for x in previous_collections_to_supersede]}")
    logger.info(f"Collections to keep: {[str(x.label.identification_area.lidvid) for x in previous_collections_to_keep]}")
    logger.info(f"New collections: {[str(x.label.identification_area.lidvid) for x in new_fullbundle.collections]}")

    previous_products_to_keep, previous_products_to_supersede = find_superseded(previous_fullbundle.products, new_fullbundle.products)
    logger.info(f"Products to supersede: {[str(x.label.identification_area.lidvid) for x in previous_products_to_supersede]}")
    logger.info(f"Products to keep: {[str(x.label.identification_area.lidvid) for x in previous_products_to_keep]}")
    logger.info(f"New bundles: {[str(x.label.identification_area.lidvid) for x in new_fullbundle.products]}")


def find_superseded(previous_products: List[pds4.Pds4Product], new_products: List[pds4.Pds4Product]):
    new_product_lids = set(x.label.identification_area.lidvid.lid for x in new_products)
    previous_products_to_keep = [x for x in previous_products if
                                x.label.identification_area.lidvid.lid not in new_product_lids]
    previous_products_to_supersede = [x for x in previous_products if
                                x.label.identification_area.lidvid.lid in new_product_lids]
    return previous_products_to_keep, previous_products_to_supersede


def check_ready(previous_bundle_directory, new_bundle_directory):
    logger.info(f"Checking readiness of new bundle {new_bundle_directory} against {previous_bundle_directory}")

    previous_fullbundle = load_local_bundle(previous_bundle_directory)
    for bundle in previous_fullbundle.bundles:
        logger.info(f'Previous bundle checksum: {bundle.label.checksum}')

    new_fullbundle = load_local_bundle(new_bundle_directory)
    for bundle in new_fullbundle.bundles:
        logger.info(f'New bundle checksum: {bundle.label.checksum}')

    do_checkready(new_fullbundle, previous_fullbundle)


def do_checkready(new_fullbundle: FullBundle, previous_fullbundle: FullBundle):
    check_bundle_against_previous(previous_fullbundle.bundles[0], new_fullbundle.bundles[0])
    check_bundle_against_collections(new_fullbundle.bundles[0], new_fullbundle.collections)
    for new_collection in new_fullbundle.collections:
        new_collection_lid = new_collection.label.identification_area.lidvid.lid
        previous_collections = [x for x in previous_fullbundle.collections if
                                x.label.identification_area.lidvid.lid == new_collection_lid]
        if previous_collections:
            previous_collection = previous_collections[0]
            check_collection_against_previous(previous_collection, new_collection)


def check_bundle_against_previous(previous_bundle: pds4.BundleProduct, new_bundle: pds4.BundleProduct):
    logger.info(f"Checking new bundle label {new_bundle.label.identification_area.lidvid} against previous bundle label {previous_bundle.label.identification_area.lidvid}")
    validator.check_bundle_increment(previous_bundle.label, new_bundle.label)


def check_bundle_against_collections(bundle: pds4.BundleProduct, collections: Iterable[pds4.CollectionProduct]):
    logger.info(f"Checking bundle label {bundle.label.identification_area.lidvid} against existing collections")
    collection_lidvids = [x.label.identification_area.lidvid for x in collections]
    validator.check_bundle_for_latest_collections(bundle.label, set(collection_lidvids))


def check_collection_against_previous(previous_collection: pds4.CollectionProduct, new_collection: pds4.CollectionProduct):
    logger.info(f"Checking new collection label {new_collection.label.identification_area.lidvid} against previous collection {previous_collection.label.identification_area.lidvid}")
    validator.check_for_modification_history(previous_collection.label)
    validator.check_for_modification_history(new_collection.label)
    validator.check_for_preserved_modification_history(previous_collection.label, new_collection.label)
    validator.check_collection_increment(previous_collection.inventory, new_collection.inventory)
    validator.check_collection_duplicates(previous_collection.inventory, new_collection.inventory)


def load_local_bundle(path: str) -> FullBundle:
    logger.info(f'Loading bundle: {path}')
    filepaths = localclient.get_file_paths(path)
    label_paths = [x for x in filepaths if x.endswith(".xml")]

    collections = [localclient.fetchcollection(path) for path in label_paths if is_collection(path) and not is_superseded(path)]
    bundles = [localclient.fetchbundle(path) for path in label_paths if is_bundle(path) and not is_superseded(path)]
    products = [localclient.fetchproduct(path) for path in label_paths if is_basic(path) and not is_superseded(path)]

    superseded_collections = [localclient.fetchcollection(path) for path in label_paths if is_collection(path) and is_superseded(path)]
    superseded_bundles = [localclient.fetchbundle(path) for path in label_paths if is_bundle(path) and is_superseded(path)]
    superseded_products = [localclient.fetchproduct(path) for path in label_paths if is_basic(path) and is_superseded(path)]

    if len(bundles) == 0:
        raise Exception(f"Could not find bundle product in: {path}")
    return FullBundle(bundles, superseded_bundles, collections, superseded_collections, products, superseded_products)


def is_basic(x: str):
    return not (is_collection(x) or is_bundle(x))


def is_collection(x: str):
    return "collection" in x


def is_bundle(x: str):
    return "bundle" in x


def is_superseded(x: str):
    return "SUPERSEDED" in x


if __name__ == "__main__":
    sys.exit(main())
