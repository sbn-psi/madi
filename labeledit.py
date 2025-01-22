from typing import Iterable

from lxml import etree

from labeltypes import BundleMemberEntry


def inject_bundle_member_entries(labelpath: str, entries_to_add: Iterable[BundleMemberEntry]):
    xmldoc: etree = etree.parse(labelpath)
    bundle_member_entries = xmldoc.find("//Product_Bundle")

    for entry_to_add in entries_to_add:
        bundle_member_entries.append(_bundle_member_entry_to_element(entry_to_add))

    with open(labelpath, "w") as outfile:
        outfile.write(etree.tostring(xmldoc, method="xml", encoding="unicode"))


def _bundle_member_entry_to_element(entry: BundleMemberEntry):
    bundle_member_entry = etree.Element("Bundle_Member_Entry")

    bundle_member_entry.append(_text_element("lidvid_reference", entry.livdid_reference))
    bundle_member_entry.append(_text_element("member_status", entry.member_status))
    bundle_member_entry.append(_text_element("reference_type", entry.reference_type))

    return bundle_member_entry


def _text_element(name: str, value: str):
    elem = etree.Element(name)
    elem.text = value
    return elem
