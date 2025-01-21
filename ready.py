import itertools
import operator
import typing
from typing import List

import pds4
import validator

import logging
logger = logging.getLogger(__name__)



def check_ready(previous_fullbundle: pds4.FullBundle, delta_fullbundle: pds4.FullBundle, jaxa: bool) -> None:
    previous_bundle_directory = previous_fullbundle.path
    delta_bundle_directory = delta_fullbundle.path

    logger.info(f"Checking readiness of delta bundle {delta_bundle_directory} against {previous_bundle_directory}")

    for bundle in previous_fullbundle.bundles:
        logger.info(f'Previous bundle checksum: {bundle.label.checksum}')

    for bundle in delta_fullbundle.bundles:
        logger.info(f'Delta bundle checksum: {bundle.label.checksum}')

    errors = do_checkready(previous_fullbundle, delta_fullbundle, jaxa)

    logger.info(f"Checking readiness of delta bundle {delta_bundle_directory} against {previous_bundle_directory} - Complete")

    if len(errors) > 0:
        summary_lines = "\n".join(
            f"  {severity} - {error_type}: {len(list(v))}" for ((severity, error_type), v) in itertools.groupby(errors, operator.attrgetter("severity", "error_type"))
        )
        logger.info(f"Error summary:\n{summary_lines}\nTotal: {len(errors)}")

        if any(e.severity == "error" for e in errors):
            raise Exception("Validation errors encountered")
    else:
        logger.info("No errors encountered")

def do_checkready(previous_fullbundle: pds4.FullBundle,
                  delta_fullbundle: pds4.FullBundle, jaxa: bool) -> List[validator.ValidationError]:
    errors = []
    errors.extend(validator.check_bundle_against_previous(previous_fullbundle.bundles[0], delta_fullbundle.bundles[0], jaxa))
    errors.extend(validator.check_bundle_against_collections(delta_fullbundle.bundles[0], delta_fullbundle.collections))

    for collection in delta_fullbundle.collections + previous_fullbundle.collections:
        errors.extend(validator.check_vid_presence(collection.inventory.products()))

    if not any(e.severity == "error" for e in errors):
        for delta_collection in delta_fullbundle.collections:
            new_collection_lid = delta_collection.label.identification_area.lidvid.lid
            previous_collections = [x for x in previous_fullbundle.collections if
                                    x.label.identification_area.lidvid.lid == new_collection_lid]
            if previous_collections:
                previous_collection = previous_collections[0]
                errors.extend(validator.check_collection_against_previous(previous_collection, delta_collection))

        errors.extend(validator.check_filename_consistency(previous_fullbundle.products, delta_fullbundle.products))

    return errors
