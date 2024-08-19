from dataclasses import dataclass
from typing import Optional, Iterable, Dict, Tuple
import itertools
import csv

import label


@dataclass(frozen=True)
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

    def __repr__(self):
        if self.product and self.collection:
            return f"{self.prefix}:{self.bundle}:{self.collection}:{self.product}"
        if self.collection:
            return f"{self.prefix}:{self.bundle}:{self.collection}"
        return f"{self.prefix}:{self.bundle}"


@dataclass(frozen=True, order=True)
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

    def __repr__(self) -> str:
        return f'{self.major}.{self.minor}'

    def inc_major(self) -> 'Vid':
        return Vid(self.major + 1, 0)

    def inc_minor(self) -> 'Vid':
        return Vid(self.major, self.minor + 1)


@dataclass(frozen=True)
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

    def __repr__(self):
        return f'{self.lid}::{self.vid}'

    def inc_major(self) -> "LidVid":
        return LidVid(self.lid, self.vid.inc_major())

    def inc_minor(self) -> "LidVid":
        return LidVid(self.lid, self.vid.inc_minor())


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
    def __init__(self, primary: set[LidVid] = None, secondary: set[LidVid] = None):
        self.primary = dict((x.lid, x) for x in primary) if primary is not None else {}
        self.secondary = dict((x.lid, x) for x in secondary) if primary is not None else {}

        if any(x in self.primary.keys() for x in self.secondary.keys()):
            raise Exception("Some products exist in both primary and secondary collections")

    def add_primary(self, lidvid: LidVid):
        lid = lidvid.lid
        if lid in self.secondary:
            raise Exception("Product already exists as a secondary member and can't be made primary")
        if lid in self.primary:
            previous = self.primary[lid]
            if previous.vid >= lidvid.vid:
                raise Exception("Product is not newer than the version that already exists in the inventory")
        self.primary[lid] = lidvid

    def add_secondary(self, lidvid: LidVid):
        lid = lidvid.lid
        if lid in self.primary:
            raise Exception("Product already exists as a primary member and can't be made secondary")
        if lid in self.secondary:
            previous = self.secondary[lid]
            if lidvid.vid >= lidvid.vid:
                raise Exception("Product is not newer than the version that already exists in the inventory")
        self.secondary[lid] = lidvid

    def products(self) -> set[LidVid]:
        return set(itertools.chain(self.primary.values(), self.secondary.values()))

    @staticmethod
    def from_csv(csvdata) -> "CollectionInventory":
        inventory = CollectionInventory()
        reader = csv.DictReader(csvdata.split("\r\n"), fieldnames=['status', 'lidvid'])
        for line in reader:
            status = line["status"]
            lidvid = LidVid.parse(line["lidvid"])
            if status == "P":
                inventory.add_primary(lidvid)
            else:
                inventory.add_secondary(lidvid)
        return inventory

    def ingest_new_inventory(self, new_inventory: "CollectionInventory"):
        for lidvid in new_inventory.primary.values():
            self.add_primary(lidvid)
        for lidvid in new_inventory.secondary.values():
            self.add_secondary(lidvid)



class BundleInfo:
    def __init__(self, lidvid: LidVid, collections: set[LidVid]):
        self.lidvid = lidvid
        self.collections = collections
