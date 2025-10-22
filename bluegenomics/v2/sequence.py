"""
Sequence - Class for managing sequencing data (FASTQ files)
"""

from pathlib import Path
from typing import List, Dict, Any, Union
from .data_object import DataObject
from ..utils import listify

FASTQ_FILE_TYPE = "fastq"
INDEX_FILE_TYPE = "index"
QC_OBJECT_IDENTIFIER = "qc"


class Sequence(DataObject):
    """
    Represents sequencing data with FASTQ files.
    Handles paired-end and single-end sequencing data.
    """

    def __init__(self, path: Union[str, Path]):
        super().__init__(path)
        self._fastq_cache = None
        self._is_paired_cache = None

    @property
    def fastq_list(self) -> List[List[Path]]:
        """
        Get list of FASTQ files organized by read number.

        Returns:
            List of lists, where each inner list contains paths for one read
        """
        if self._fastq_cache is not None:
            return self._fastq_cache

        try:
            fastq_files = listify(self.files(type_=FASTQ_FILE_TYPE, as_list=True, metadata=True))
        except FileNotFoundError:
            return [[]]

        reads = {}
        for file_info in fastq_files:
            subtypes = file_info.get("subtypes", {})
            read_num = subtypes.get("read", 1)
            lane = subtypes.get("lane", 0)

            if read_num not in reads:
                reads[read_num] = []

            file_path = self._DataObject__files_path / file_info["filename"]
            reads[read_num].append(file_path)

        result = [reads.get(i, []) for i in sorted(reads.keys())]
        self._fastq_cache = result
        return result

    @property
    def is_paired(self) -> bool:
        """
        Check if this is paired-end sequencing data.

        Returns:
            True if paired-end, False if single-end
        """
        if self._is_paired_cache is not None:
            return self._is_paired_cache

        fastq_list = self.fastq_list
        self._is_paired_cache = len(fastq_list) >= 2 and len(fastq_list[1]) > 0
        return self._is_paired_cache

    def objects(cls_or_self, parent_or_type=None):
        """
        List Sequence objects or child objects of this Sequence.

        Can be called two ways:
        1. As classmethod: Sequence.objects() - lists all Sequences
        2. As instance method: sequence.objects(SomeType) - lists child objects

        Args:
            parent_or_type: Either a parent DataObject (classmethod) or object type (instance method)

        Returns:
            List of DataObject instances
        """
        # Check if being used as instance method with a type argument
        if parent_or_type is not None and isinstance(parent_or_type, type):
            # Instance method pattern: sequence.objects(SomeType)
            # Call the parent class's instance method
            return DataObject.objects(cls_or_self, parent_or_type)

        # Classmethod pattern: Sequence.objects() or Sequence.objects(parent)
        if isinstance(cls_or_self, type):
            # Called as Sequence.objects()
            return cls_or_self.all_objects(parent_or_type)
        else:
            # Called as sequence.objects() on an instance
            return cls_or_self.__class__.all_objects(parent_or_type)

    @classmethod
    def import_from_directory(cls, fastq_directory: Union[str, Path],
                             parent: DataObject = None) -> Dict[str, 'Sequence']:
        """
        Import all sequences from a directory of FASTQ files.
        Groups files by sequence identifier extracted from filename pattern.

        Filename pattern: {SAMPLE_ID}_S{NUMBER}_R{1|2}_001.fastq.gz or {SAMPLE_ID}_S{NUMBER}_I{1|2}_001.fastq.gz
        Extracts SAMPLE_ID by removing last 3 underscore-separated components.

        Args:
            fastq_directory: Directory containing FASTQ files
            parent: Parent DataObject for storing sequences

        Returns:
            Dictionary mapping sequence identifiers to Sequence objects
        """
        import os
        from collections import defaultdict

        fastq_dir = Path(fastq_directory)
        if not fastq_dir.exists():
            raise FileNotFoundError(f"Directory not found: {fastq_dir}")

        sample_files = defaultdict(lambda: {'reads': [], 'index': []})

        for filename in os.listdir(fastq_dir):
            if filename.endswith('.fastq.gz') or filename.endswith('.fq.gz'):
                parts = filename.split('_')
                if len(parts) >= 4:
                    seq_id = '_'.join(parts[:-3])
                    file_path = fastq_dir / filename

                    if '_I1_' in filename or '_I2_' in filename:
                        sample_files[seq_id]['index'].append(file_path)
                    else:
                        sample_files[seq_id]['reads'].append(file_path)

        sequences = {}
        for seq_id, files in sorted(sample_files.items()):
            all_files = files['reads'] + files['index']
            all_files.sort()

            try:
                existing_seq = cls.object_by_identifier(seq_id, parent=parent)
                sequences[seq_id] = existing_seq
            except:
                if files['index']:
                    reads_matrix = [[], []]
                    index_matrix = [[], []]

                    for f in files['reads']:
                        if '_R1_' in f.name:
                            reads_matrix[0].append(f.name)
                        elif '_R2_' in f.name:
                            reads_matrix[1].append(f.name)

                    for f in files['index']:
                        if '_I1_' in f.name:
                            index_matrix[0].append(f.name)
                        elif '_I2_' in f.name:
                            index_matrix[1].append(f.name)

                    import_matrix = {'reads': reads_matrix, 'index': index_matrix}

                    seq = cls.import_sequence(
                        identifier=seq_id,
                        import_sequence_paths=all_files,
                        import_matrix=import_matrix,
                        parent=parent
                    )
                else:
                    seq = cls.import_sequence(
                        identifier=seq_id,
                        import_sequence_paths=all_files,
                        parent=parent
                    )
                sequences[seq_id] = seq

        return sequences

    @classmethod
    def import_sequence(cls, identifier: str, import_sequence_paths: List[Path],
                        import_matrix: Dict[str, List[List[str]]] = None,
                        parent: DataObject = None) -> 'Sequence':
        """
        Import sequencing data from FASTQ files.

        Args:
            identifier: Name for the new Sequence object
            import_sequence_paths: List of FASTQ file paths
            import_matrix: Dictionary mapping 'reads' and 'index' to file organization
            parent: Parent DataObject

        Returns:
            New Sequence instance
        """
        files_to_add = []

        if import_matrix:
            reads_matrix = import_matrix.get('reads', [[]])
            index_matrix = import_matrix.get('index', [[]])

            for read_num, read_files in enumerate(reads_matrix):
                for lane_num, filename in enumerate(read_files):
                    matching_path = None
                    for path in import_sequence_paths:
                        if path.name == filename or str(path).endswith(filename):
                            matching_path = path
                            break

                    if matching_path:
                        files_to_add.append({
                            "file_path": matching_path,
                            "type": FASTQ_FILE_TYPE,
                            "subtypes": {"read": read_num, "lane": lane_num}
                        })

            for idx_num, index_files in enumerate(index_matrix):
                for lane_num, filename in enumerate(index_files):
                    matching_path = None
                    for path in import_sequence_paths:
                        if path.name == filename or str(path).endswith(filename):
                            matching_path = path
                            break

                    if matching_path:
                        files_to_add.append({
                            "file_path": matching_path,
                            "type": INDEX_FILE_TYPE,
                            "subtypes": {"index": idx_num, "lane": lane_num}
                        })
        else:
            for idx, path in enumerate(import_sequence_paths):
                read_num = 1 if "_R2" in path.name else 0
                files_to_add.append({
                    "file_path": path,
                    "type": FASTQ_FILE_TYPE,
                    "subtypes": {"read": read_num, "lane": 0}
                })

        seq = cls.create_from_files(identifier=identifier, files=files_to_add, parent=parent)
        return seq
