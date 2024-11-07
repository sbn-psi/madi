import logging
import os
from typing import Iterable, List

from lids import Vid

logger = logging.getLogger(__name__)


def rebase_filenames(basepath: str, filenames: Iterable[str]) -> List[str]:
    """
    Puts all of the given file names under the given base path
    """
    return [os.path.join(basepath, filename) for filename in filenames]


def relocate_path(path: str, old_base: str, new_base: str) -> str:
    """Changes the base directory of a given path"""
    if path.startswith(old_base):
        return os.path.join(new_base, os.path.relpath(path, old_base))
    return path


def generate_product_path(path: str, superseded=False, vid: Vid = None) -> str:
    """
    Moves the given path into a versioned subdirectory when the path is for a superseded product.
    Does not change the path if this has already been done
    """
    product_dirname = os.path.dirname(path)
    filename = os.path.basename(path)
    if superseded and "SUPERSEDED" not in path:
        if vid is None:
            raise Exception("Vid must be specified when superseding a product for the first time")
        return os.path.join(product_dirname, "SUPERSEDED", f'v{vid.major}_{vid.minor}', filename)
    return path
