"""
GenomeIndex - Class for managing genome index files (e.g., BWA index)
"""

from pathlib import Path
from typing import Union
from .data_object import DataObject


class GenomeIndex(DataObject):
    """
    Represents an indexed genome for use with alignment tools like BWA.
    """

    def __init__(self, path: Union[str, Path]):
        super().__init__(path)

    def index_files(self) -> list:
        """Get all index files"""
        try:
            return self.files(as_list=True)
        except FileNotFoundError:
            return []
