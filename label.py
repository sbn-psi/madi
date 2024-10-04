"""
Common code for label extraction
"""
import os
from typing import TypeVar, Callable

import bs4

import pds4
from labeltypes import DocumentFile, DocumentEdition, Document, SoftwareProgram, Software, Process, \
    ProcessingInformation, DisciplineArea, FileArea, TimeCoordinates, ContextArea, ModificationDetail, \
    ModificationHistory, IdentificationArea, ProductLabel, ObservingSystem, ObservingSystemComponent, \
    InternalReference, BundleMemberEntry


def extract_collection(collection: bs4.Tag, checksum: str) -> ProductLabel:
    """
    Extracts keywords from the Product_Collection element
    """
    return ProductLabel(
        checksum=checksum,
        identification_area=_extract_identification_area(collection.Identification_Area),
        context_area=_extract_context_area(collection.Context_Area),
        file_area=_extract_file_area(collection.File_Area_Inventory)
    )


def extract_bundle(bundle: bs4.Tag, checksum: str) -> ProductLabel:
    """
    Extracts keywords from the Product_Bundle element
    """
    return ProductLabel(
        checksum=checksum,
        identification_area=_extract_identification_area(bundle.Identification_Area),
        context_area=_extract_context_area(bundle.Context_Area),
        bundle_member_entries=[_extract_bundle_member_entry(x) for x in bundle.find_all("Bundle_Member_Entry")]
    )


def extract_product_observational(product_observational: bs4.Tag, checksum: str) -> ProductLabel:
    """
    Extracts keywords from the Product_Observational element
    """
    return ProductLabel(
        checksum=checksum,
        identification_area=_extract(product_observational.Identification_Area, _extract_identification_area),
        context_area=_extract(product_observational.Observation_Area, _extract_observation_area),
        discipline_area=_extract(product_observational.Discipline_Area, _extract_discipline_area),
        file_area=_extract_file_area(product_observational.File_Area_Observational)
    )


def extract_product_ancillary(product_ancillary: bs4.Tag, checksum: str) -> ProductLabel:
    """
    Extracts keywords from the Product_Observational element
    """
    return ProductLabel(
        checksum=checksum,
        identification_area=_extract(product_ancillary.Identification_Area, _extract_identification_area),
        context_area=_extract(product_ancillary.Context_Area, _extract_context_area),
        discipline_area=_extract(product_ancillary.Discipline_Area, _extract_discipline_area),
        file_area=_extract_file_area(product_ancillary.File_Area_Ancillary)
    )


def extract_product_document(product_document: bs4.Tag, checksum: str) -> ProductLabel:
    """
    Extracts keywords from the Product_Document element
    """
    return ProductLabel(
        checksum=checksum,
        identification_area=_extract(product_document.Identification_Area, _extract_identification_area),
        document=_extract(product_document.Document, _extract_document)
    )


def _extract_identification_area(identification_area: bs4.Tag) -> IdentificationArea:
    """
    Extracts keywords from the Identification_Area element
    """
    lid = _elemstr(identification_area.logical_identifier)
    vid = _elemstr(identification_area.version_id)
    modification_history = _extract(identification_area.Modification_History, _extract_modification_history)

    return IdentificationArea(
        lidvid=pds4.LidVid.assemble(lid, vid),
        collection_id=_extract_collection_id(lid),
        modification_history=modification_history
    )


def _extract_modification_history(modification_history: bs4.Tag) -> ModificationHistory:
    details = [_extract_modification_detail(d) for d in modification_history.find_all("Modification_Detail")]
    return ModificationHistory(details)


def _extract_modification_detail(modification_detail: bs4.Tag) -> ModificationDetail:
    return ModificationDetail(
        version_id=_elemstr(modification_detail.version_id),
        modification_date=_elemstr(modification_detail.modification_date),
        description=_elemstr(modification_detail.description)
    )


def _extract_observation_area(context_area: bs4.Tag) -> ContextArea:
    """
    Extract from the observation_area element
    """
    return ContextArea(
        time_coordinates=_extract(context_area.Time_Coordinates, _extract_time_coordinates),
        observing_system=_extract(context_area.Observing_System, _extract_observing_system)
    )


def _extract_observing_system(observing_system: bs4.Tag) -> ObservingSystem:
    """
    Extract from the Observing_System element
    """
    return ObservingSystem(
        components=[_extract_observing_system_component(component)
                    for component in observing_system.find_all("Observing_System_Component")]
    )


