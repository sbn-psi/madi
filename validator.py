import operator

import pds4
import label
import labeltypes
import os.path
from typing import Dict, Set, Iterable, List, Tuple

from lids import Lid, LidVid
import logging

logger = logging.getLogger(__name__)


class ValidationError:
    def __init__(self, message: str, error_type: str, severity: str = "error"):
        if severity == "error":
            logger.error(message)
        elif severity == "warning":
            logger.warning(message)
        else:
            raise Exception("Unsupported severity")
            
        self.message = message
        self.error_type = error_type
        self.severity = severity


def check_bundle_against_previous(previous_bundle: pds4.BundleProduct, delta_bundle: pds4.BundleProduct, jaxa: bool, previous_collections: List[pds4.CollectionProduct]) -> List[ValidationError]:
    """
    Performs bundle level checks, comparing the delta bundle to the previous bundle:
        * Compare the bundle version numbers
    """
    logger.info(f"Checking delta bundle label {delta_bundle.lidvid()} against previous bundle label {previous_bundle.lidvid()}")
    errors = []
    errors.extend(_check_modification_history(previous_bundle, delta_bundle))
    errors.extend(_check_bundle_increment(previous_bundle.label, delta_bundle.label, jaxa, previous_collections))
    return errors


def check_bundle_against_collections(bundle: pds4.BundleProduct, collections: Iterable[pds4.CollectionProduct]) -> List[ValidationError]:
    """
    Compare the collections declared in the bundle to the collections that actually appear
    """
    logger.info(f"Checking bundle label {bundle.lidvid()} against existing collections")
    collection_lidvids = [x.lidvid() for x in collections]
    return _check_bundle_for_latest_collections(bundle.label, set(collection_lidvids))


def check_collection_against_previous(previous_collection: pds4.CollectionProduct, delta_collection: pds4.CollectionProduct) -> List[ValidationError]:
    """
    Compare the discovered collections in the delta bundle to the discovered collections in the previous bundle.
        * Compare the modification histories of any bundles that correspond
        * check that the version numbers are incremented correctly
        * check that any products in the delta collection inventory correctly supersede the products in the old inventory
        * check that products in the delta inventory do not duplicate the old inventory
    """
    logger.info(f"Checking delta product label {delta_collection.lidvid()} against previous product {previous_collection.lidvid()}")
    errors = []
    errors.extend(_check_modification_history(previous_collection, delta_collection))

    errors.extend(_check_collection_increment(previous_collection, delta_collection))
    errors.extend(_check_collection_duplicates(previous_collection, delta_collection))
    return errors


def _check_modification_history(previous_collection: pds4.Pds4Product, delta_collection: pds4.Pds4Product):
    logger.info(f"Checking delta collection label {delta_collection.lidvid()} against previous collection {previous_collection.lidvid()}")
    errors = []
    errors.extend(_check_for_modification_history(previous_collection.label))
    errors.extend(_check_for_modification_history(delta_collection.label))
    if not any(e.severity == "error" for e in errors):
        errors.extend(_check_for_preserved_modification_history(previous_collection.label, delta_collection.label))
    return errors


def _check_collection_increment(previous_collection: pds4.CollectionProduct,
                                delta_collection: pds4.CollectionProduct) -> List[ValidationError]:
    """
    Ensure that the LIDVIDs for all the products in a collection have been correctly incremented
    """
    logger.info(f'Checking version increment for collection inventory members: {delta_collection.lidvid()}')
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


