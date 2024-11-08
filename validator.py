import pds4
import label
import labeltypes
from typing import Dict, Set, Iterable, List, Tuple

from lids import Lid, LidVid
import logging

logger = logging.getLogger(__name__)


class ValidationError:
    def __init__(self, message: str, fatal: bool = False):
        if fatal:
            logger.fatal(message)
        else:
            logger.error(message)
            
        self.message = message
        self.fatal = fatal


def check_bundle_against_previous(previous_bundle: pds4.BundleProduct, delta_bundle: pds4.BundleProduct) -> List[ValidationError]:
    """
    Performs bundle level checks, comparing the delta bundle to the previous bundle:
        * Compare the bundle version numbers
    """
    logger.info(f"Checking delta bundle label {delta_bundle.label.identification_area.lidvid} against previous bundle label {previous_bundle.label.identification_area.lidvid}")
    errors = []
    errors.extend(_check_modification_history(delta_bundle, previous_bundle))
    errors.extend(_check_bundle_increment(previous_bundle.label, delta_bundle.label))
    return errors


def check_bundle_against_collections(bundle: pds4.BundleProduct, collections: Iterable[pds4.CollectionProduct]) -> List[ValidationError]:
    """
    Compare the collections declared in the bundle to the collections that actually appear
    """
    logger.info(f"Checking bundle label {bundle.label.identification_area.lidvid} against existing collections")
    collection_lidvids = [x.label.identification_area.lidvid for x in collections]
    return _check_bundle_for_latest_collections(bundle.label, set(collection_lidvids))


def check_collection_against_previous(previous_collection: pds4.CollectionProduct, delta_collection: pds4.CollectionProduct) -> List[ValidationError]:
    """
    Compare the discovered collections in the delta bundle to the discovered collections in the previous bundle.
        * Compare the modification histories of any bundles that correspond
        * check that the version numbers are incremented correctly
        * check that any products in the delta collection inventory correctly supersede the products in the old inventory
        * check that products in the delta inventory do not duplicate the old inventory
    """
    logger.info(f"Checking delta product label {delta_collection.label.identification_area.lidvid} against previous product {previous_collection.label.identification_area.lidvid}")
    errors = []
    errors.extend(_check_modification_history(delta_collection, previous_collection))

    errors.extend(_check_collection_increment(previous_collection, delta_collection))
    errors.extend(_check_collection_duplicates(previous_collection, delta_collection))
    return errors


def _check_modification_history(delta_collection: pds4.Pds4Product, previous_collection: pds4.Pds4Product):
    logger.info(f"Checking delta collection label {delta_collection.label.identification_area.lidvid} against previous collection {previous_collection.label.identification_area.lidvid}")
    errors = []
    errors.extend(_check_for_modification_history(previous_collection.label))
    errors.extend(_check_for_modification_history(delta_collection.label))
    if not errors:
        errors.extend(_check_for_preserved_modification_history(previous_collection.label, delta_collection.label))
    return errors


def _check_collection_increment(previous_collection: pds4.CollectionProduct,
                                delta_collection: pds4.CollectionProduct) -> List[ValidationError]:
    """
    Ensure that the LIDVIDs for all the products in a collection have been correctly incremented
    """
    logger.info(f'Checking version increment for collection inventory members: {delta_collection.label.identification_area.lidvid}')
    errors = []
    errors.extend(_check_dict_increment(previous_collection.inventory.items, delta_collection.inventory.items))
    return errors


def _check_dict_increment(previous_lidvids: Dict[Lid, pds4.InventoryItem], delta_lidvids: Dict[Lid, pds4.InventoryItem]) -> List[ValidationError]:
    """
    Ensure that the supplied new LIDVIDs have been correctly incremented from the previous LIDVIDs
    """
    errors = []
    for lid in delta_lidvids.keys():
        if lid in previous_lidvids.keys():
            lidvid: LidVid = delta_lidvids[lid].lidvid
            previous_lidvid: LidVid = previous_lidvids[lid].lidvid
            errors.extend(_check_lidvid_increment(previous_lidvid, lidvid, same=False))
    return errors


def _check_bundle_increment(previous_bundle: label.ProductLabel, delta_bundle: label.ProductLabel) -> List[ValidationError]:
    """
    Check that the LIDVIDs of both the bundle and any declared bundle member entries have been incremented
    correctly.
    """
    logger.info(f'Checking version increment for {delta_bundle.identification_area.lidvid} against {previous_bundle.identification_area.lidvid}')
    errors = []

    previous_bundle_lidvid = previous_bundle.identification_area.lidvid
    delta_bundle_lidvid = delta_bundle.identification_area.lidvid
    errors.extend(_check_lidvid_increment(previous_bundle_lidvid, delta_bundle_lidvid, same=False))

    for x in previous_bundle.bundle_member_entries + delta_bundle.bundle_member_entries:
        if not x.livdid_reference:
            errors.append(ValidationError(x.lid_reference + " is referenced by lid instead of lidvid"))

    previous_collection_lidvids = [LidVid.parse(x.livdid_reference)
                        for x in previous_bundle.bundle_member_entries
                        if x.livdid_reference]
    delta_collection_lidvids = [LidVid.parse(x.livdid_reference)
                               for x in delta_bundle.bundle_member_entries
                               if x.livdid_reference]

    for next_collection_lidvid in delta_collection_lidvids:
        matching_lidvids = [x for x in previous_collection_lidvids if x.lid == next_collection_lidvid.lid]
        if matching_lidvids:
            matching_lidvid = matching_lidvids[0]
            errors.extend(_check_lidvid_increment(matching_lidvid, next_collection_lidvid))
        else:
            errors.append(ValidationError(f"{next_collection_lidvid} does not have a corresponding LidVid in the previous collection"))

    for previous_collection_lidvid in previous_collection_lidvids:
        matching_lidvids = [x for x in previous_collection_lidvids if x.lid == previous_collection_lidvid.lid]
        if not matching_lidvids:
            errors.append(ValidationError(f"{previous_collection_lidvid} does not have a corresponding LidVid in the new collection"))

    return errors

