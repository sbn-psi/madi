import pds4
import label
import labeltypes
from typing import Dict, Set, Iterable, List

from lids import Lid, LidVid
import logging

logger = logging.getLogger(__name__)


class ValidationError:
    def __init__(self, message: str, fatal: bool = False):
        self.message = message
        self.fatal = fatal


def check_bundle_against_previous(previous_bundle: pds4.BundleProduct, new_bundle: pds4.BundleProduct) -> List[ValidationError]:
    logger.info(f"Checking new bundle label {new_bundle.label.identification_area.lidvid} against previous bundle label {previous_bundle.label.identification_area.lidvid}")
    return _check_bundle_increment(previous_bundle.label, new_bundle.label)


def check_bundle_against_collections(bundle: pds4.BundleProduct, collections: Iterable[pds4.CollectionProduct]) -> List[ValidationError]:
    logger.info(f"Checking bundle label {bundle.label.identification_area.lidvid} against existing collections")
    collection_lidvids = [x.label.identification_area.lidvid for x in collections]
    return _check_bundle_for_latest_collections(bundle.label, set(collection_lidvids))


def check_collection_against_previous(previous_collection: pds4.CollectionProduct, new_collection: pds4.CollectionProduct) -> List[ValidationError]:
    logger.info(f"Checking new collection label {new_collection.label.identification_area.lidvid} against previous collection {previous_collection.label.identification_area.lidvid}")
    errors = []
    errors.extend(_check_for_modification_history(previous_collection.label))
    errors.extend(_check_for_modification_history(new_collection.label))
    if len(errors) == 0:
        errors.extend(_check_for_preserved_modification_history(previous_collection.label, new_collection.label))

    errors.extend(_check_collection_increment(previous_collection.inventory, new_collection.inventory))
    errors.extend(_check_collection_duplicates(previous_collection.inventory, new_collection.inventory))
    return errors


def _check_collection_increment(previous_collection: pds4.CollectionInventory,
                                next_collection: pds4.CollectionInventory) -> List[ValidationError]:
    logger.info(f'Checking version increment for collection inventory members')
    errors = []
    errors.extend(_check_dict_increment(previous_collection.primary, next_collection.primary))
    errors.extend(_check_dict_increment(previous_collection.secondary, next_collection.secondary))
    return errors

def _check_dict_increment(previous_lidvids: Dict[Lid, LidVid], next_lidvids: Dict[Lid, LidVid]) -> List[ValidationError]:
    errors = []
    for lid in next_lidvids.keys():
        if lid in previous_lidvids.keys():
            lidvid: LidVid = next_lidvids[lid]
            previous_lidvid: LidVid = previous_lidvids[lid]
            errors.extend(_check_lidvid_increment(previous_lidvid, lidvid, same=False))
    return errors


def _check_bundle_increment(previous_bundle: label.ProductLabel, next_bundle: label.ProductLabel) -> List[ValidationError]:
    logger.info(f'Checking version increment for {next_bundle.identification_area.lidvid} against {previous_bundle.identification_area.lidvid}')
    errors = []

    previous_bundle_lidvid = previous_bundle.identification_area.lidvid
    next_bundle_lidvid = next_bundle.identification_area.lidvid
    errors.extend(_check_lidvid_increment(previous_bundle_lidvid, next_bundle_lidvid, same=False))

    for x in previous_bundle.bundle_member_entries + next_bundle.bundle_member_entries:
        if not x.livdid_reference:
            errors.append(ValidationError(x.lid_reference + " is referenced by lid instead of lidvid"))

    previous_lidvids = [LidVid.parse(x.livdid_reference)
                        for x in previous_bundle.bundle_member_entries
                        if x.livdid_reference]
    next_lidvids = [LidVid.parse(x.livdid_reference)
                    for x in next_bundle.bundle_member_entries
                    if x.livdid_reference]

    for next_lidvid in next_lidvids:
        matching_lidvids = [x for x in previous_lidvids if x.lid == next_lidvid.lid]
        if len(matching_lidvids):
            matching_lidvid = matching_lidvids[0]
            errors.extend(_check_lidvid_increment(matching_lidvid, next_lidvid))
        else:
            errors.append(ValidationError(f"{next_lidvid} does not have a corresponding LidVid in the previous collection"))

    for previous_lidvid in previous_lidvids:
        matching_lidvids = [x for x in previous_lidvids if x.lid == previous_lidvid.lid]
        if not len(matching_lidvids):
            errors.append(ValidationError(f"{previous_lidvid} does not have a corresponding LidVid in the new collection"))

    return errors

