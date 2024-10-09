import os

from pds4 import Pds4Product


def rebase_filenames(basepath, filenames):
    return [os.path.join(basepath, filename) for filename in filenames]


def generate_product_dir(p: Pds4Product, superseded=False):
    product_dirname = os.path.dirname(p.label_path)
    if superseded and "SUPERSEDED" not in p.label_path:
        vid = p.label.identification_area.lidvid.vid
        return os.path.join(product_dirname, "SUPERSEDED", f'V{vid.major}_{vid.minor}')
    return product_dirname
