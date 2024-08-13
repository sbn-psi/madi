from typing import Optional, Iterable, Dict, Tuple
import itertools
import functools

import label

class Lid:
    def __init__(self, component: str, parent: Optional[str] = None):
        self.component = component
        self.parent = parent

    def fmt(self) -> str:
        return f'{self.parent}:{self.component}' if self.parent else self.component


@functools.total_ordering
class Vid:
    def __init__(self, major: int, minor: int):
        self.major = major
        self.minor = minor

    def fmt(self) -> str:
        return f'{self.major}.{self.minor}'

    def inc_major(self) -> 'Vid':
        return Vid(self.major + 1, 0)

    def inc_minor(self) -> 'Vid':
        return Vid(self.major, self.minor + 1)

    @staticmethod
    def _is_valid_operand(other):
        return hasattr(other, "major") and hasattr(other, "minor")

    def __eq__(self, other):
        if not Vid._is_valid_operand(other):
            return NotImplemented
        return (self.major, self.minor) == (other.major, other.minor)

    def __ge__(self, other):
        if not Vid._is_valid_operand(other):
            return NotImplemented
        return (self.major, self.minor) >= (other.major, other.minor)


class LidVid:
    def __init__(self, lid: Lid, vid: Vid):
        self.lid = lid
        self.vid = vid


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


class BundleInfo:
    def __init__(self, lidvid: LidVid, collections: set[LidVid]):
        self.lidvid = lidvid
        self.collections = collections
