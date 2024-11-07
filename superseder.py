import itertools
import logging
import os
import shutil
from typing import List, Iterable, Tuple

import paths
import pds4

import re

logger = logging.getLogger(__name__)


def supersede(previous_fullbundle: pds4.FullBundle, delta_fullbundle: pds4.FullBundle, merged_bundle_directory, dry: bool) -> None:
    """
    Merges the bundles together and supersedes any products that have a newer version.
    """
    previous_bundle_directory = previous_fullbundle.path
    delta_bundle_directory = delta_fullbundle.path

    logger.info(f"TODO: Supersede {previous_bundle_directory} "
                f"with delta data from {delta_bundle_directory} into {merged_bundle_directory}")

    previous_bundles_to_keep, previous_bundles_to_supersede = find_products_to_supersede(previous_fullbundle.bundles,
                                                                                         delta_fullbundle.bundles)
    report_superseded(previous_bundles_to_keep,
                      previous_bundles_to_supersede,
                      delta_fullbundle.bundles,
                      previous_bundle_directory,
                      delta_bundle_directory,
                      merged_bundle_directory,
                      "Bundles")

    previous_collections_to_keep, previous_collections_to_supersede = find_products_to_supersede(previous_fullbundle.collections,
                                                                                                 delta_fullbundle.collections)
    report_superseded(previous_collections_to_keep,
                      previous_collections_to_supersede,
                      delta_fullbundle.collections,
                      previous_bundle_directory,
                      delta_bundle_directory,
                      merged_bundle_directory,
                      "Collections")

    previous_products_to_keep, previous_products_to_supersede = find_products_to_supersede(previous_fullbundle.products,
                                                                                           delta_fullbundle.products)
    report_superseded(previous_products_to_keep,
                      previous_products_to_supersede,
                      delta_fullbundle.products,
                      previous_bundle_directory,
                      delta_bundle_directory,
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
    do_copy_label(itertools.chain(delta_fullbundle.collections,
                                  delta_fullbundle.bundles,
                                  delta_fullbundle.products), delta_bundle_directory, merged_bundle_directory)

    do_copy_data(previous_products_to_keep, previous_bundle_directory, merged_bundle_directory, dry)
    do_copy_data(previous_products_to_supersede, previous_bundle_directory, merged_bundle_directory, dry, superseded=True)
    do_copy_data(delta_fullbundle.products, delta_bundle_directory, merged_bundle_directory, dry)

    do_copy_readme(previous_fullbundle.superseded_bundles, previous_bundle_directory, merged_bundle_directory, superseded=True)
    do_copy_readme(previous_fullbundle.bundles, previous_bundle_directory, merged_bundle_directory, superseded=True)
    do_copy_readme(delta_fullbundle.bundles, delta_bundle_directory, merged_bundle_directory)

    do_copy_inventory(previous_collections_to_supersede, previous_bundle_directory, merged_bundle_directory, superseded=True)

    copy_unmodified_collections(previous_collections_to_keep, previous_bundle_directory, delta_bundle_directory, dry)
    generate_collections(previous_collections_to_supersede,
                         delta_fullbundle.collections,
                         previous_bundle_directory,
                         delta_bundle_directory,
                         merged_bundle_directory,
                         dry)

    copy_previously_superseded_products(
        previous_fullbundle.superseded_products,
        previous_fullbundle.superseded_collections,
        previous_fullbundle.superseded_bundles,
        previous_bundle_directory,
        merged_bundle_directory,
        dry)


def generate_collections(previous_collections_to_supersede: List[pds4.Pds4Product],
                         delta_collections: List[pds4.CollectionProduct],
                         previous_bundle_directory: str,
                         delta_bundle_directory: str,
                         merged_bundle_directory: str,
                         dry: bool) -> None:
    """
    Matches up previous and delta collections and merges their inventories.
    """
    logger.info(f"Merging collection inventories")
    for previous_collection in previous_collections_to_supersede:
        logger.info(f"Merging collection inventory: {previous_collection.label.identification_area.lidvid}")
        if isinstance(previous_collection, pds4.CollectionProduct):
            previous_collection_lid = previous_collection.label.identification_area.lidvid.lid
            delta_collection = [x for x in delta_collections
                                if x.label.identification_area.lidvid.lid == previous_collection_lid][0]
            generate_collection(previous_collection, delta_collection, previous_bundle_directory, delta_bundle_directory,
                                merged_bundle_directory, dry)


def generate_collection(previous_collection: pds4.CollectionProduct,
                        delta_collection: pds4.CollectionProduct,
                        previous_bundle_directory: str,
                        delta_bundle_directory: str,
                        merged_bundle_directory: str,
                        dry: bool) -> None:
    """
    Merges the inventories from the previous and delta collection and updates the label file with the new
    record count.
    """
    inventory = pds4.CollectionInventory()
    inventory.ingest_new_inventory(previous_collection.inventory)
    inventory.ingest_new_inventory(delta_collection.inventory)
    previous_count = len(previous_collection.inventory.products())
    delta_count = len(delta_collection.inventory.products())
    product_count = len(inventory.products())
    logger.info(f"Merged collection has {product_count} products after adding {delta_count} to {previous_count}")
    inventory_path = paths.relocate_path(previous_collection.inventory_path,
                                         previous_bundle_directory,
                                         merged_bundle_directory)

    if not dry:
        logger.info(f"Writing merged inventory to {inventory_path}")
        with open(inventory_path, 'w') as f:
            f.write(inventory.to_csv())
    else:
        logger.info(f"Skipped: Writing merged inventory to {inventory_path}")

    inventory_label_contents = open(delta_collection.label_path).read()
    new_inventory_label_contents = re.sub(r"<records>\d*</records>", f"<records>{product_count}</records>",
                                          inventory_label_contents)
    new_path = paths.relocate_path(delta_collection.label_path, delta_bundle_directory, merged_bundle_directory)

    if not dry:
        logger.info(f"Writing new inventory label to f{new_path}")
        open(new_path, "w").write(new_inventory_label_contents)
    else:
        logger.info(f"Skipped: Writing new inventory label to f{new_path}")


def report_superseded(products_to_keep: List[pds4.Pds4Product],
                      products_to_supersede: List[pds4.Pds4Product],
                      delta_products: List[pds4.Pds4Product],
                      previous_bundle_dir,
                      delta_bundle_dir,
                      merged_bundle_dir,
                      label: str = "Products") -> None:
    """
    Logs which products will be superseded by MADI
    """
    logger.info(f"{label} to supersede: {[str(x.label.identification_area.lidvid) for x in products_to_supersede]}")
    report_new_paths(products_to_supersede, previous_bundle_dir, merged_bundle_dir, True)
    logger.info(f"{label} to keep: {[str(x.label.identification_area.lidvid) for x in products_to_keep]}")
    report_new_paths(products_to_keep, previous_bundle_dir, merged_bundle_dir)
    logger.info(f"New {label.lower()}: {[str(x.label.identification_area.lidvid) for x in delta_products]}")
    report_new_paths(delta_products, delta_bundle_dir, merged_bundle_dir)


def report_new_paths(products: List[pds4.Pds4Product], old_base, new_base, superseded=False) -> None:
    """
    Logs the new paths for the given products
    """
    for p in products:
        vid = p.label.identification_area.lidvid.vid
        versioned_path = paths.generate_product_path(p.label_path, superseded=superseded, vid=vid)
        new_path = paths.relocate_path(versioned_path, old_base, new_base)
        logger.info(f"{p.label.identification_area.lidvid} will be moved to {new_path}")


def do_copy_label(products: Iterable[pds4.Pds4Product], old_base, new_base, superseded=False) -> None:
    """
    Copies a label to a new directory. This will update the path to move it to the superseded directory if necessary.
    """
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
        new_base: str,
        dry: bool):
    """
    Copies products that have already been superseded to a new directory. Since these have already been superseded,
    no manipulations to their path should be necessary.
    """
    for bundle in bundles:
        copy_to_path(bundle.label_path, paths.relocate_path(bundle.label_path, old_base, new_base), dry)
    for collection in collections:
        copy_to_path(collection.label_path, paths.relocate_path(collection.label_path, old_base, new_base), dry)
        copy_to_path(collection.inventory_path, paths.relocate_path(collection.inventory_path, old_base, new_base), dry)
    for product in products:
        copy_to_path(product.label_path, paths.relocate_path(product.label_path, old_base, new_base), dry)
        for data_path in product.data_paths:
            if os.path.exists(data_path):
                copy_to_path(data_path, paths.relocate_path(data_path, old_base, new_base), dry)


