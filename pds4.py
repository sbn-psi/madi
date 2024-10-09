from dataclasses import dataclass
from typing import List
import itertools
import csv

import label
import labeltypes

from lids import LidVid

class Pds4Product:
    def __init__(self, product_label: labeltypes.ProductLabel, label_url: str = None, label_path: str = None):
        self.label = product_label
        self.label_url = label_url
        self.label_path = label_path


class BasicProduct(Pds4Product):
    def __init__(self, product_label: labeltypes.ProductLabel, label_url: str = None,
                 data_urls: List[str] = None, label_path: str = None, data_paths: List[str] = None):
        super().__init__(product_label, label_url, label_path)
        self.data_urls = data_urls
        self.data_paths = data_paths


class CollectionProduct(Pds4Product):
    def __init__(self,
                 collection_label: labeltypes.ProductLabel,
                 inventory: "CollectionInventory",
                 label_url: str = None,
                 inventory_url: str = None,
                 label_path: str = None,
                 inventory_path: str = None):
        super().__init__(collection_label, label_url, label_path)
        self.inventory = inventory
        self.inventory_url = inventory_url
        self.inventory_path = inventory_path


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
            if previous.vid >= lidvid.vid:
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

    def to_csv(self) -> str:
        return "\r\n".join(itertools.chain(
            sorted((f'P,{x}' for x in self.primary.values())),
            sorted((f'S,{x}' for x in self.secondary.values()))
        ))


class BundleProduct(Pds4Product):
    def __init__(self, bundle_label: labeltypes.ProductLabel, url: str = None, path: str = None):
        super().__init__(bundle_label, url, path)
