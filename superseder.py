import itertools
import logging
import os
import shutil
from typing import List, Iterable, Tuple

import paths
import pds4

logger = logging.getLogger(__name__)


def supersede(previous_fullbundle, new_fullbundle, merged_bundle_directory) -> None:
    previous_bundle_directory = previous_fullbundle.path
    new_bundle_directory = new_fullbundle.path

    logger.info(f"TODO: Supersede {previous_bundle_directory} "
                f"with new data from {new_bundle_directory} into {merged_bundle_directory}")

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

    copy_previously_superseded_products(
        previous_fullbundle.superseded_products,
        previous_fullbundle.collections,
        previous_fullbundle.bundles,
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


def copy_previously_superseded_products(
        products: Iterable[pds4.BasicProduct],
        collections: Iterable[pds4.CollectionProduct],
        bundles: Iterable[pds4.BundleProduct],
        old_base: str,
        new_base: str):
    for bundle in bundles:
        copy_to_path(bundle.label_path, paths.relocate_path(bundle.label_path, old_base, new_base))
    for collection in collections:
        copy_to_path(collection.label_path, paths.relocate_path(collection.label_path, old_base, new_base))
        copy_to_path(collection.inventory_path, paths.relocate_path(collection.inventory_path, old_base, new_base))
    for product in products:
        copy_to_path(product.label_path, paths.relocate_path(product.label_path, old_base, new_base))
        for data_path in product.data_paths:
            if os.path.exists(data_path):
                copy_to_path(data_path, paths.relocate_path(data_path, old_base, new_base))


def copy_unmodified_collections(collections: Iterable[pds4.Pds4Product], old_base: str, new_base: str) -> None:
    for c in collections:
        if isinstance(c, pds4.CollectionProduct):
            new_path = paths.relocate_path(paths.generate_product_path(c.inventory_path), old_base, new_base)
            copy_to_path(c.inventory_path, new_path)
        else:
            logger.info(f'Skipping non-collection product: {c.label.identification_area.lidvid}')


def do_copy_data(products: Iterable[pds4.Pds4Product], old_base, new_base, superseded=False) -> None:
    for p in products:
        if isinstance(p, pds4.BasicProduct):
            for d in p.data_paths:
                vid = p.label.identification_area.lidvid.vid
                versioned_path = paths.generate_product_path(d, superseded=superseded, vid=vid)
                new_path = paths.relocate_path(versioned_path, old_base, new_base)
                copy_to_path(d, new_path)
        else:
            logger.info(f'Skipping non-basic product: {p.label.identification_area.lidvid}')


def copy_to_path(src_path: str, dest_path: str):
    logger.debug(f'{src_path} -> {dest_path}')
    dirname = os.path.dirname(dest_path)
    os.makedirs(dirname, exist_ok=True)
    shutil.copy(src_path, dest_path)


def find_superseded(previous_products: List[pds4.Pds4Product],
                    new_products: List[pds4.Pds4Product]) -> Tuple[List[pds4.Pds4Product], List[pds4.Pds4Product]]:
    new_product_lids = set(x.label.identification_area.lidvid.lid for x in new_products)
    previous_products_to_keep = [x for x in previous_products if
                                 x.label.identification_area.lidvid.lid not in new_product_lids]
    previous_products_to_supersede = [x for x in previous_products if
                                      x.label.identification_area.lidvid.lid in new_product_lids]
    return previous_products_to_keep, previous_products_to_supersede

