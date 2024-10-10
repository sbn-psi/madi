#!/usr/bin/env python3
import itertools
import os
import shutil
import sys
from dataclasses import dataclass

import paths
import pds4
import validator
import localclient

from typing import Iterable, List, Tuple
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

    check_ready(args.previous_bundle_directory, args.new_bundle_directory)

    if args.supersede:
        supersede(args.previous_bundle_directory, args.new_bundle_directory, args.supersede)


def supersede(previous_bundle_directory, new_bundle_directory, merged_bundle_directory) -> None:
    logger.info(f"TODO: Supersede {previous_bundle_directory} "
                f"with new data from {new_bundle_directory} into {merged_bundle_directory}")
    previous_fullbundle = load_local_bundle(previous_bundle_directory)
    new_fullbundle = load_local_bundle(new_bundle_directory)

    previous_bundles_to_keep, previous_bundles_to_supersede = find_superseded(previous_fullbundle.bundles,
                                                                              new_fullbundle.bundles)
    report_superseded(previous_bundles_to_keep,
                      previous_bundles_to_supersede,
                      new_fullbundle.bundles,
                      previous_bundle_directory,
                      new_bundle_directory,
                      merged_bundle_directory,
                      "Bundles")

    previous_collections_to_keep, previous_collections_to_supersede = find_superseded(previous_fullbundle.collections,
                                                                                      new_fullbundle.collections)
    report_superseded(previous_collections_to_keep,
                      previous_collections_to_supersede,
                      new_fullbundle.collections,
                      previous_bundle_directory,
                      new_bundle_directory,
                      merged_bundle_directory,
                      "Collections")

    previous_products_to_keep, previous_products_to_supersede = find_superseded(previous_fullbundle.products,
                                                                                new_fullbundle.products)
    report_superseded(previous_products_to_keep,
                      previous_products_to_supersede,
                      new_fullbundle.products,
                      previous_bundle_directory,
                      new_bundle_directory,
                      merged_bundle_directory,
                      "Products")

    do_copy_label(itertools.chain(previous_bundles_to_keep,
                                  previous_collections_to_keep,
                                  previous_products_to_keep,),
                  previous_bundle_directory,
                  merged_bundle_directory)
    do_copy_label(itertools.chain(previous_bundles_to_supersede,
                                  previous_collections_to_supersede,
                                  previous_products_to_supersede),
                  previous_bundle_directory,
                  merged_bundle_directory, superseded=True)

    do_copy_label(itertools.chain(new_fullbundle.collections,
                                  new_fullbundle.bundles,
                                  new_fullbundle.products), new_bundle_directory, merged_bundle_directory)

    do_copy_data(previous_products_to_keep, previous_bundle_directory, merged_bundle_directory)
    do_copy_data(previous_products_to_supersede, previous_bundle_directory, merged_bundle_directory, superseded=True)
    do_copy_data(new_fullbundle.products, new_bundle_directory, merged_bundle_directory)

    copy_unmodified_collections(previous_collections_to_keep, previous_bundle_directory, new_bundle_directory)
    generate_collections(previous_collections_to_supersede,
                         new_fullbundle.collections,
                         previous_bundle_directory,
                         merged_bundle_directory)


def generate_collections(previous_collections_to_supersede: List[pds4.Pds4Product],
                         new_collections: List[pds4.CollectionProduct],
                         previous_bundle_directory,
                         merged_bundle_directory) -> None:
    for previous in previous_collections_to_supersede:
        if isinstance(previous, pds4.CollectionProduct):
            collection_id = previous.label.identification_area.lidvid.lid.collection
            new_collection = [x for x in new_collections
                              if x.label.identification_area.lidvid.lid.collection == collection_id][0]
            inventory = pds4.CollectionInventory()
            inventory.ingest_new_inventory(previous.inventory)
            inventory.ingest_new_inventory(new_collection.inventory)

            inventory_path = paths.relocate_path(previous.inventory_path,
                                                 previous_bundle_directory,
                                                 merged_bundle_directory)
            with open(inventory_path, 'w') as f:
                f.write(inventory.to_csv())


def report_superseded(products_to_keep: List[pds4.Pds4Product],
                      products_to_supersede: List[pds4.Pds4Product],
                      new_products: List[pds4.Pds4Product],
                      previous_bundle_dir,
                      new_bundle_dir,
                      merged_bundle_dir,
                      label: str = "Products") -> None:
    logger.info(f"{label} to supersede: {[str(x.label.identification_area.lidvid) for x in products_to_supersede]}")
    report_new_paths(products_to_supersede, previous_bundle_dir, merged_bundle_dir, True)
    logger.info(f"{label} to keep: {[str(x.label.identification_area.lidvid) for x in products_to_keep]}")
    report_new_paths(products_to_keep, previous_bundle_dir, merged_bundle_dir)
    logger.info(f"New {label.lower()}: {[str(x.label.identification_area.lidvid) for x in new_products]}")
    report_new_paths(new_products, new_bundle_dir, merged_bundle_dir)


def report_new_paths(products: List[pds4.Pds4Product], old_base, new_base, superseded=False) -> None:
    for p in products:
        vid = p.label.identification_area.lidvid.vid
        versioned_path = paths.generate_product_path(p.label_path, superseded=superseded, vid=vid)
        new_path = paths.relocate_path(versioned_path, old_base, new_base)
        logger.info(f"{p.label.identification_area.lidvid} will be moved to {new_path}")


