from typing import List

import pds4
import validator

import logging
logger = logging.getLogger(__name__)



def check_ready(previous_fullbundle, new_fullbundle) -> None:
    previous_bundle_directory = previous_fullbundle.path
    new_bundle_directory = new_fullbundle.path

    logger.info(f"Checking readiness of new bundle {new_bundle_directory} against {previous_bundle_directory}")

    for bundle in previous_fullbundle.bundles:
        logger.info(f'Previous bundle checksum: {bundle.label.checksum}')

    for bundle in new_fullbundle.bundles:
        logger.info(f'New bundle checksum: {bundle.label.checksum}')

    errors = do_checkready(new_fullbundle, previous_fullbundle)

    logger.info(f"Checking readiness of new bundle {new_bundle_directory} against {previous_bundle_directory}")

    if len(errors) > 0:
        for e in errors:
            logger.error(e.message)
        raise Exception("Validation errors encountered")


def do_checkready(new_fullbundle: pds4.FullBundle, previous_fullbundle: pds4.FullBundle) -> List[validator.ValidationError]:
    errors = []
    errors.extend(validator.check_bundle_against_previous(previous_fullbundle.bundles[0], new_fullbundle.bundles[0]))
    errors.extend(validator.check_bundle_against_collections(new_fullbundle.bundles[0], new_fullbundle.collections))
    for new_collection in new_fullbundle.collections:
        new_collection_lid = new_collection.label.identification_area.lidvid.lid
        previous_collections = [x for x in previous_fullbundle.collections if
                                x.label.identification_area.lidvid.lid == new_collection_lid]
        if previous_collections:
            previous_collection = previous_collections[0]
            errors.extend(validator.check_collection_against_previous(previous_collection, new_collection))
    return errors