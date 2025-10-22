"""
Genome - Class for managing reference genome data
"""

from pathlib import Path
from typing import Union, List
from .data_object import DataObject
from ..config import config

FASTA_TYPE = "fasta"
CHROMINFO_TYPE = "chrominfo"


class _ObjectsDescriptor:
    """Descriptor to support both classmethod and instance method behavior for objects()"""

    def __get__(self, obj, objtype=None):
        if obj is None:
            # Called on class: Genome.objects()
            def classmethod_wrapper(parent=None):
                return objtype.all_objects(parent)
            return classmethod_wrapper
        else:
            # Called on instance: genome.objects(Type)
            def instance_wrapper(object_type=None):
                return DataObject.objects(obj, object_type)
            return instance_wrapper


class Genome(DataObject):
    """
    Represents a reference genome with FASTA files and chromosome information.
    """

    objects = _ObjectsDescriptor()

    def __init__(self, path: Union[str, Path]):
        super().__init__(path)
        self._organism = None
        self._chromosomes = None
        self.annotation = None

    @property
    def organism(self) -> str:
        """Get the organism name for this genome"""
        if self._organism is None:
            # Access private method using name mangling
            info_file = self._path / "info.json"
            if info_file.exists():
                import json
                with open(info_file, 'r') as f:
                    info = json.load(f)
                self._organism = info.get("organism", "unknown")
            else:
                self._organism = "unknown"
        return self._organism

    @property
    def chromosomes(self) -> List[str]:
        """Get list of chromosome names"""
        if self._chromosomes is None:
            try:
                chrominfo_file = self.files(type_=CHROMINFO_TYPE)
                with open(chrominfo_file, 'r') as f:
                    self._chromosomes = [line.split('\t')[0] for line in f if line.strip()]
            except (FileNotFoundError, Exception):
                self._chromosomes = []
        return self._chromosomes

    def fasta_file(self) -> Path:
        """Get the FASTA file for this genome"""
        return self.files(type_=FASTA_TYPE)

    def _resolve_child_path(self, identifier: str) -> Path:
        """
        Resolve the path for a child object with special handling for genome indices and annotations.

        Args:
            identifier: Name of child object

        Returns:
            Path to the child object
        """
        if identifier == 'bwa':
            # BWA index is nested under genome_index/bwa
            genome_index_path = self._path / 'genome_index' / 'bwa'
            if genome_index_path.exists():
                return genome_index_path

        # Check if this is an annotation nested under annotation/
        annotation_path = self._path / 'annotation' / identifier
        if annotation_path.exists():
            return annotation_path

        # Default: direct child
        return self._path / identifier

    @classmethod
    def all_objects(cls, parent: 'DataObject' = None) -> List['Genome']:
        """
        List all Genome objects from the genome directory.

        Args:
            parent: Parent DataObject to search within (if None, uses genome_directory)

        Returns:
            List of Genome instances
        """
        if parent:
            search_path = parent._path
        else:
            # Use genome_directory instead of data_directory
            search_path = config.genome_directory

        if not search_path.exists():
            return []

        objects = []
        for item in search_path.iterdir():
            if item.is_dir() and (item / "info.json").exists():
                try:
                    objects.append(cls(item))
                except Exception:
                    continue
        return objects

    @classmethod
    def all_genomes(cls, parent=None):
        """
        List all Genome objects.

        Args:
            parent: Parent DataObject to search within

        Returns:
            List of Genome instances
        """
        return cls.all_objects(parent)

    @classmethod
    def create_genome(cls, identifier: str, fasta_path: Path,
                      organism: str = None, chromosomes: List[str] = None,
                      parent: DataObject = None) -> 'Genome':
        """
        Create a new Genome from a FASTA file.

        Args:
            identifier: Name for the genome
            fasta_path: Path to FASTA file
            organism: Organism name
            chromosomes: List of chromosome names
            parent: Parent DataObject

        Returns:
            New Genome instance
        """
        genome = cls.create_from_files(
            identifier=identifier,
            files=[{"file_path": fasta_path, "type": FASTA_TYPE}],
            parent=parent
        )

        if organism:
            import json
            info_file = genome._path / "info.json"
            if info_file.exists():
                with open(info_file, 'r') as f:
                    info = json.load(f)
            else:
                info = {"files": {}}

            info["organism"] = organism

            with open(info_file, 'w') as f:
                json.dump(info, f, indent=2)

            genome._organism = organism

        return genome