def copy_unmodified_collections(collections: Iterable[pds4.Pds4Product], old_base: str, new_base: str, dry: bool) -> None:
    """
    Copies collection labels and inventories that should be passed through as-is to a new directory
    """
    for c in collections:
        if isinstance(c, pds4.CollectionProduct):
            new_path = paths.relocate_path(paths.generate_product_path(c.inventory_path), old_base, new_base)
            copy_to_path(c.inventory_path, new_path, dry)
        else:
            logger.info(f'Skipping non-collection product: {c.label.identification_area.lidvid}')


def do_copy_inventory(collections: Iterable[pds4.Pds4Product], old_base, new_base, superseded=False, dry=False) -> None:
    """
    Copies the collection inventories of a collection product to a new directory
    """
    for c in collections:
        if isinstance(c, pds4.CollectionProduct):
            d = c.inventory_path
            vid = c.label.identification_area.lidvid.vid
            versioned_path = paths.generate_product_path(d, superseded=superseded, vid=vid)
            new_path = paths.relocate_path(versioned_path, old_base, new_base)
            copy_to_path(d, new_path, dry)
        else:
            logger.info(f'Skipping non-collection product: {c.label.identification_area.lidvid}')


def do_copy_data(products: Iterable[pds4.Pds4Product], old_base, new_base, dry: bool, superseded=False) -> None:
    """
    Copies the data files of a basic product to another directory
    """
    for p in products:
        if isinstance(p, pds4.BasicProduct):
            for d in p.data_paths:
                vid = p.label.identification_area.lidvid.vid
                versioned_path = paths.generate_product_path(d, superseded=superseded, vid=vid)
                new_path = paths.relocate_path(versioned_path, old_base, new_base)
                copy_to_path(d, new_path, dry)
        else:
            logger.info(f'Skipping non-basic product: {p.label.identification_area.lidvid}')


