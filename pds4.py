from dataclasses import dataclass
from typing import Optional, Iterable, Dict, Tuple
import itertools
import functools

import label


@dataclass()
class Lid:
    prefix: str
    bundle: str
    collection: str = None
    product: str = None

    @staticmethod
    def parse(lid: str) -> "Lid":
        tokens = lid.split(":")
        return Lid(
            prefix=":".join(tokens[0:3]),
            bundle=tokens[3],
            collection=tokens[4] if len(tokens) >= 5 else None,
            product=tokens[5] if len(tokens) >= 6 else None
        )

    def fmt(self):
        if self.product and self.collection:
            return f"{self.prefix}:{self.bundle}:{self.collection}:{self.product}"
        if self.collection:
            return f"{self.prefix}:{self.bundle}:{self.collection}"
        return f"{self.prefix}:{self.bundle}"


@dataclass(order=True)
class Vid:
    major: int
    minor: int

    @staticmethod
    def parse(vid):
        tokens = vid.split(".")
        return Vid(
            major=int(tokens[0]),
            minor=int(tokens[1])
        )

    def fmt(self) -> str:
        return f'{self.major}.{self.minor}'

    def inc_major(self) -> 'Vid':
        return Vid(self.major + 1, 0)

    def inc_minor(self) -> 'Vid':
        return Vid(self.major, self.minor + 1)


@dataclass()
class LidVid:
    lid: Lid
    vid: Vid
    @staticmethod
    def parse(lidvid):
        tokens = lidvid.split("::")
        return LidVid(
            lid=Lid.parse(tokens[0]),
            vid=Vid.parse(tokens[1])
        )

    def fmt(self):
        return f'{self.lid.fmt()}::{self.vid.fmt()}'


class ProductInfo:
    def __init__(self, lidvid: LidVid, path: str, lbl: label.ProductLabel):
        self.lidvid: LidVid = lidvid
        self.path = path
        self.lbl = lbl


class CollectionInfo:
    def __init__(self, lidvid: LidVid, products: set[ProductInfo]):
        self.lidvid = lidvid
        self.lids = dict((x.lidvid.lid, x) for x in products)

    def lookup_product(self, lid: Lid) -> ProductInfo:
        return self.lids.get(lid)

    def add_product(self, product: ProductInfo):
        self.lids[product.lidvid.lid] = product

    def products(self) -> Iterable[ProductInfo]:
        return self.lids.values()


class CollectionInventory:
    def __init__(self, primary: set[ProductInfo], secondary: set[ProductInfo]):
        self.primary = dict((x.lidvid.lid, x) for x in primary)
        self.secondary = dict((x.lidvid.lid, x) for x in secondary)

        if any(x.lidvid.lid in primary for x in secondary):
            raise Exception("Some products exist in both primary and secondary collections")

    def add_primary(self, product: ProductInfo):
        lid = product.lidvid.lid
        if lid in self.secondary:
            raise Exception("Product already exists as a secondary member and can't be made primary")
        if lid in self.primary:
            previous = self.primary[lid]
            if previous.lidvid.vid >= product.lidvid.vid:
                raise Exception("Product is not newer than the version that already exists in the inventory")
        self.primary[lid] = product

    def add_secondary(self, product: ProductInfo):
        lid = product.lidvid.lid
        if lid in self.primary:
            raise Exception("Product already exists as a primary member and can't be made secondary")
        if lid in self.secondary:
            previous = self.secondary[lid]
            if previous.lidvid.vid >= product.lidvid.vid:
                raise Exception("Product is not newer than the version that already exists in the inventory")
        self.secondary[lid] = product

    def products(self) -> set[ProductInfo]:
        return set(itertools.chain(self.primary.values(), self.secondary.values()))

    @staticmethod
    def from_csv(csvdata) -> "CollectionInventory":
        pass


class BundleInfo:
    def __init__(self, lidvid: LidVid, collections: set[LidVid]):
        self.lidvid = lidvid
        self.collections = collections
