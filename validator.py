import pds4
import label
import pds4types
from typing import Dict, Set


def check_collection_increment(previous_collection: pds4.CollectionInventory,
                               next_collection: pds4.CollectionInventory):
    _check_dict_increment(previous_collection.primary, next_collection.primary)
    _check_dict_increment(previous_collection.secondary, next_collection.secondary)


def _check_dict_increment(previous_lidvids: Dict[pds4.Lid, pds4.LidVid], next_lidvids: Dict[pds4.Lid, pds4.LidVid]):
    for lid in next_lidvids.keys():
        if lid in previous_lidvids.keys():
            lidvid: pds4.LidVid = next_lidvids[lid]
            previous_lidvid: pds4.LidVid = previous_lidvids[lid]
            _check_lidvid_increment(previous_lidvid, lidvid, same=False)


def check_bundle_increment(previous_bundle: label.ProductLabel, next_bundle: label.ProductLabel):

    previous_bundle_lidvid = pds4.LidVid.parse(previous_bundle.identification_area.lidvid)
    next_bundle_lidvid = pds4.LidVid.parse(next_bundle.identification_area.lidvid)
    _check_lidvid_increment(previous_bundle_lidvid, next_bundle_lidvid, same=False)

    for x in previous_bundle.bundle_member_entries + next_bundle.bundle_member_entries:
        if not x.livdid_reference:
            raise Exception(x.lid_reference + " is referenced by lid instead of lidvid")

    previous_lidvids = [pds4.LidVid.parse(x.livdid_reference)
                        for x in previous_bundle.bundle_member_entries
                        if x.livdid_reference]
    next_lidvids = [pds4.LidVid.parse(x.livdid_reference)
                    for x in next_bundle.bundle_member_entries
                    if x.livdid_reference]

    for next_lidvid in next_lidvids:
        matching_lidvids = [x for x in previous_lidvids if x.lid == next_lidvid.lid]
        if len(matching_lidvids):
            matching_lidvid = matching_lidvids[0]
            _check_lidvid_increment(matching_lidvid, next_lidvid)
        else:
            raise Exception(f"{next_lidvid} does not have a corresponding LidVid in the previous collection")

    for previous_lidvid in previous_lidvids:
        matching_lidvids = [x for x in previous_lidvids if x.lid == previous_lidvid.lid]
        if not len(matching_lidvids):
            raise Exception(f"{previous_lidvid} does not have a corresponding LidVid in the new collection")


def _check_lidvid_increment(previous_lidvid: pds4.LidVid, next_lidvid: pds4.LidVid, same=True, minor=True, major=True):
    allowed = ([previous_lidvid] if same else []) + \
              ([previous_lidvid.inc_minor()] if minor else []) + \
              ([previous_lidvid.inc_major()] if major else [])
    if next_lidvid not in allowed:
        raise Exception(f"Invalid lidvid: {next_lidvid}. Must be one of {[x.__str__() for x in allowed]}")


def check_collection_duplicates(previous_collection: pds4.CollectionInventory,
                                next_collection: pds4.CollectionInventory):
    duplicates = next_collection.products().intersection(previous_collection.products())
    if len(duplicates):
        raise Exception(f'Collection had duplicate products: {", ".join(x.__str__() for x in duplicates)}')


def check_for_modification_history(lbl: label.ProductLabel):
    lidvid = pds4.LidVid.parse(lbl.identification_area.lidvid)
    vid = lidvid.vid.__str__()
    if lbl.identification_area.modification_history is None:
        raise Exception(f"{lidvid} does not have a modification history")

    versions = [detail.version_id for detail in lbl.identification_area.modification_history.modification_details]
    if vid not in versions:
        raise Exception(f'{lidvid} does not have a current modification history. Versions seen were: {versions}')


def check_for_preserved_modification_history(previous_collection: label.ProductLabel,
                                             next_collection: label.ProductLabel):
    previous_details = previous_collection.identification_area.modification_history.modification_details
    next_details = next_collection.identification_area.modification_history.modification_details

    next_lidvid = next_collection.identification_area.lidvid
    prev_lidvid = previous_collection.identification_area.lidvid

    next_vid = pds4.LidVid.parse(next_lidvid).vid
    prev_vid = pds4.LidVid.parse(prev_lidvid).vid

    if len(next_details) >= len(previous_details):
        pairs = zip(previous_details, next_details[:len(previous_details)])
        for pair in pairs:
            previous_detail: pds4types.ModificationDetail
            next_detail: pds4types.ModificationDetail
            previous_detail, next_detail = pair

            if not previous_detail == next_detail:
                raise Exception(f'{next_lidvid} has a mismatched modification detail from {prev_lidvid}. '
                                f'The old modification detail was {previous_detail}, and the new one was {next_detail}')
    else:
        raise Exception(f"{next_lidvid} must contain at least as many modification details as {prev_lidvid}")

    if next_vid > prev_vid:
        if not len(next_details) == len(previous_details) + 1:
            raise Exception(f"{next_lidvid} must contain one more modification detail than {prev_lidvid}")

    if next_vid == prev_vid:
        if not len(next_details) == len(previous_details):
            raise Exception(f"{next_lidvid} must contain exactly as many modification details as {prev_lidvid}")


def check_bundle_for_latest_collections(bundle: pds4types.ProductLabel, collection_lidvids: Set[pds4.LidVid]):
    bundle_member_lidvids = set(pds4.LidVid.parse(e.livdid_reference) for e in bundle.bundle_member_entries)
    bundle_lidvid = bundle.identification_area.lidvid
    if not collection_lidvids == bundle_member_lidvids:
        raise Exception(f"{bundle_lidvid} does not contain the expected collection list: "
                        f"{','.join(x.__str__() for x in collection_lidvids)}"
                        f"Instead, it had: "
                        f"{','.join(x.__str__() for x in bundle_member_lidvids)}")