def do_copy_readme(products: Iterable[pds4.BundleProduct], old_base, new_base, superseded=False, dry = False) -> None:
    """
    Copies the readme file of a bundle product to another directory
    """
    for p in products:
        if p.readme_path:
            vid = p.label.identification_area.lidvid.vid
            versioned_path = paths.generate_product_path(p.readme_path, superseded=superseded, vid=vid)
            new_path = paths.relocate_path(versioned_path, old_base, new_base)
            copy_to_path(p.readme_path, new_path, dry)


def copy_to_path(src_path: str, dest_path: str, dry: bool):
    """
    Copies files from one path to another. Essentially a wrapper for shutil.copy that logs the copy operation
    and makes sure that all of the parent directories exist.
    """
    logger.debug(f'{src_path} -> {dest_path}')
    if not dry:
        dirname = os.path.dirname(dest_path)
        os.makedirs(dirname, exist_ok=True)
        shutil.copy(src_path, dest_path)


def find_products_to_supersede(previous_products: List[pds4.Pds4Product],
                               delta_products: List[pds4.Pds4Product]) -> Tuple[List[pds4.Pds4Product], List[pds4.Pds4Product]]:
    """
    Compares products in the delta bundle to the existing products, and determines which of the existing products should
    be superseded.
    :param previous_products: A list of products that were in the existing bundle.
    :param delta_products: A list of products that are present in the existing bundle
    :return: A tuple consisting of a list of products to keep as-is and a list of products that should be superseded.
    """
    delta_product_lids = set(x.label.identification_area.lidvid.lid for x in delta_products)
    previous_products_to_keep = [x for x in previous_products if
                                 x.label.identification_area.lidvid.lid not in delta_product_lids]
    previous_products_to_supersede = [x for x in previous_products if
                                      x.label.identification_area.lidvid.lid in delta_product_lids]
    return previous_products_to_keep, previous_products_to_supersede

