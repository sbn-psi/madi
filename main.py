#!/usr/bin/env python3
import sys

import pds4
import validator
import localclient
from typing import Iterable
from pds4 import LidVid


def main():
    previous_bundle_directory = sys.argv[1]
    new_bundle_directory = sys.argv[2]

    check_ready(previous_bundle_directory, new_bundle_directory)


def check_ready(previous_bundle_directory, new_bundle_directory):
    previous_bundles, previous_collections, previous_products = load_local_bundle(previous_bundle_directory)
    for bundle in previous_bundles:
        print(bundle.label.checksum)

    new_bundles, new_collections, new_products = load_local_bundle(new_bundle_directory)
    for bundle in new_bundles:
        print(bundle.label.checksum)

    check_bundle_against_previous(previous_bundles[0], new_bundles[0])
    check_bundle_against_collections(new_bundles[0], new_collections)

    for new_collection in new_collections:
        new_collection_lid = LidVid.parse(new_collection.label.identification_area.lidvid).lid
        previous_collections = [x for x in previous_collections if x.label.identification_area.lidvid.lid == new_collection_lid]
        if previous_collections:
            previous_collection = previous_collections[0]
            check_collection_against_previous(previous_collection, new_collection)


def check_bundle_against_previous(previous_bundle: pds4.BundleProduct, new_bundle: pds4.BundleProduct):
    validator.check_bundle_increment(previous_bundle.label, new_bundle.label)


def check_bundle_against_collections(bundle: pds4.BundleProduct, collections: Iterable[pds4.CollectionProduct]):
    collection_lidvids = [x.label.identification_area.lidvid for x in collections]
    validator.check_bundle_for_latest_collections(bundle.label, set(collection_lidvids))


def check_collection_against_previous(previous_collection: pds4.CollectionProduct, new_collection: pds4.CollectionProduct):
    validator.check_for_modification_history(previous_collection.label)
    validator.check_for_modification_history(new_collection.label)
    validator.check_for_preserved_modification_history(previous_collection.label, new_collection.label)
    validator.check_collection_increment(previous_collection.inventory, new_collection.inventory)
    validator.check_collection_duplicates(previous_collection.inventory, new_collection.inventory)


def load_local_bundle(path: str):
    filepaths = localclient.get_file_paths(path)
    label_paths = [x for x in filepaths if x.endswith(".xml")]

    collections = [localclient.fetchcollection(path) for path in label_paths if is_collection(path)]
    bundles = [localclient.fetchbundle(path) for path in label_paths if is_bundle(path)]
    products = [localclient.fetchproduct(path) for path in label_paths if is_basic(path)]

    if len(bundles) == 0:
        raise Exception(f"Could not find bundle product in: {path}")
    return bundles, collections, products


def is_basic(x: str):
    return not (is_collection(x) or is_bundle(x))


def is_collection(x: str):
    return "collection" in x


def is_bundle(x: str):
    return "bundle" in x


if __name__ == "__main__":
    sys.exit(main())
