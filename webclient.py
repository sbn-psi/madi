import itertools
import os
from typing import Iterable
from functools import cache
import hashlib

import bs4
import requests

import pds4
from label import ProductLabel
import product
from pds4 import CollectionInventory


class ArchiveDir:
    def __init__(self, url: str, files: Iterable[str], dirs: Iterable["ArchiveDir"]):
        self.url = url
        self.files = files
        self.dirs = dirs

    def flat_dirs(self) -> Iterable["ArchiveDir"]:
        return itertools.chain([self], itertools.chain.from_iterable(d.flat_dirs() for d in self.dirs))

    def flat_files(self) -> Iterable[str]:
        return itertools.chain(self.files, itertools.chain.from_iterable(d.flat_files() for d in self.dirs))


def fetchdir(url) -> ArchiveDir:
    r = requests.get(url)
    if r.status_code == 200:
        soup = bs4.BeautifulSoup(r.text, "lxml")
        hrefs = (str(a["href"]) for a in soup("a"))
        urls = [make_absolute(url, href) for href in hrefs if is_below(url, href) and not is_ignored(href)]
        directory_urls = [url for url in urls if url.endswith("/")]
        file_urls = [url for url in urls if not url.endswith("/")]
        dirs = [fetchdir(url) for url in directory_urls]
        return ArchiveDir(url, file_urls, dirs)

    raise Exception("Could not reach url: " + url)


def fetchlabel(url) -> ProductLabel:
    r = requests.get(url)
    if r.status_code == 200:
        text = r.text
        checksum = hashlib.md5(text.encode('utf-8')).hexdigest()
        soup = bs4.BeautifulSoup(text, "lxml-xml")
        return product.extract_label(soup, checksum, url)

    raise Exception("Could not reach url: " + url)


def fetchinventory(url) -> CollectionInventory:
    r = requests.get(url)
    if r.status_code == 200:
        return CollectionInventory.from_csv(r.text)

    raise Exception("Could not reach url: " + url)


def fetchcollection(label_url) -> pds4.Collection:
    collection_label = fetchlabel(label_url)
    inventory_url = os.path.join(os.path.dirname(label_url), collection_label.file_area.file_name)
    inventory = fetchinventory(inventory_url)
    return pds4.Collection(collection_label, inventory, label_url, inventory_url)


def fetchbundle(label_url) -> pds4.Bundle:
    bundle_label = fetchlabel(label_url)
    return pds4.Bundle(bundle_label, label_url)


def fetchproduct(label_url) -> pds4.ProductInfo:
    product_label = fetchlabel(label_url)
    basepath = os.path.dirname(label_url)
    data_urls = rebase_filenames(basepath, [product_label.file_area.file_name]) if product_label.file_area else []
    document_urls = rebase_filenames(basepath, product_label.document.filenames()) if product_label.document else []
    return pds4.ProductInfo(product_label, label_url, data_urls + document_urls)


def fetch_file(url: str, destfilename) -> str:
    r = requests.get(url)
    if r.status_code == 200:
        c = hashlib.md5()
        with open(destfilename) as destfile:
            for chunk in r.iter_content():
                c.update(chunk)
                destfile.write(chunk)
        return c.hexdigest()
    raise Exception("Could not reach url: " + url)


def build_destfilename(url, baseurl, basepath, superseded_version=None):
    dir_url = os.path.dirname(url)
    filename = os.path.basename(url)
    dir_path = dir_url.replace(baseurl, basepath)
    dest_path = os.path.join(dir_path, 'SUPERSEDED', f'V_{superseded_version.replace(".", "_")}') \
        if superseded_version else dir_path
    destfilename = os.path.join(dest_path, filename, 'wb')
    return destfilename


def save_pds4_file(url: str, baseurl: str, basepath: str, superseded_version=None):
    destfilename = build_destfilename(url, baseurl, basepath, superseded_version)
    fetch_file(url, destfilename)


@cache
def remote_checksum(url: str) -> str:
    r = requests.get(url)
    if r.status_code == 200:
        m = hashlib.md5()
        for c in r.iter_content(chunk_size=4096):
            m.update(c)
        return m.hexdigest()
    raise Exception("Could not reach url: " + url)


def rebase_filenames(basepath, filenames):
    return [os.path.join(basepath, filename) for filename in filenames]


def make_absolute(base: str, candidate: str) -> str:
    if candidate.startswith(base):
        return candidate
    return base + candidate


def is_below(base: str, candidate: str) -> bool:
    return candidate.startswith(base) or (not "://" in candidate and not candidate.startswith("/") and not candidate.startswith(".."))


def is_ignored(candidate: str):
    return any([".DS_Store" in candidate, candidate.startswith("?")])
