#!/usr/bin/env python3
import os.path
import sys
import webclient

def main():
    bundles1, collections1, products1 = load_remote_bundle("http://localhost:8000/orex.tagcams_v1.0/")

    for b in bundles1:
        print(webclient.remote_checksum(b.url))
        print(b.label.checksum)

    bundles2, collections2, products2 = load_remote_bundle("http://localhost:8000/orex.tagcams_v2.0/")
    for b in bundles2:
        print(webclient.remote_checksum(b.url))
        print(b.label.checksum)



def load_remote_bundle(url):
    root = webclient.fetchdir(url)
    label_urls = [x for x in root.flat_files() if x.endswith(".xml")]
    product_urls = [x for x in label_urls if is_basic(x)]
    bundle_urls = [x for x in label_urls if is_bundle(x)]
    collection_urls = [x for x in label_urls if is_collection(x)]

    collections = [webclient.fetchcollection(url) for url in collection_urls]
    bundles = [webclient.fetchbundle(url) for url in bundle_urls]
    products = [webclient.fetchproduct(url) for url in product_urls]

    return bundles, collections, products

def is_basic(x):
    return not (is_collection(x) or is_bundle(x))


def is_collection(x):
    return "collection" in x


def is_bundle(x):
    return "bundle" in x


if __name__ == "__main__":
    sys.exit(main())