def _check_bundle_increment(previous_bundle: label.ProductLabel, delta_bundle: label.ProductLabel, jaxa: bool, previous_collections: List[pds4.CollectionProduct]) -> List[ValidationError]:
    """
    Check that the LIDVIDs of both the bundle and any declared bundle member entries have been incremented
    correctly.
    """
    logger.info(f'Checking version increment for {delta_bundle.identification_area.lidvid} against {previous_bundle.identification_area.lidvid}')
    errors = []

    previous_bundle_lidvid = previous_bundle.identification_area.lidvid
    delta_bundle_lidvid = delta_bundle.identification_area.lidvid
    errors.extend(_check_lidvid_increment(previous_bundle_lidvid, delta_bundle_lidvid, same=False))

    # verify that all collections are referenced by vid
    for x in delta_bundle.bundle_member_entries:
        if not x.lidvid_reference:
            errors.append(ValidationError(x.lid_reference + " is referenced by lid instead of lidvid", "non_lidvid_reference"))

    patched_entries, issues = patch_bundle_member_entries(previous_bundle.bundle_member_entries, previous_collections)
    previous_collection_lidvids = [x.lidvid() for x in patched_entries]
    delta_collection_lidvids = [x.lidvid() for x in delta_bundle.bundle_member_entries]

    # ensure that any declared LIDVIDs actually have a VID component
    #errors.extend(check_vid_presence(previous_collection_lidvids))
    errors.extend(issues)
    errors.extend(check_vid_presence(delta_collection_lidvids))

    # verify that all non-new (> 1.0) collections in the delta bundle also exist in the previous bundle
    for next_collection_lidvid in delta_collection_lidvids:
        if next_collection_lidvid.vid.major > 1 or next_collection_lidvid.vid.minor > 0:
            matching_lidvids = [x for x in previous_collection_lidvids if x.lid == next_collection_lidvid.lid]
            if matching_lidvids:
                matching_lidvid = matching_lidvids[0]
                errors.extend(_check_lidvid_increment(matching_lidvid, next_collection_lidvid))
            else:
                errors.append(ValidationError(f"{next_collection_lidvid} does not have a corresponding LidVid in the previous bundle", "collection_missing_from_previous_bundle"))

    # verify that all collections in the previous bundle also exist in the delta bundle
    # this requirement has been waived for JAXA bundles
    if not jaxa:
        for previous_collection_lidvid in previous_collection_lidvids:
            matching_lidvids = [x for x in delta_collection_lidvids if x.lid == previous_collection_lidvid.lid]
            if not matching_lidvids:
                errors.append(ValidationError(f"{previous_collection_lidvid} does not have a corresponding LidVid in the delta bundle", "collection_missing_from_delta_bundle"))

    return errors

def patch_bundle_member_entries(entries: List[label.BundleMemberEntry], collections: List[pds4.CollectionProduct]) -> Tuple[List[label.BundleMemberEntry], List[ValidationError]]:
    result = []
    issues = []
    for entry in entries:
        if entry.lidvid_reference:
            result.append(entry)
        else:
            matching_collections = [x for x in collections if x.lidvid().lid == entry.lidvid().lid]
            if matching_collections:
                matching_collection = matching_collections[0]
                issues.append(ValidationError(f"Patched lid-reference bundle member f{entry.lid_reference} with collection LIDVID from label: {matching_collection.lidvid()}", "patched_lid_reference_with_collection_lidvid", "warning"))
                result.append(label.BundleMemberEntry(entry.member_status, entry.reference_type, None, str(matching_collection.lidvid())))
            else:
                issues.append(ValidationError(f"Encountered lid-reference bundle member f{entry.lid_reference}. No collection was available to lookup LID", "unpatchable_lid_reference", "warning"))
                result.append(entry)
    return result, issues

def check_vid_presence(lidvids: Iterable[LidVid]) -> Iterable[ValidationError]:
    """
    Checl that a LIDVID actually has a VID. The parser is tolerant, and will return a negative VID if one isn't supplied
    :param lidvids: A list of LIDVIDs
    :return: A list of validation errors
    """
    return (ValidationError(f"Vid not provided for {x.lid}", "missing_vid_From_lidvid") for x in lidvids if x.vid.major < 0 and x.lid.bundle != "context")


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
    if previous_lidvid.vid.major > 0:
        allowed = ([previous_lidvid] if same else []) + \
                  ([previous_lidvid.inc_minor()] if minor else []) + \
                  ([previous_lidvid.inc_major()] if major else [])
        if delta_lidvid not in allowed:
            errors.append(ValidationError(f"Invalid lidvid: {delta_lidvid}. Must be one of {[x.__str__() for x in allowed]}", "incorrectly_incremented_lidvid"))
    return errors


def _check_collection_duplicates(previous_collection: pds4.CollectionProduct,
                                 delta_collection: pds4.CollectionProduct) -> List[ValidationError]:
    """
    Ensure that the new collection does not have products that match the old collection.
    Every product must be new or must supersede the old product
    """
    logger.info(f'Checking collection inventory for duplicate products: {delta_collection.lidvid()}')
    errors = []
    duplicates = delta_collection.inventory.products().intersection(previous_collection.inventory.products())
    if duplicates:
        errors.append(ValidationError(f'Collection had duplicate products: {", ".join(x.__str__() for x in duplicates)}', "duplicate_products"))
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
        errors.append(ValidationError(f"{lidvid} does not have a modification history", "missing_modification_history"))
    else:
        versions = [detail.version_id for detail in lbl.identification_area.modification_history.modification_details]
        if vid not in versions:
            errors.append(ValidationError(f'{lidvid} does not have a current modification history. Versions seen were: {versions}', "missing_current_modification_detail"))

    return errors

