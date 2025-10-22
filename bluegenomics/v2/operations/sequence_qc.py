"""
SequenceQC - Quality control for sequencing data using FastQC
"""

from pathlib import Path
from typing import Dict, Any, List, Union
from .shell_operation import ShellOperation
from ..data_object import DataObject
from ..sequence import Sequence
from ...utils import listify


class SequenceQC(ShellOperation):
    """
    Performs quality control on sequencing data using FastQC.
    """

    def input_spec(self) -> dict:
        """
        Specify required inputs.

        Returns:
            Dictionary specifying input requirements
        """
        return {
            'sequence': Sequence,
        }

    def output_spec(self) -> dict:
        """
        Specify outputs produced.

        Returns:
            Dictionary specifying output structure
        """
        return {
            'qc': {
                'type': DataObject,
                'parent': 'sequence',
                'files': self.__get_qc_files
            }
        }

    def params(self) -> dict:
        """
        Specify default parameters.

        Returns:
            Dictionary of parameters
        """
        return {
            'fastqc_options': {'-t': 4},
            'tool': 'fastqc',
        }

    def __get_qc_files(self, temp_dir: Path) -> List[Dict[str, Any]]:
        """
        Collect FastQC output files.

        Args:
            temp_dir: Temporary directory containing FastQC output

        Returns:
            List of file specifications
        """
        files = []
        temp_path = Path(temp_dir)

        # Find all FastQC HTML and ZIP files
        for html_file in temp_path.glob("*_fastqc.html"):
            files.append({
                'file_path': html_file,
                'type': 'report',
                'subtypes': {'format': 'html'}
            })

        for zip_file in temp_path.glob("*_fastqc.zip"):
            files.append({
                'file_path': zip_file,
                'type': 'qc_data',
                'subtypes': {'format': 'zip'}
            })

        # Find fastqc_data.txt files in extracted directories
        for data_file in temp_path.glob("*/fastqc_data.txt"):
            files.append({
                'file_path': data_file,
                'type': 'qc_metrics',
                'subtypes': {'format': 'txt'}
            })

        return files

    def cmd(self, inputs: Dict[str, DataObject], params: Dict[str, Any]) -> dict:
        """
        Generate FastQC command.

        Args:
            inputs: Dictionary of input objects
            params: Dictionary of parameters

        Returns:
            Command specification
        """
        sequence = inputs.get('sequence')
        fastqc_options = params.get('fastqc_options', {})
        tool = params.get('tool', 'fastqc')

        # Get FASTQ files from the sequence
        fastq_list = sequence.fastq_list

        # Collect all FASTQ files
        all_fastqs = []
        for read_files in fastq_list:
            all_fastqs.extend(read_files)

        if not all_fastqs:
            raise ValueError(f"No FASTQ files found in sequence {sequence.identifier()}")

        # Build FastQC command
        cmd_parts = [
            tool,
            *self.format_args(fastqc_options),
            '-o', '.',
        ]

        # Add all FASTQ files
        cmd_parts.extend([str(f) for f in all_fastqs])

        return {
            'cmd': cmd_parts,
            'inputs': ['sequence'],
            'outputs': ['qc'],
            'label': f'FastQC for {sequence.identifier()}',
        }
