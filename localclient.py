import hashlib
import itertools
import os

import bs4

import paths
import product
import pds4


def fetchcollection(path):
    collection_label = fetchlabel(path)
    inventory_path = os.path.join(os.path.dirname(path), collection_label.file_area.file_name)
    with open(inventory_path, newline="") as f:
        inventory = pds4.CollectionInventory.from_csv(f.read())
    return pds4.CollectionProduct(collection_label, inventory, label_path=path, inventory_path=inventory_path)


def fetchbundle(path):
    bundle_label = fetchlabel(path)
    return pds4.BundleProduct(bundle_label, path=path)


def fetchproduct(path):
    product_label = fetchlabel(path)
    data_paths = paths.rebase_filenames(path, [product_label.file_area.file_name]) if product_label.file_area else []
    document_paths = paths.rebase_filenames(path, product_label.document.filenames()) if product_label.document else []

    return pds4.BasicProduct(product_label, label_path=path, data_paths=data_paths + document_paths)


def fetchlabel(path):
    with open(path) as f:
        text = f.read()
        checksum = hashlib.md5(text.encode('utf-8')).hexdigest()
        soup = bs4.BeautifulSoup(text, "lxml-xml")
        return product.extract_label(soup, checksum, path)


def get_file_paths(path):
    return itertools.chain.from_iterable(
        (os.path.join(dirpath, filename) for filename in filenames)
        for dirpath, _, filenames in os.walk(path))
