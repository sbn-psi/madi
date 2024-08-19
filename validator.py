import pds4
from typing import Dict


def check_collection_increment(previous: pds4.CollectionInventory, next: pds4.CollectionInventory):
    check_dict_increment(previous.primary, next.primary)
    check_dict_increment(previous.secondary, next.secondary)


def check_dict_increment(previous: Dict[pds4.Lid, pds4.LidVid], next: Dict[pds4.Lid, pds4.LidVid]):
    for lid in next.keys():
        if lid in previous.keys():
            lidvid: pds4.LidVid = next[lid]
            previous_lidvid: pds4.LidVid = previous[lid]
            allowed = (previous_lidvid.inc_major(), previous_lidvid.inc_minor())
            if lidvid not in allowed:
                raise Exception(f"Invalid lidvid: {lidvid}. Must be one of {allowed}")