def _extract_observing_system_component(observing_system_component: bs4.Tag) -> ObservingSystemComponent:
    """
    Extract from the Observing_System_Component element
    """
    return ObservingSystemComponent(
        name=_elemstr(observing_system_component.find("name")),
        type=_elemstr(observing_system_component.type),
        internal_reference=_extract(observing_system_component.Internal_Reference, _extract_internal_reference)
    )


def _extract_internal_reference(internal_reference: bs4.Tag) -> InternalReference:
    """
    Extract from the Internal_Reference element
    """
    return InternalReference(
        lid_reference=_elemstr(internal_reference.lid_reference)
    )


def _extract_context_area(context_area: bs4.Tag) -> ContextArea:
    """
    Extract from the observation_area element
    """
    return ContextArea(
        time_coordinates=_extract(context_area.Time_Coordinates, _extract_time_coordinates),
        observing_system=_extract(context_area.Observing_System, _extract_observing_system)
    )


def _extract_time_coordinates(time_coordinates: bs4.Tag) -> TimeCoordinates:
    """
    gets the start and stop time from the time_coordinates element
    """
    return TimeCoordinates(
        start_date=_elemstr(time_coordinates.start_date_time),
        stop_date=_elemstr(time_coordinates.stop_date_time)
    )


def _extract_file_area(file_area: bs4.Tag) -> FileArea:
    """
    Extracts keywords from the File_Area element
    """
    return FileArea(os.path.basename(_elemstr(file_area.File.file_name)))


def _extract_collection_id(lid: str) -> str:
    """
    Extracts the collection id component from a LID
    """
    tokens = lid.split(':')
    return tokens[4] if len(tokens) > 4 else None


def _extract_discipline_area(discipline_area: bs4.Tag) -> DisciplineArea:
    """
    Extracts discipline information from the discipline area
    """
    return DisciplineArea(_extract(discipline_area.Processing_Information, _extract_processing_information))


def _extract_processing_information(processing_information: bs4.Tag) -> ProcessingInformation:
    """
    Extracts information from the processing area
    """
    return ProcessingInformation([_extract_process(process) for process in processing_information.find_all("Process")])


def _extract_process(process: bs4.Tag) -> Process:
    """
    Extract from the process element
    """
    return Process(
        name=_elemstr(process.find("name")),
        description=_elemstr(process.description, ''),
        software=[_extract_software(software) for software in process.find_all("Software")]
    )


def _extract_software(software: bs4.Tag) -> Software:
    """
    Extract from the software element
    """
    return Software(
        software_id=_elemstr(software.software_id, ''),
        software_version_id=_elemstr(software.software_version_id, ''),
        software_program=[_extract_software_program(software_program)
                          for software_program in software.find_all("Software_Program")]
    )


def _extract_software_program(software_program: bs4.Tag) -> SoftwareProgram:
    """
    Extract from the software element
    """
    return SoftwareProgram(
        name=_elemstr(software_program.find("name"), ''),
        program_version=_elemstr(software_program.program_version, '')
    )


def _extract_document(document: bs4.Tag) -> Document:
    """
    Extracts keywords form the Document element
    """
    editions = [_extract_document_edition(edition) for edition in document.find_all("Document_Edition")]
    return Document(editions)


def _extract_document_edition(document_edition: bs4.Tag) -> DocumentEdition:
    """
    Extracts keywords form the Document_Edition element
    """
    files = [_extract_document_file(document_file) for document_file in document_edition.find_all("Document_File")]
    return DocumentEdition(files)


def _extract_document_file(document_file: bs4.Tag) -> DocumentFile:
    """
    Extracts keywords form the Document_File element
    """
    return DocumentFile(_elemstr(document_file.file_name))


def _extract_bundle_member_entry(bundle_member_entry: bs4.Tag) -> BundleMemberEntry:
    return BundleMemberEntry(
        _elemstr(bundle_member_entry.member_status),
        _elemstr(bundle_member_entry.reference_type),
        _elemstr(bundle_member_entry.lid_reference),
        _elemstr(bundle_member_entry.lidvid_reference)
    )


def _optstr(value: str, default: str = None) -> str:
    """Extracts a value from a navigable string"""
    return str(value) if value else default


def _elemstr(elem: bs4.Tag, default: str = None) -> str:
    """Extracts a value from a tag"""
    return _optstr(elem.string, default) if elem else default


T = TypeVar("T")


def _extract(elem: bs4.Tag, func: Callable[[bs4.Tag], T], default=None) -> T:
    return func(elem) if elem else default
