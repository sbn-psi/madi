from typing import Iterable

from bs4 import BeautifulSoup

from labeltypes import BundleMemberEntry


def inject_bundle_member_entries(labelpath: str, entries_to_add: Iterable[BundleMemberEntry]):
    with open(labelpath) as in_f:
        xmldoc = BeautifulSoup(in_f, "lxml-xml")
    bundle_member_entries = xmldoc.find("Bundle_Member_Entries")

    bundle_member_entries.extend(
        _bundle_member_entry_to_element(x, xmldoc) for x in entries_to_add
    )

    with open(labelpath, "w") as out_f:
        out_f.write(xmldoc.prettify())


def _bundle_member_entry_to_element(entry: BundleMemberEntry, xmldoc: BeautifulSoup):
    bundle_member_entry = xmldoc.new_tag("Bundle_Member_Entry")

    lidvid_reference = xmldoc.new_tag("lidvid_reference")
    lidvid_reference.string = entry.livdid_reference
    bundle_member_entry.append(lidvid_reference)

    member_status = xmldoc.new_tag("member_status")
    member_status.string = entry.member_status
    bundle_member_entry.append(member_status)

    return bundle_member_entry
