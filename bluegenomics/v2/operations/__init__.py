"""
Operations module for bioinformatics workflow execution
"""

from .shell_operation import ShellOperation
from .sequence_qc import SequenceQC
from .umi_dedup import DeduplicateByUMI

__all__ = ['ShellOperation', 'SequenceQC', 'DeduplicateByUMI']
