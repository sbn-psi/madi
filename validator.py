import pds4
import label
import pds4types
from typing import Dict, Set


def check_collection_increment(previous: pds4.CollectionInventory, next: pds4.CollectionInventory):
    _check_dict_increment(previous.primary, next.primary)
    _check_dict_increment(previous.secondary, next.secondary)


def _check_dict_increment(previous: Dict[pds4.Lid, pds4.LidVid], next: Dict[pds4.Lid, pds4.LidVid]):
    for lid in next.keys():
        if lid in previous.keys():
            lidvid: pds4.LidVid = next[lid]
            previous_lidvid: pds4.LidVid = previous[lid]
            allowed = (previous_lidvid.inc_major(), previous_lidvid.inc_minor())
            if lidvid not in allowed:
                raise Exception(f"Invalid lidvid: {lidvid}. Must be one of {allowed}")


def check_for_modification_history(lbl: label.ProductLabel):
    lidvid = pds4.LidVid.parse(lbl.identification_area.lidvid)
    vid = lidvid.vid.__str__()
    if lbl.identification_area.modification_history is None:
        raise Exception(f"{lidvid} does not have a modification history")

    versions = [detail.version_id for detail in lbl.identification_area.modification_history.modification_details]
    if vid not in versions:
        raise Exception(f'{lidvid} does not have a current modification history. Versions seen were: {versions}')


def check_for_modification_history(previous: label.ProductLabel, next: label.ProductLabel):
    previous_details = previous.identification_area.modification_history.modification_details
    next_details = next.identification_area.modification_history.modification_details

    next_lidvid = next.identification_area.lidvid
    prev_lidvid = previous.identification_area.lidvid

    if len(next_details) == len(previous_details) + 1:
        pairs = zip(previous_details, next_details[:len(previous_details)])
        for pair in pairs:
            previous_detail: pds4types.ModificationDetail
            next_detail: pds4types.ModificationDetail
            previous_detail, next_detail = pair

            if not previous_detail == next_detail:
                raise Exception(f'{next_lidvid} has a mismatched modification detail from {prev_lidvid}. The old modification detail was {previous_detail}, and the new one was {next_detail}')
    else:
        raise Exception(f"{next_lidvid} must contain one more modification detail than {prev_lidvid}")

def check_bundle_for_latest_collections(bundle: pds4types.ProductLabel, collection_lidvids: Set[pds4.LidVid]):
    bundle_member_lidvids = set(e.livdid_reference for e in bundle.bundle_member_entries)
    bundle_lidvid = bundle.identification_area.lidvid
    if not collection_lidvids == bundle_member_lidvids:
        raise Exception(f"{}")