def _check_lidvid_increment(previous_lidvid: LidVid, next_lidvid: LidVid, same=True, minor=True, major=True) -> List[ValidationError]:
    logger.info(f'Checking increment of {next_lidvid} against {previous_lidvid}')
    errors = []
    allowed = ([previous_lidvid] if same else []) + \
              ([previous_lidvid.inc_minor()] if minor else []) + \
              ([previous_lidvid.inc_major()] if major else [])
    if next_lidvid not in allowed:
        errors.append(ValidationError(f"Invalid lidvid: {next_lidvid}. Must be one of {[x.__str__() for x in allowed]}"))
    return errors


def _check_collection_duplicates(previous_collection: pds4.CollectionInventory,
                                 next_collection: pds4.CollectionInventory) -> List[ValidationError]:
    logger.info(f'Checking collection inventory for duplicate products')
    errors = []
    duplicates = next_collection.products().intersection(previous_collection.products())
    if len(duplicates):
        errors.append(ValidationError(f'Collection had duplicate products: {", ".join(x.__str__() for x in duplicates)}'))
    return errors


def _check_for_modification_history(lbl: label.ProductLabel) -> List[ValidationError]:
    logger.info(f'Checking modification history for {lbl.identification_area.lidvid}')
    errors = []
    lidvid = lbl.identification_area.lidvid
    vid = lidvid.vid.__str__()
    if lbl.identification_area.modification_history is None:
        errors.append(ValidationError(f"{lidvid} does not have a modification history"))

    versions = [detail.version_id for detail in lbl.identification_area.modification_history.modification_details]
    if vid not in versions:
        errors.append(ValidationError(f'{lidvid} does not have a current modification history. Versions seen were: {versions}'))

    return errors

def _check_for_preserved_modification_history(previous_collection: label.ProductLabel,
                                              next_collection: label.ProductLabel) -> List[ValidationError]:
    errors = []
    logger.info(f'Checking consistency of modification history for {next_collection.identification_area.lidvid} against {previous_collection.identification_area.lidvid}')
    previous_details = previous_collection.identification_area.modification_history.modification_details
    next_details = next_collection.identification_area.modification_history.modification_details

    next_lidvid = next_collection.identification_area.lidvid
    prev_lidvid = previous_collection.identification_area.lidvid

    next_vid = next_lidvid.vid
    prev_vid = prev_lidvid.vid

    if len(next_details) >= len(previous_details):
        pairs = zip(previous_details, next_details[:len(previous_details)])
        for pair in pairs:
            previous_detail: labeltypes.ModificationDetail
            next_detail: labeltypes.ModificationDetail
            previous_detail, next_detail = pair

            if not previous_detail == next_detail:
                errors.append(ValidationError(f'{next_lidvid} has a mismatched modification detail from {prev_lidvid}. '
                                f'The old modification detail was {previous_detail}, and the new one was {next_detail}'))
    else:
        errors.append(ValidationError(f"{next_lidvid} must contain at least as many modification details as {prev_lidvid}"))

    if next_vid > prev_vid:
        if not len(next_details) == len(previous_details) + 1:
            errors.append(ValidationError(f"{next_lidvid} must contain one more modification detail than {prev_lidvid}"))

    if next_vid == prev_vid:
        if not len(next_details) == len(previous_details):
            errors.append(ValidationError(f"{next_lidvid} must contain exactly as many modification details as {prev_lidvid}"))

    return errors


def _check_bundle_for_latest_collections(bundle: labeltypes.ProductLabel, collection_lidvids: Set[LidVid]) -> List[ValidationError]:
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
