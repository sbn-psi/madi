#!/usr/bin/env python3

import sys
import webclient

def main():
    url = "http://localhost:8000/orex.tagcams_v1.0/"
    root = webclient.fetchdir(url)
    label_urls = [x for x in root.flat_files() if x.endswith(".xml")]
    product_urls = [x for x in label_urls if not is_collection(x) and not is_bundle(x)]
    bundle_urls = [x for x in label_urls if is_bundle(x)]
    collection_urls = [x for x in label_urls if is_collection(x)]

    for url in bundle_urls:
        label = webclient.fetchlabel(url)
        print(f"{label.identification_area.lidvid}, {url}")


def is_collection(x):
    return "collection" in x


def is_bundle(x):
    return "bundle" in x


if __name__ == "__main__":
    sys.exit(main())
