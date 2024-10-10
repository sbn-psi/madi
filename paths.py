import logging
import os
from typing import Iterable, List

from pds4 import Pds4Product

logger = logging.getLogger(__name__)


def rebase_filenames(basepath: str, filenames: Iterable[str]) -> List[str]:
    return [os.path.join(basepath, filename) for filename in filenames]


def relocate_path(path: str, old_base: str, new_base: str) -> str:
    if path.startswith(old_base):
        return os.path.join(new_base, os.path.relpath(path, old_base))
    return path


def generate_product_path(p: Pds4Product, path: str, superseded=False) -> str:
    product_dirname = os.path.dirname(path)
    filename = os.path.basename(path)
    if superseded and "SUPERSEDED" not in path:
        vid = p.label.identification_area.lidvid.vid
        return os.path.join(product_dirname, "SUPERSEDED", f'V{vid.major}_{vid.minor}', filename)
    return path
