#!/usr/bin/env python3
import os.path
import sys
import webclient

def main():
    url = "http://localhost:8000/orex.tagcams_v1.0/"
    root = webclient.fetchdir(url)
    label_urls = [x for x in root.flat_files() if x.endswith(".xml")]
    product_urls = [x for x in label_urls if not is_collection(x) and not is_bundle(x)]
    bundle_urls = [x for x in label_urls if is_bundle(x)]
    collection_urls = [x for x in label_urls if is_collection(x)]

    for url in collection_urls:
        label = webclient.fetchlabel(url)
        print(f"{label.identification_area.lidvid}, {url}")
        print(label)

        collection_url = os.path.join(os.path.dirname(url), label.file_area.file_name)
        inventory = webclient.fetchinventory(collection_url)
        for p in inventory.products():
            print(p.fmt())



def is_collection(x):
    return "collection" in x


def is_bundle(x):
    return "bundle" in x


if __name__ == "__main__":
    sys.exit(main())