def _check_for_preserved_modification_history(previous_collection: label.ProductLabel,
                                              delta_collection: label.ProductLabel) -> List[ValidationError]:
    """
    Verify that all of the modification history entries that were in the old product are also in the new product
    """
    errors = []
    logger.info(f'Checking consistency of modification history for {delta_collection.identification_area.lidvid} against {previous_collection.identification_area.lidvid}')

    previous_details = sorted(previous_collection.identification_area.modification_history.modification_details, key=operator.attrgetter("version_id"))
    delta_details = sorted(delta_collection.identification_area.modification_history.modification_details, key=operator.attrgetter("version_id"))

    delta_lidvid = delta_collection.identification_area.lidvid
    prev_lidvid = previous_collection.identification_area.lidvid

    delta_vid = delta_lidvid.vid
    prev_vid = prev_lidvid.vid

    if len(delta_details) >= len(previous_details):

        pairs = zip(previous_details, delta_details[:len(previous_details)])
        for pair in pairs:
            errors.extend(_compare_modifcation_detail(pair, prev_lidvid, delta_lidvid))
    else:
        errors.append(ValidationError(f"{delta_lidvid} must contain at least as many modification details as {prev_lidvid}", "not_enough_modification_details"))

    if delta_vid > prev_vid:
        if len(delta_details) != len(previous_details) + 1:
            errors.append(ValidationError(f"{delta_lidvid} must contain one more modification detail than {prev_lidvid}", "incorrect_modification_detail_count_for_superseding_product"))

    if delta_vid == prev_vid:
        if len(delta_details) != len(previous_details):
            errors.append(ValidationError(f"{delta_lidvid} must contain exactly as many modification details as {prev_lidvid}", "incorrect_modification_detail_count_for_non_superseding_product"))

    return errors


def _compare_modifcation_detail(pair: Tuple[labeltypes.ModificationDetail, labeltypes.ModificationDetail],
                                prev_lidvid: LidVid, delta_lidvid: LidVid) -> List[ValidationError]:
    """
    Ensures that two corresponding modification detail entries are the same
    """
    errors = []
    previous_detail: labeltypes.ModificationDetail
    delta_detail: labeltypes.ModificationDetail
    previous_detail, delta_detail = pair
    if not previous_detail == delta_detail:
        errors.append(ValidationError(f'{delta_lidvid} has a mismatched modification detail from {prev_lidvid}. '
                                      f'The old modification detail was {previous_detail}, and the new one was {delta_detail}', "mismatched_modification_detail"))
    return errors


def _check_bundle_for_latest_collections(bundle: labeltypes.ProductLabel, collection_lidvids: Set[LidVid]) -> List[ValidationError]:
    """
    Ensure that the discovered collections and the declared collections match
    """
    logger.info(f'Checking collections references in {bundle.identification_area.lidvid}')
    errors = []
    bundle_member_lidvids = set(e.lidvid() for e in bundle.bundle_member_entries)

    errors.extend(ValidationError(f"{c} not found in bundle member entry list", "collection_not_declared") for c in collection_lidvids - bundle_member_lidvids)
    errors.extend(ValidationError(f"{b} was declared, but no collection is present", "declared collection not found", "warning") for b in bundle_member_lidvids - collection_lidvids)

    return errors


def check_filename_consistency(previous_products: Iterable[pds4.BasicProduct], delta_products: Iterable[pds4.BasicProduct]) -> List[ValidationError]:
    errors = []
    previous_products_by_lid = dict((x.lidvid().lid, x) for x in previous_products)
    superseding_products = (x for x in delta_products if x.lidvid().vid.is_superseding())
    for delta_product in superseding_products:
        previous_product = previous_products_by_lid.get(delta_product.lidvid().lid)
        if previous_product:
            errors.extend(_do_check_filename_consistency(previous_product, delta_product))
        else:
            errors.append(ValidationError(f"Could not check filename consistency for {delta_product.lidvid()}. Previous product not found.", "previous_product_missing"))
    return errors


def _do_check_filename_consistency(previous_product: pds4.BasicProduct, delta_product: pds4.BasicProduct):
    errors = []
    previous_label_filename = os.path.basename(previous_product.label_path)
    delta_label_filename = os.path.basename(delta_product.label_path)

    if previous_label_filename != delta_label_filename:
        errors.append(ValidationError(
            f"New product has inconsistent label filename. Was: {previous_label_filename}, Now: {delta_label_filename}", "product_inconsistent_filenames"))
    else:
        logger.info(f"Label Filename check for {delta_product.lidvid()}: OK. Original Filename: {previous_label_filename}, Delta Filename: {delta_label_filename}")

    previous_data_filenames = set(os.path.basename(x) for x in previous_product.data_paths)
    delta_data_filenames = set(os.path.basename(x) for x in delta_product.data_paths)

    if previous_data_filenames != delta_data_filenames:
        errors.append(ValidationError(
            f"New product has inconsistent data filenames. Was: {','.join(previous_data_filenames)}, Now: {','.join(delta_data_filenames)}", "data_inconsistent_filename"))
    else:
        logger.info(f"Data filename check for {delta_product.lidvid()}: OK. Filenames: {','.join(delta_data_filenames)}")
    return errors
