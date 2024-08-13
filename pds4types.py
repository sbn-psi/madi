import itertools
from dataclasses import dataclass
from typing import Optional, Iterable


@dataclass()
class DocumentFile:
    filename: str


@dataclass()
class DocumentEdition:
    files: list[DocumentFile]

    def filenames(self) -> Iterable[str]:
        return (f.filename for f in self.files)


@dataclass()
class Document:
    editions: list[DocumentEdition]

    def filenames(self) -> Iterable[str]:
        return itertools.chain.from_iterable(e.filenames() for e in self.editions)


@dataclass()
class SoftwareProgram:
    name: str
    program_version: str


@dataclass()
class Software:
    software_id: str
    software_version_id: str
    software_program: list[SoftwareProgram]


@dataclass()
class Process:
    name: str
    description: str
    software: list[Software]


@dataclass()
class ProcessingInformation:
    process: list[Process]


@dataclass()
class DisciplineArea:
    processing_information: ProcessingInformation


@dataclass()
class FileArea:
    file_name: str


@dataclass
class TimeCoordinates:
    start_date: str
    stop_date: str


@dataclass()
class InternalReference:
    lid_reference: str


@dataclass()
class ObservingSystemComponent:
    name: str
    type: str
    internal_reference: Optional[InternalReference]


@dataclass()
class ObservingSystem:
    components: list[ObservingSystemComponent]


@dataclass()
class ContextArea:
    time_coordinates: TimeCoordinates
    observing_system: Optional[ObservingSystem]


@dataclass()
class ObservationArea:
    time_coordinates: TimeCoordinates


@dataclass()
class ModificationDetail:
    version_id: str
    modification_date: str
    description: str


@dataclass
class ModificationHistory:
    modification_details: list[ModificationDetail]


@dataclass()
class IdentificationArea:
    logical_id: str
    collection_id: str
    version_id: str
    lidvid: str
    major: int
    minor: int
    modification_history: ModificationHistory


@dataclass()
class ProductLabel:
    identification_area: IdentificationArea = None
    file_area: Optional[FileArea] = None
    context_area: Optional[ContextArea] = None
    discipline_area: Optional[DisciplineArea] = None
    document: Optional[Document] = None


@dataclass()
class CollectionLabel:
    identification_area: IdentificationArea
    context_area: ContextArea
