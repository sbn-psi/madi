import localclient
import logging
import pds4

logger = logging.getLogger(__name__)


def load_local_bundle(path: str) -> pds4.FullBundle:
    """
    Loads a bundle located at the given path on the filesystsm
    """
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
    return pds4.FullBundle(path, bundles, superseded_bundles, collections, superseded_collections, products, superseded_products)


def is_basic(filepath: str) -> bool:
    """
    Determines if the product at the given path is a basic (non-collection or bundle) product.
    :param filepath:
    :return:
    """
    return not (is_collection(filepath) or is_bundle(filepath))


def is_collection(filepath: str) -> bool:
    """
    Determines if the product at the given path is a collection product
    :param filepath:
    :return:
    """
    return "collection" in filepath


def is_bundle(filepath: str) -> bool:
    """
    Determines if the product at the given path is a bundle product
    :param filepath:
    :return:
    """
    return "bundle" in filepath


def is_superseded(filepath: str) -> bool:
    """
    Determines if the product at the given path has been superseded
    :param filepath:
    :return:
    """
    return "SUPERSEDED" in filepath