def do_copy_label(products: Iterable[pds4.Pds4Product], old_base, new_base, superseded=False) -> None:
    for p in products:
        vid = p.label.identification_area.lidvid.vid
        versioned_path = paths.generate_product_path(p.label_path, superseded=superseded, vid=vid)
        new_path = paths.relocate_path(versioned_path, old_base, new_base)
        dirname = os.path.dirname(new_path)
        os.makedirs(dirname, exist_ok=True)
        shutil.copy(p.label_path, new_path)


def copy_unmodified_collections(collections: Iterable[pds4.Pds4Product], old_base: str, new_base: str) -> None:
    for c in collections:
        if isinstance(c, pds4.CollectionProduct):
            new_path = paths.relocate_path(paths.generate_product_path(c.inventory_path), old_base, new_base)
            dirname = os.path.dirname(new_path)
            os.makedirs(dirname, exist_ok=True)
            shutil.copy(c.inventory_path, new_path)
        else:
            logger.info(f'Skipping non-collection product: {c.label.identification_area.lidvid}')


def do_copy_data(products: Iterable[pds4.Pds4Product], old_base, new_base, superseded=False) -> None:
    for p in products:
        if isinstance(p, pds4.BasicProduct):
            for d in p.data_paths:
                vid = p.label.identification_area.lidvid.vid
                versioned_path = paths.generate_product_path(d, superseded=superseded, vid=vid)
                new_path = paths.relocate_path(versioned_path, old_base, new_base)
                logger.debug(f'{d} -> {new_path}')
                dirname = os.path.dirname(new_path)
                os.makedirs(dirname, exist_ok=True)
                shutil.copy(d, new_path)
        else:
            logger.info(f'Skipping non-basic product: {p.label.identification_area.lidvid}')


def find_superseded(previous_products: List[pds4.Pds4Product],
                    new_products: List[pds4.Pds4Product]) -> Tuple[List[pds4.Pds4Product], List[pds4.Pds4Product]]:
    new_product_lids = set(x.label.identification_area.lidvid.lid for x in new_products)
    previous_products_to_keep = [x for x in previous_products if
                                 x.label.identification_area.lidvid.lid not in new_product_lids]
    previous_products_to_supersede = [x for x in previous_products if
                                      x.label.identification_area.lidvid.lid in new_product_lids]
    return previous_products_to_keep, previous_products_to_supersede


def check_ready(previous_bundle_directory, new_bundle_directory) -> None:
    logger.info(f"Checking readiness of new bundle {new_bundle_directory} against {previous_bundle_directory}")

    previous_fullbundle = load_local_bundle(previous_bundle_directory)
    for bundle in previous_fullbundle.bundles:
        logger.info(f'Previous bundle checksum: {bundle.label.checksum}')

    new_fullbundle = load_local_bundle(new_bundle_directory)
    for bundle in new_fullbundle.bundles:
        logger.info(f'New bundle checksum: {bundle.label.checksum}')

    do_checkready(new_fullbundle, previous_fullbundle)


def do_checkready(new_fullbundle: FullBundle, previous_fullbundle: FullBundle) -> None:
    validator.check_bundle_against_previous(previous_fullbundle.bundles[0], new_fullbundle.bundles[0])
    validator.check_bundle_against_collections(new_fullbundle.bundles[0], new_fullbundle.collections)
    for new_collection in new_fullbundle.collections:
        new_collection_lid = new_collection.label.identification_area.lidvid.lid
        previous_collections = [x for x in previous_fullbundle.collections if
                                x.label.identification_area.lidvid.lid == new_collection_lid]
        if previous_collections:
            previous_collection = previous_collections[0]
            validator.check_collection_against_previous(previous_collection, new_collection)


def load_local_bundle(path: str) -> FullBundle:
    logger.info(f'Loading bundle: {path}')
    filepaths = localclient.get_file_paths(path)
    label_paths = [x for x in filepaths if x.endswith(".xml")]

    collections = [localclient.fetchcollection(path)
                   for path in label_paths if is_collection(path) and not is_superseded(path)]
    bundles = [localclient.fetchbundle(path)
               for path in label_paths if is_bundle(path) and not is_superseded(path)]
    products = [localclient.fetchproduct(path) for path in label_paths if is_basic(path) and not is_superseded(path)]

    superseded_collections = [localclient.fetchcollection(path)
                              for path in label_paths if is_collection(path) and is_superseded(path)]
    superseded_bundles = [localclient.fetchbundle(path)
                          for path in label_paths if is_bundle(path) and is_superseded(path)]
    superseded_products = [localclient.fetchproduct(path)
                           for path in label_paths if is_basic(path) and is_superseded(path)]

    if len(bundles) == 0:
        raise Exception(f"Could not find bundle product in: {path}")
    return FullBundle(bundles, superseded_bundles, collections, superseded_collections, products, superseded_products)


def is_basic(x: str) -> bool:
    return not (is_collection(x) or is_bundle(x))


def is_collection(x: str) -> bool:
    return "collection" in x


def is_bundle(x: str) -> bool:
    return "bundle" in x


def is_superseded(x: str) -> bool:
    return "SUPERSEDED" in x


if __name__ == "__main__":
    sys.exit(main())
