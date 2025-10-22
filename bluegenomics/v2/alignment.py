"""
Alignment - Class for managing alignment data (BAM files)
"""

from pathlib import Path
from typing import Union
from .data_object import DataObject

ALIGNED_FILE_TYPE = "alignment"
BAM_INDEX_FILE_TYPE = "index"


class Alignment(DataObject):
    """
    Represents alignment data (BAM files) from mapping reads to a reference genome.
    """

    def __init__(self, path: Union[str, Path]):
        super().__init__(path)

    def bam_file(self, alignment_type: str = "final") -> Path:
        """
        Get the BAM file for a specific alignment type.

        Args:
            alignment_type: Type of alignment (e.g., 'raw', 'final', 'mark_duplicate')

        Returns:
            Path to BAM file
        """
        return self.files(type_=ALIGNED_FILE_TYPE, subtypes={"alignment_type": alignment_type})

    @property
    def final_bam(self) -> Path:
        """Get the final processed BAM file"""
        return self.bam_file("final")

    @property
    def raw_bam(self) -> Path:
        """Get the raw alignment BAM file"""
        return self.bam_file("raw")