def _check_lidvid_increment(previous_lidvid: LidVid, delta_lidvid: LidVid, same=True, minor=True, major=True) -> List[ValidationError]:
    """
    Check that the provided new_lidvid is an allowable increment from the previous LIDVID.
    There are three possible ways to increment a LIDVID that we recognize:
        * Don't increment it at all
        * Increment the minor version number e.g 1.1 -> 1.2
        * Increment the major version number and reset the minor version number to 0 e.g. 1.1 -> 2.0
    Flags control which of these methods we allow at the moment
    """
    logger.info(f'Checking increment of {delta_lidvid} against {previous_lidvid}')
    errors = []
    allowed = ([previous_lidvid] if same else []) + \
              ([previous_lidvid.inc_minor()] if minor else []) + \
              ([previous_lidvid.inc_major()] if major else [])
    if delta_lidvid not in allowed:
        errors.append(ValidationError(f"Invalid lidvid: {delta_lidvid}. Must be one of {[x.__str__() for x in allowed]}"))
    return errors


def _check_collection_duplicates(previous_collection: pds4.CollectionProduct,
                                 delta_collection: pds4.CollectionProduct) -> List[ValidationError]:
    """
    Ensure that the new collection does not have products that match the old collection.
    Every product must be new or must supersede the old product
    """
    logger.info(f'Checking collection inventory for duplicate products: {delta_collection.label.identification_area.lidvid}')
    errors = []
    duplicates = delta_collection.inventory.products().intersection(previous_collection.inventory.products())
    if duplicates:
        errors.append(ValidationError(f'Collection had duplicate products: {", ".join(x.__str__() for x in duplicates)}'))
    return errors


def _check_for_modification_history(lbl: label.ProductLabel) -> List[ValidationError]:
    """
    Verify that the modification history for a product exists and is current
    """
    logger.info(f'Checking modification history for {lbl.identification_area.lidvid}')
    errors = []
    lidvid = lbl.identification_area.lidvid
    vid = lidvid.vid.__str__()
    if lbl.identification_area.modification_history is None:
        errors.append(ValidationError(f"{lidvid} does not have a modification history"))
    else:
        versions = [detail.version_id for detail in lbl.identification_area.modification_history.modification_details]
        if vid not in versions:
            errors.append(ValidationError(f'{lidvid} does not have a current modification history. Versions seen were: {versions}'))

    return errors

def _check_for_preserved_modification_history(previous_collection: label.ProductLabel,
                                              delta_collection: label.ProductLabel) -> List[ValidationError]:
    """
    Verify that all of the modification history entries that were in the old product are also in the new product
    """
    errors = []
    logger.info(f'Checking consistency of modification history for {delta_collection.identification_area.lidvid} against {previous_collection.identification_area.lidvid}')
    previous_details = previous_collection.identification_area.modification_history.modification_details
    delta_details = delta_collection.identification_area.modification_history.modification_details

    delta_lidvid = delta_collection.identification_area.lidvid
    prev_lidvid = previous_collection.identification_area.lidvid

    delta_vid = delta_lidvid.vid
    prev_vid = prev_lidvid.vid

    if len(delta_details) >= len(previous_details):
        pairs = zip(previous_details, delta_details[:len(previous_details)])
        for pair in pairs:
            errors.extend(_compare_modifcation_detail(pair, delta_lidvid, prev_lidvid))
    else:
        errors.append(ValidationError(f"{delta_lidvid} must contain at least as many modification details as {prev_lidvid}"))

    if delta_vid > prev_vid:
        if len(delta_details) != len(previous_details) + 1:
            errors.append(ValidationError(f"{delta_lidvid} must contain one more modification detail than {prev_lidvid}"))

    if delta_vid == prev_vid:
        if len(delta_details) != len(previous_details):
            errors.append(ValidationError(f"{delta_lidvid} must contain exactly as many modification details as {prev_lidvid}"))

    return errors


def _compare_modifcation_detail(pair: Tuple[labeltypes.ModificationDetail, labeltypes.ModificationDetail], delta_lidvid: LidVid, prev_lidvid: LidVid) -> List[ValidationError]:
    """
    Ensures that two corresponding modification detail entries are the same
    """
    errors = []
    previous_detail: labeltypes.ModificationDetail
    delta_detail: labeltypes.ModificationDetail
    previous_detail, delta_detail = pair
    if not previous_detail == delta_detail:
        errors.append(ValidationError(f'{delta_lidvid} has a mismatched modification detail from {prev_lidvid}. '
                                      f'The old modification detail was {previous_detail}, and the new one was {delta_detail}'))
    return errors


def _check_bundle_for_latest_collections(bundle: labeltypes.ProductLabel, collection_lidvids: Set[LidVid]) -> List[ValidationError]:
    """
    Ensure that the discovered collections and the declared collections match
    """
    logger.info(f'Checking collections references in {bundle.identification_area.lidvid}')
    errors = []
    bundle_member_lidvids = set(LidVid.parse(e.livdid_reference) for e in bundle.bundle_member_entries)
    bundle_lidvid = bundle.identification_area.lidvid
    if not collection_lidvids == bundle_member_lidvids:
        errors.append(ValidationError(f"{bundle_lidvid} does not contain the expected collection list: "
                        f"{','.join(x.__str__() for x in collection_lidvids)}"
                        f"Instead, it had: "
                        f"{','.join(x.__str__() for x in bundle_member_lidvids)}"))
    return errors
