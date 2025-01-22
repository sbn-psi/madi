from typing import Iterable

from lxml import etree

from labeltypes import BundleMemberEntry


def inject_bundle_member_entries(labelpath: str, entries_to_add: Iterable[BundleMemberEntry]):
    xmldoc: etree = etree.parse(labelpath)
    bundle_member_entries = xmldoc.find("//Bundle_Member_Entries")

    for entry_to_add in entries_to_add:
        bundle_member_entries.append(_bundle_member_entry_to_element(entry_to_add))

    with open(labelpath, "w") as outfile:
        outfile.write(etree.tostring(xmldoc, method="xml", encoding="unicode"))


def _bundle_member_entry_to_element(entry: BundleMemberEntry):
    bundle_member_entry = etree.Element("Bundle_Member_Entry")

    lidvid_reference = etree.Element("lidvid_reference")
    lidvid_reference.text = entry.livdid_reference
    bundle_member_entry.append(lidvid_reference)

    member_status = etree.Element("member_status")
    member_status.text = entry.member_status
    bundle_member_entry.append(member_status)

    return bundle_member_entry
