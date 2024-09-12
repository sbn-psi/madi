#!/usr/bin/env python3
import os.path
import sys

import validator
import webclient
from pds4 import LidVid


def main():
    previous_bundle_directory = "http://localhost:8000/orex.tagcams_v1.0/"
    new_bundle_directory = "http://localhost:8000/orex.tagcams_v2.0/"

    previous_bundles, previous_collections, previous_products = load_remote_bundle(previous_bundle_directory)
    for bundle in previous_bundles:
        print(webclient.remote_checksum(bundle.url))
        print(bundle.label.checksum)

    new_bundles, new_collections, new_products = load_remote_bundle(new_bundle_directory)
    for bundle in new_bundles:
        print(webclient.remote_checksum(bundle.url))
        print(bundle.label.checksum)

    check_bundle_against_previous(previous_bundles[0], new_bundles[0])
    check_bundle_against_collections(new_bundles[0], new_collections)

    for new_collection in new_collections:
        new_collection_lid = LidVid.parse(new_collection.label.identification_area.lidvid).lid
        previous_collections = [x for x in previous_collections if LidVid.parse(x.label.identification_area.lidvid).lid == new_collection_lid]
        if previous_collections:
            previous_collection = previous_collections[0]
            check_collection_against_previous(previous_collection, new_collection)


def check_bundle_against_previous(previous_bundle, new_bundle):
    validator.check_bundle_increment(previous_bundle.label, new_bundle.label)


def check_bundle_against_collections(bundle, collections):
    collection_lidvids = [LidVid.parse(x.label.identification_area.lidvid) for x in collections]
    validator.check_bundle_for_latest_collections(bundle.label, set(collection_lidvids))


def check_collection_against_previous(previous_collection, new_collection):
    validator.check_for_modification_history(previous_collection.label)
    validator.check_for_modification_history(new_collection.label)
    validator.check_for_preserved_modification_history(previous_collection.label, new_collection.label)
    validator.check_collection_increment(previous_collection.inventory, new_collection.inventory)
    validator.check_collection_duplicates(previous_collection.inventory, new_collection.inventory)


def load_remote_bundle(url):
    root = webclient.fetchdir(url)
    label_urls = [x for x in root.flat_files() if x.endswith(".xml")]
    product_urls = [x for x in label_urls if is_basic(x)]
    bundle_urls = [x for x in label_urls if is_bundle(x)]
    collection_urls = [x for x in label_urls if is_collection(x)]

    collections = [webclient.fetchcollection(url) for url in collection_urls]
    bundles = [webclient.fetchbundle(url) for url in bundle_urls]
    products = [webclient.fetchproduct(url) for url in product_urls]

    return bundles, collections, products


def is_basic(x):
    return not (is_collection(x) or is_bundle(x))


def is_collection(x):
    return "collection" in x


def is_bundle(x):
    return "bundle" in x


if __name__ == "__main__":
    sys.exit(main())
