"""
This class represents a product, and contains the necessary
attributes for running through the pipeline.
"""
import hashlib
import os
from dataclasses import dataclass
from typing import IO, Iterable

from bs4 import BeautifulSoup
import label
import logging

from labeltypes import ProductLabel, ObservingSystemComponent


def extract_label(xmldoc: BeautifulSoup, checksum: str, filepath: str = '') -> ProductLabel:
    """
    Extracts keywords from a PDS4 label.
    """
    if xmldoc.Product_Observational:
        return label.extract_product_observational(xmldoc.Product_Observational, checksum)
    if xmldoc.Product_Ancillary:
        return label.extract_product_ancillary(xmldoc.Product_Ancillary, checksum)
    if xmldoc.Product_Document:
        return label.extract_product_document(xmldoc.Product_Document, checksum)
    if xmldoc.Product_Collection:
        return label.extract_collection(xmldoc.Product_Collection, checksum)
    if xmldoc.Product_Bundle:
        return label.extract_bundle(xmldoc.Product_Bundle, checksum)

    raise RuntimeError(f"Unknown product type: {filepath}")
    

def extract_keywords(contents: str, checksum: str, filepath: str = '') -> ProductLabel:
    """
    Wrapper for extract_label. This handles creation and destruction of
    the BeautifulSoup object.
    """
    xmldoc = BeautifulSoup(contents, 'lxml-xml')
    if xmldoc:
        keywords = extract_label(xmldoc, checksum, filepath)
        xmldoc.decompose()
        return keywords
    else:
        raise RuntimeError(f"Not a valid xml document: {filepath}")

class Product:
    """
    Represents the product itself.
    """

    def __init__(self, filepath: str) -> None:
        """
        Parses a label file into a Product
        """
        logging.debug(f"Creating product for: {filepath}")
        with open(filepath) as infile:
            contents = infile.read()
            checksum = hashlib.md5(contents.encode("utf-8")).hexdigest()
            self.keywords = extract_keywords(contents, checksum, filepath)
            self.labelfilename = os.path.basename(filepath)
            self.labeldir = os.path.dirname(filepath)
            self.labelpath = filepath

    def lidvid(self) -> str:
        return self.keywords.identification_area.lidvid

    def filenames(self) -> Iterable[str]:
        if self.keywords.document:
            return self.keywords.document.filenames()
        elif self.keywords.file_area:
            return [self.keywords.file_area.file_name]
        else:
            return []

    def start_date(self) -> str:
        return self.keywords.context_area.time_coordinates.start_date \
            if self.keywords.context_area \
            else None

    def stop_date(self) -> str:
        return self.keywords.context_area.time_coordinates.stop_date \
            if self.keywords.context_area \
            else None

    def majorversion(self) -> str:
        return str(self.keywords.identification_area.major)

    def minorversion(self) -> str:
        return str(self.keywords.identification_area.minor)

    def observing_system_components(self) -> list[ObservingSystemComponent]:
        return self.keywords.context_area.observing_system.components \
            if self.keywords.context_area and self.keywords.context_area.observing_system \
            else []

    def collection_id(self) -> str:
        return self.keywords.identification_area.collection_id

