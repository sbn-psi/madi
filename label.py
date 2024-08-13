"""
Common code for label extraction
"""
import os
from typing import TypeVar, Callable

import bs4

from pds4types import DocumentFile, DocumentEdition, Document, SoftwareProgram, Software, Process, \
    ProcessingInformation, DisciplineArea, FileArea, TimeCoordinates, ContextArea, ModificationDetail, \
    ModificationHistory, IdentificationArea, ProductLabel, CollectionLabel, ObservingSystem, ObservingSystemComponent, \
    InternalReference


def extract_collection(collection: bs4.Tag) -> ProductLabel:
    """
    Extracts keywords from the Product_Collection element
    """
    return ProductLabel(
        identification_area=extract_identification_area(collection.Identification_Area),
        context_area=extract_context_area(collection.Context_Area)
    )


def extract_bundle(bundle: bs4.Tag) -> ProductLabel:
    """
    Extracts keywords from the Product_Bundle element
    """
    return ProductLabel(
        identification_area=extract_identification_area(bundle.Identification_Area),
        context_area=extract_context_area(bundle.Context_Area)
    )


def extract_product_observational(product_observational: bs4.Tag) -> ProductLabel:
    """
    Extracts keywords from the Product_Observational element
    """
    return ProductLabel(
        identification_area=extract(product_observational.Identification_Area, extract_identification_area),
        context_area=extract(product_observational.Observation_Area, extract_observation_area),
        discipline_area=extract(product_observational.Discipline_Area, extract_discipline_area),
        file_area=extract_file_area(product_observational.File_Area_Observational)
    )


def extract_product_ancillary(product_ancillary: bs4.Tag) -> ProductLabel:
    """
    Extracts keywords from the Product_Observational element
    """
    return ProductLabel(
        identification_area=extract(product_ancillary.Identification_Area, extract_identification_area),
        context_area=extract(product_ancillary.Context_Area, extract_context_area),
        discipline_area=extract(product_ancillary.Discipline_Area, extract_discipline_area),
        file_area=extract_file_area(product_ancillary.File_Area_Ancillary)
    )


def extract_product_document(product_document: bs4.Tag) -> ProductLabel:
    """
    Extracts keywords from the Product_Document element
    """
    return ProductLabel(
        identification_area=extract(product_document.Identification_Area, extract_identification_area),
        document=extract(product_document.Document, extract_document)
    )


def extract_identification_area(identification_area: bs4.Tag) -> IdentificationArea:
    """
    Extracts keywords from the Identification_Area element
    """
    lid = elemstr(identification_area.logical_identifier)
    vid = elemstr(identification_area.version_id)
    modification_history = extract(identification_area.Modification_History, extract_modification_history)

    major, minor = [int(x) for x in vid.split(".")]

    return IdentificationArea(
        logical_id=lid,
        collection_id=extract_collection_id(lid),
        version_id=vid,
        lidvid=f"{lid}::{vid}",
        major=major,
        minor=minor,
        modification_history=modification_history
    )


def extract_modification_history(modification_history: bs4.Tag) -> ModificationHistory:
    details = [extract_modification_detail(d) for d in modification_history.find_all("Modification_Detail")]
    return ModificationHistory(details)


def extract_modification_detail(modification_detail: bs4.Tag) -> ModificationDetail:
    return ModificationDetail(
        version_id=elemstr(modification_detail.version_id),
        modification_date=elemstr(modification_detail.modification_date),
        description=elemstr(modification_detail.description)
    )


def extract_observation_area(context_area: bs4.Tag) -> ContextArea:
    """
    Extract from the observation_area element
    """
    return ContextArea(
        time_coordinates=extract(context_area.Time_Coordinates, extract_time_coordinates),
        observing_system=extract(context_area.Observing_System, extract_observing_system)
    )


def extract_observing_system(observing_system: bs4.Tag) -> ObservingSystem:
    """
    Extract from the Observing_System element
    """
    return ObservingSystem(
        components=[extract_observing_system_component(component)
                    for component in observing_system.find_all("Observing_System_Component")]
    )


