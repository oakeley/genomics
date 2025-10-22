"""
DataObject - Base class for managing data files and metadata in workflows
"""

from pathlib import Path
from typing import Any, Dict, List, Union, Iterable
import json
import shutil
import os
import uuid
from ..utils import listify, pathify
from ..logging import LOG
from ..config import config

_STR_KEYED_DICT = Dict[str, Any]
DEFAULT_FILE_TYPE = "file"


class DataObjectNotFoundError(Exception):
    """Raised when a DataObject cannot be found"""
    pass


class ObjectByIdentifierDescriptor:
    """
    Descriptor that makes object_by_identifier work both as classmethod and instance method.
    """
    def __get__(self, obj, objtype=None):
        if obj is None:
            # Called on class: Class.object_by_identifier('id')
            def classmethod_wrapper(identifier: str, parent: 'DataObject' = None) -> 'DataObject':
                if parent:
                    obj_path = parent._path / identifier
                else:
                    # Use genome_directory for Genome class, data_directory for others
                    from ..v2.genome import Genome
                    if objtype and issubclass(objtype, Genome):
                        obj_path = config.genome_directory / identifier
                    else:
                        obj_path = config.data_directory / identifier

                if not obj_path.exists():
                    raise DataObjectNotFoundError(f"DataObject '{identifier}' not found at {obj_path}")

                return objtype(obj_path)
            return classmethod_wrapper
        else:
            # Called on instance: instance.object_by_identifier('child')
            def instancemethod_wrapper(identifier: str) -> 'DataObject':
                # Check if instance has custom path resolution
                if hasattr(obj, '_resolve_child_path'):
                    obj_path = obj._resolve_child_path(identifier)
                else:
                    obj_path = obj._path / identifier

                if not obj_path.exists():
                    raise DataObjectNotFoundError(f"DataObject '{identifier}' not found at {obj_path}")

                return objtype(obj_path)
            return instancemethod_wrapper


