import localclient
import logging
import pds4

logger = logging.getLogger(__name__)

def load_local_bundle(path: str) -> pds4.FullBundle:
    logger.info(f'Loading bundle: {path}')
    filepaths = localclient.get_file_paths(path)
    label_paths = [x for x in filepaths if x.endswith(".xml")]

    collections = [localclient.fetchcollection(path)
                   for path in label_paths if is_collection(path) and not is_superseded(path)]
    bundles = [localclient.fetchbundle(path)
               for path in label_paths if is_bundle(path) and not is_superseded(path)]
    products = [localclient.fetchproduct(path) for path in label_paths if is_basic(path) and not is_superseded(path)]

    superseded_collections = [localclient.fetchcollection(path)
                              for path in label_paths if is_collection(path) and is_superseded(path)]
    superseded_bundles = [localclient.fetchbundle(path)
                          for path in label_paths if is_bundle(path) and is_superseded(path)]
    superseded_products = [localclient.fetchproduct(path)
                           for path in label_paths if is_basic(path) and is_superseded(path)]

    if len(bundles) == 0:
        raise Exception(f"Could not find bundle product in: {path}")
    return pds4.FullBundle(bundles, superseded_bundles, collections, superseded_collections, products, superseded_products)


def is_basic(x: str) -> bool:
    return not (is_collection(x) or is_bundle(x))


def is_collection(x: str) -> bool:
    return "collection" in x


def is_bundle(x: str) -> bool:
    return "bundle" in x


def is_superseded(x: str) -> bool:
    return "SUPERSEDED" in x
