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
    if xmldoc.Product_Context:
        return label.extract_product_context(xmldoc.Product_Context, checksum)
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

