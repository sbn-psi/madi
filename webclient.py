import itertools
from typing import Iterable

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
        soup = bs4.BeautifulSoup(r.text, "lxml-xml")
        return product.extract_label(soup, url)

    raise Exception("Could not reach url: " + url)


def fetchinventory(url) -> CollectionInventory:
    r = requests.get(url)
    if r.status_code == 200:
        return CollectionInventory.from_csv(r.text)

    raise Exception("Could not reach url: " + url)




def make_absolute(base: str, candidate: str) -> str:
    if candidate.startswith(base):
        return candidate
    return base + candidate


def is_below(base: str, candidate: str) -> bool:
    return candidate.startswith(base) or (not "://" in candidate and not candidate.startswith("/") and not candidate.startswith(".."))


def is_ignored(candidate: str):
    return any([".DS_Store" in candidate, candidate.startswith("?")])
