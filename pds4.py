from dataclasses import dataclass
from typing import List, Iterable
import itertools
import csv

import labeltypes

from lids import LidVid


class Pds4Product:
    def __init__(self, product_label: labeltypes.ProductLabel, label_url: str = None, label_path: str = None):
        self.label = product_label
        self.label_url = label_url
        self.label_path = label_path

    def lidvid(self) -> LidVid:
        return self.label.identification_area.lidvid


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


@dataclass
class InventoryItem:
    lidvid: LidVid
    status: str


class CollectionInventory:
    def __init__(self, items: Iterable[InventoryItem] = ()):
        self.items = dict((x.lidvid.lid, x) for x in items) if items else {}

    def add_item(self, item: InventoryItem):
        lid = item.lidvid.lid
        if lid in self.items:
            previous = self.items[lid]
            if previous.lidvid.vid >= item.lidvid.vid:
                raise Exception("Product is not newer than the version that already exists in the inventory")
        self.items[lid] = item

    def products(self) -> set[LidVid]:
        return set(x.lidvid for x in self.items.values())

    @staticmethod
    def from_csv(csvdata) -> "CollectionInventory":
        inventory = CollectionInventory()
        reader = csv.DictReader(csvdata.split("\r\n"), fieldnames=['status', 'lidvid'])
        for line in reader:
            status = line["status"]
            lidvid = LidVid.parse(line["lidvid"])
            inventory.add_item(InventoryItem(lidvid, status))
        return inventory

    def ingest_new_inventory(self, new_inventory: "CollectionInventory") -> None:
        for item in new_inventory.items.values():
            self.add_item(item)

    def to_csv(self) -> str:
        return "\r\n".join(itertools.chain(
            sorted((f'{x.status},{x.lidvid}' for x in self.items.values()))
        ))


class BundleProduct(Pds4Product):
    def __init__(self, bundle_label: labeltypes.ProductLabel,
                 label_url: str = None,
                 label_path: str = None,
                 readme_url: str = None,
                 readme_path: str = None):
        super().__init__(bundle_label, label_url, label_path)
        self.readme_url = readme_url
        self.readme_path = readme_path


@dataclass
class FullBundle:
    path: str
    bundles: List[BundleProduct]
    superseded_bundles: List[BundleProduct]
    collections: List[CollectionProduct]
    superseded_collections: List[CollectionProduct]
    products: List[BasicProduct]
    superseded_products: List[BasicProduct]