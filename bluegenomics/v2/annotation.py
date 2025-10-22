"""
Annotation - Class for managing genome annotation data (GTF/GFF files)
"""

from pathlib import Path
from typing import Union
from .data_object import DataObject

ANNOTATION_TYPE = "annotation"


class Annotation(DataObject):
    """
    Represents genome annotation data in GTF or GFF format.
    """

    def __init__(self, path: Union[str, Path]):
        super().__init__(path)

    def annotation_file(self) -> Path:
        """Get the annotation file (GTF/GFF)"""
        try:
            return self.files(type_=ANNOTATION_TYPE)
        except FileNotFoundError:
            return self.files()