def extract_observing_system_component(observing_system_component: bs4.Tag) -> ObservingSystemComponent:
    """
    Extract from the Observing_System_Component element
    """
    return ObservingSystemComponent(
        name=elemstr(observing_system_component.find("name")),
        type=elemstr(observing_system_component.type),
        internal_reference=extract(observing_system_component.Internal_Reference, extract_internal_reference)
    )


def extract_internal_reference(internal_reference: bs4.Tag) -> InternalReference:
    """
    Extract from the Internal_Reference element
    """
    return InternalReference(
        lid_reference=elemstr(internal_reference.lid_reference)
    )


def extract_context_area(context_area: bs4.Tag) -> ContextArea:
    """
    Extract from the observation_area element
    """
    return ContextArea(
        time_coordinates=extract(context_area.Time_Coordinates, extract_time_coordinates),
        observing_system=extract(context_area.Observing_System, extract_observing_system)
    )


def extract_time_coordinates(time_coordinates: bs4.Tag) -> TimeCoordinates:
    """
    gets the start and stop time from the time_coordinates element
    """
    return TimeCoordinates(
        start_date=elemstr(time_coordinates.start_date_time),
        stop_date=elemstr(time_coordinates.stop_date_time)
    )


def extract_file_area(file_area: bs4.Tag) -> FileArea:
    """
    Extracts keywords from the File_Area element
    """
    return FileArea(os.path.basename(elemstr(file_area.File.file_name)))


def extract_collection_id(lid: str) -> str:
    """
    Extracts the collection id component from a LID
    """
    tokens = lid.split(':')
    return tokens[4] if len(tokens) > 4 else None


def extract_discipline_area(discipline_area: bs4.Tag) -> DisciplineArea:
    """
    Extracts discipline information from the discipline area
    """
    return DisciplineArea(extract(discipline_area.Processing_Information, extract_processing_information))


def extract_processing_information(processing_information: bs4.Tag) -> ProcessingInformation:
    """
    Extracts information from the processing area
    """
    return ProcessingInformation([extract_process(process) for process in processing_information.find_all("Process")])


def extract_process(process: bs4.Tag) -> Process:
    """
    Extract from the process element
    """
    return Process(
        name=elemstr(process.find("name")),
        description=elemstr(process.description, ''),
        software=[extract_software(software) for software in process.find_all("Software")]
    )


def extract_software(software: bs4.Tag) -> Software:
    """
    Extract from the software element
    """
    return Software(
        software_id=elemstr(software.software_id, ''),
        software_version_id=elemstr(software.software_version_id, ''),
        software_program=[extract_software_program(software_program)
                          for software_program in software.find_all("Software_Program")]
    )


def extract_software_program(software_program: bs4.Tag) -> SoftwareProgram:
    """
    Extract from the software element
    """
    return SoftwareProgram(
        name=elemstr(software_program.find("name"), ''),
        program_version=elemstr(software_program.program_version, '')
    )


def extract_document(document: bs4.Tag) -> Document:
    """
    Extracts keywords form the Document element
    """
    editions = [extract_document_edition(edition) for edition in document.find_all("Document_Edition")]
    return Document(editions)


def extract_document_edition(document_edition: bs4.Tag) -> DocumentEdition:
    """
    Extracts keywords form the Document_Edition element
    """
    files = [extract_document_file(document_file) for document_file in document_edition.find_all("Document_File")]
    return DocumentEdition(files)


def extract_document_file(document_file: bs4.Tag) -> DocumentFile:
    """
    Extracts keywords form the Document_File element
    """
    return DocumentFile(elemstr(document_file.file_name))


def optstr(value: str, default: str = None) -> str:
    """Extracts a value from a navigable string"""
    return str(value) if value else default


def elemstr(elem: bs4.Tag, default: str = None) -> str:
    """Extracts a value from a tag"""
    return optstr(elem.string, default) if elem else default


T = TypeVar("T")


def extract(elem: bs4.Tag, func: Callable[[bs4.Tag], T], default=None) -> T:
    return func(elem) if elem else default
