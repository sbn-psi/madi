from typing import List

import pds4
import validator

import logging
logger = logging.getLogger(__name__)



def check_ready(previous_fullbundle, delta_fullbundle) -> None:
    previous_bundle_directory = previous_fullbundle.path
    delta_bundle_directory = delta_fullbundle.path

    logger.info(f"Checking readiness of delta bundle {delta_bundle_directory} against {previous_bundle_directory}")

    for bundle in previous_fullbundle.bundles:
        logger.info(f'Previous bundle checksum: {bundle.label.checksum}')

    for bundle in delta_fullbundle.bundles:
        logger.info(f'Delta bundle checksum: {bundle.label.checksum}')

    errors = do_checkready(previous_fullbundle, delta_fullbundle)

    logger.info(f"Checking readiness of delta bundle {delta_bundle_directory} against {previous_bundle_directory} - Complete")

    if len(errors) > 0:
        for e in errors:
            logger.error(e.message)
        raise Exception("Validation errors encountered")


def do_checkready(previous_fullbundle: pds4.FullBundle,
                  delta_fullbundle: pds4.FullBundle) -> List[validator.ValidationError]:
    errors = []
    errors.extend(validator.check_bundle_against_previous(previous_fullbundle.bundles[0], delta_fullbundle.bundles[0]))
    errors.extend(validator.check_bundle_against_collections(delta_fullbundle.bundles[0], delta_fullbundle.collections))

    for delta_collection in delta_fullbundle.collections:
        new_collection_lid = delta_collection.label.identification_area.lidvid.lid
        previous_collections = [x for x in previous_fullbundle.collections if
                                x.label.identification_area.lidvid.lid == new_collection_lid]
        if previous_collections:
            previous_collection = previous_collections[0]
            errors.extend(validator.check_collection_against_previous(previous_collection, delta_collection))

    errors.extend(validator.check_filename_consistency(previous_fullbundle.products, delta_fullbundle.products))

    return errors