class DataObject:
    """
    Base class for managing data files and associated metadata.
    Provides file management, versioning, and hierarchical organization.
    """

    # Use descriptor to make object_by_identifier work both as classmethod and instance method
    object_by_identifier = ObjectByIdentifierDescriptor()

    def __init__(self, path: Union[str, Path]):
        """
        Initialize a DataObject from an existing path.

        Args:
            path: Path to the data object directory
        """
        self._path = pathify(path)
        if not self._path.exists():
            raise DataObjectNotFoundError(f"DataObject not found at {self._path}")

        self.__files_path = self._path / "files"
        self.__info_file = self._path / "info.json"
        self.__info = self.__read_info()

    def __read_info(self) -> Dict[str, Any]:
        """Read metadata from info.json file"""
        if self.__info_file.exists():
            with open(self.__info_file, 'r') as f:
                return json.load(f)
        return {"files": {}}

    def __write_info(self):
        """Write metadata to info.json file"""
        with open(self.__info_file, 'w') as f:
            json.dump(self.__info, f, indent=2)

    def identifier(self) -> str:
        """Get the identifier (name) of this DataObject"""
        return self._path.name

    @property
    def uuid(self) -> str:
        """
        Get a unique identifier for this DataObject.

        Generates a deterministic UUID based on the absolute path.

        Returns:
            UUID string
        """
        # Use UUID5 with a namespace and the absolute path for deterministic UUID
        namespace = uuid.UUID('6ba7b810-9dad-11d1-80b4-00c04fd430c8')  # DNS namespace
        return str(uuid.uuid5(namespace, str(self._path.absolute())))

    def files(self, type_: str = None, subtypes: Dict[str, Any] = None,
              as_list: bool = False, metadata: bool = False) -> Union[Path, List[Path], Dict]:
        """
        Get files of a specific type from this DataObject.

        Args:
            type_: File type to filter by
            subtypes: Dictionary of subtype key-value pairs to match
            as_list: Return as list even if single file
            metadata: Return file metadata dict instead of paths

        Returns:
            Path, List of Paths, or metadata dict depending on parameters

        Raises:
            FileNotFoundError: If no matching files found
        """
        files_info = self.__info.get("files", {})

        if type_ is None:
            all_files = []
            for file_type, file_entries in files_info.items():
                for entry in listify(file_entries):
                    all_files.append(self.__files_path / entry["filename"])
            if not all_files:
                raise FileNotFoundError("No files found")
            return all_files

        if type_ not in files_info:
            raise FileNotFoundError(f"No files of type '{type_}' found")

        entries = listify(files_info[type_])

        # Filter by subtypes if provided
        if subtypes:
            filtered_entries = []
            for entry in entries:
                entry_subtypes = entry.get("subtypes", {})
                if all(entry_subtypes.get(k) == v for k, v in subtypes.items()):
                    filtered_entries.append(entry)
            entries = filtered_entries

        if not entries:
            raise FileNotFoundError(f"No files matching criteria found")

        if metadata:
            return entries if len(entries) > 1 or as_list else entries[0]

        file_paths = [self.__files_path / entry["filename"] for entry in entries]

        if len(file_paths) == 1 and not as_list:
            return file_paths[0]
        return file_paths

    def add_files(self, files: Union[Iterable[Union[Path, _STR_KEYED_DICT]], Path, _STR_KEYED_DICT],
                  default_type: str = None, keep_original: bool = True):
        """
        Add files to this DataObject.

        Args:
            files: Path(s) or dict(s) specifying files to add
            default_type: Default type for files without explicit type
            keep_original: Keep original files (copy vs move)
        """
        if default_type is None:
            default_type = DEFAULT_FILE_TYPE

        file_dicts = []
        for item in listify(files):
            if isinstance(item, Path):
                file_dict = {"file_path": item}
            elif isinstance(item, dict):
                file_dict = item.copy()
            else:
                raise ValueError("Invalid file specification")
            file_dicts.append(file_dict)

        for item in file_dicts:
            item["file_path"] = pathify(item["file_path"])
            item.setdefault("type", default_type)
            item.setdefault("original_file_path", item["file_path"].absolute())

        if not self.__files_path.exists():
            self.__files_path.mkdir(parents=True)

        for file_dict in file_dicts:
            file_path = file_dict["file_path"]
            file_type = file_dict["type"]
            dest_filename = file_path.name
            destpath = self.__files_path / dest_filename

            if destpath.exists() or destpath.is_symlink():
                if destpath.is_symlink():
                    destpath.unlink()
                elif destpath.is_file():
                    destpath.unlink()

            if keep_original:
                os.symlink(file_path.absolute(), destpath)
            else:
                shutil.move(file_path, destpath)

            file_mtime = file_path.stat().st_mtime if keep_original else destpath.stat().st_mtime
            final_dict = {
                "filename": dest_filename,
                "time": str(file_mtime),
                "original_file_path": str(file_dict["original_file_path"]),
            }
            if "subtypes" in file_dict:
                final_dict["subtypes"] = file_dict["subtypes"]

            if file_type in self.__info["files"]:
                self.__info["files"][file_type] = listify(self.__info["files"][file_type])
                self.__info["files"][file_type].append(final_dict)
            else:
                self.__info["files"][file_type] = final_dict

            self.__write_info()

    @classmethod
    def create_from_files(cls, identifier: str, files: Union[Path, List, Dict],
                          parent: 'DataObject' = None, keep_original: bool = True) -> 'DataObject':
        """
        Create a new DataObject from files.

        Args:
            identifier: Name for the new DataObject
            files: Files to include
            parent: Parent DataObject
            keep_original: Keep original files

        Returns:
            New DataObject instance
        """
        if parent:
            base_path = parent._path
        else:
            base_path = config.data_directory

        obj_path = base_path / identifier
        obj_path.mkdir(parents=True, exist_ok=True)

        info_file = obj_path / "info.json"
        with open(info_file, 'w') as f:
            json.dump({"files": {}, "identifier": identifier}, f)

        obj = cls(obj_path)

        if isinstance(files, (Path, list, dict)):
            obj.add_files(files, keep_original=keep_original)

        return obj

    def objects(self, object_type: type = None) -> List['DataObject']:
        """
        List all child DataObjects within this DataObject.

        Args:
            object_type: Filter by specific DataObject subclass

        Returns:
            List of DataObject instances
        """
        if not self._path.exists():
            return []

        found_objects = []
        for item in self._path.iterdir():
            if item.is_dir() and (item / "info.json").exists():
                try:
                    if object_type and object_type != DataObject:
                        obj = object_type(item)
                    else:
                        obj = DataObject(item)
                    found_objects.append(obj)
                except Exception:
                    continue
        return found_objects

    @classmethod
    def all_objects(cls, parent: 'DataObject' = None) -> List['DataObject']:
        """
        List all DataObjects of this class type.

        Args:
            parent: Parent DataObject to search within

        Returns:
            List of DataObject instances
        """
        if parent:
            search_path = parent._path
        else:
            search_path = config.data_directory

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

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.identifier()})"
