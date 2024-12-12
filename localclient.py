import hashlib
import itertools
import os
from typing import Iterable

import bs4

import paths
import product
from labeltypes import ProductLabel

from pds4 import CollectionProduct, BundleProduct, BasicProduct, CollectionInventory


def fetchcollection(path: str) -> CollectionProduct:
    """Retrieves a collection product located at the specified path"""
    collection_label = fetchlabel(path)
    inventory_path = os.path.join(os.path.dirname(path), collection_label.file_areas[0].file_name)
    with open(inventory_path, newline="") as f:
        inventory = CollectionInventory.from_csv(f.read())
    return CollectionProduct(collection_label, inventory, label_path=path, inventory_path=inventory_path)


def fetchbundle(path: str) -> BundleProduct:
    """Retrieves a bundle product located at the specified path"""
    bundle_label = fetchlabel(path)
    dirname = os.path.dirname(path)
    readme_path = os.path.join(dirname, bundle_label.file_areas[0].file_name) if bundle_label.file_areas else None

    return BundleProduct(bundle_label, label_path=path, readme_path=readme_path)


def fetchproduct(path: str) -> BasicProduct:
    """Retrieves a basic product located at the specified path"""
    product_label = fetchlabel(path)
    dirname = os.path.dirname(path)
    data_paths = paths.rebase_filenames(dirname, [f.file_name for f in product_label.file_areas]) if product_label.file_areas else []
    document_paths = paths.rebase_filenames(dirname, product_label.document.filenames()) if product_label.document else []

    return BasicProduct(product_label, label_path=path, data_paths=data_paths + document_paths)


def fetchlabel(path: str) -> ProductLabel:
    """Retrieves a product label located at the specified path"""
    with open(path) as f:
        text = f.read()
        checksum = hashlib.md5(text.encode('utf-8')).hexdigest()
        soup = bs4.BeautifulSoup(text, "lxml-xml")
        return product.extract_label(soup, checksum, path)


def get_file_paths(path: str) -> Iterable[str]:
    """Retrieves every file path located below a directory."""
    return itertools.chain.from_iterable(
        (os.path.join(dirpath, filename) for filename in filenames)
        for dirpath, _, filenames in os.walk(path))
