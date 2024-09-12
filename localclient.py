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
    with open(inventory_path) as f:
        inventory = pds4.CollectionInventory.from_csv(f.read())
    return pds4.Collection(collection_label, inventory)


def fetchbundle(path):
    bundle_label = fetchlabel(path)
    return pds4.Bundle(bundle_label)


def fetchproduct(path):
    product_label = fetchlabel(path)
    return pds4.ProductInfo(product_label)


def fetchlabel(path):
    with open(path) as f:
        text = f.read()
        checksum = hashlib.md5(text.encode('utf-8')).hexdigest()
        soup = bs4.BeautifulSoup(text, "lxml-xml")
        return product.extract_label(soup, checksum)


def get_file_paths(path):
    return itertools.chain.from_iterable(
        (os.path.join(dirpath, filename) for filename in filenames)
        for dirpath, _, filenames in os.walk(path))
