"""
Configuration management for BlueGenomics
"""

import os
import json
from pathlib import Path
from typing import Dict, Any


class Config:
    """
    Configuration manager for BlueGenomics paths and settings.
    Loads from config file or uses defaults.
    """

    _instance = None
    _config = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._config is None:
            self._load_config()

    def _load_config(self):
        """Load configuration from file or use defaults"""
        config_paths = [
            Path("/_org/saliogen/bluegenomics_config.json"),
            Path.home() / ".bluegenomics" / "config.json",
            Path.cwd() / "bluegenomics_config.json",
        ]

        for config_path in config_paths:
            if config_path.exists():
                with open(config_path, 'r') as f:
                    self._config = json.load(f)
                return

        self._config = self._get_defaults()

    def _get_defaults(self) -> Dict[str, Any]:
        """Get default configuration"""
        ncraig_base = Path("/_org/saliogen/ncraig")
        home_base = Path.home()

        if ncraig_base.exists():
            data_dir = ncraig_base / "bluegenomics_data"
            sequence_dir = ncraig_base / "sequence"
            notebook_home = ncraig_base
        else:
            data_dir = home_base / "bluegenomics_data"
            sequence_dir = home_base / "sequence"
            notebook_home = home_base

        reference_dir = Path("/home") / os.environ.get('USER', 'edward') / "git" / "FP2" / "reference_genomes"
        if not reference_dir.exists():
            reference_dir = home_base / "reference_genomes"

        return {
            "data_directory": str(data_dir),
            "sequence_directory": str(sequence_dir),
            "reference_genomes_directory": str(reference_dir),
            "default_reference": "T2T-CHM13.fa.gz",
            "notebook_home": str(notebook_home)
        }

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        return self._config.get(key, default)

    @property
    def data_directory(self) -> Path:
        """Get data storage directory"""
        return Path(self.get("data_directory"))

    @property
    def sequence_directory(self) -> Path:
        """Get sequence files directory"""
        return Path(self.get("sequence_directory"))

    @property
    def reference_genomes_directory(self) -> Path:
        """Get reference genomes directory"""
        return Path(self.get("reference_genomes_directory"))

    @property
    def genome_directory(self) -> Path:
        """Get genome objects directory"""
        genome_dir = self.get("genome_directory")
        if genome_dir:
            return Path(genome_dir)
        # Fall back to ncraig/genome if not configured
        ncraig_genome = Path("/_org/saliogen/ncraig/genome")
        if ncraig_genome.exists():
            return ncraig_genome
        return self.data_directory

    @property
    def default_reference(self) -> str:
        """Get default reference genome filename"""
        return self.get("default_reference", "T2T-CHM13.fa.gz")

    @property
    def notebook_home(self) -> Path:
        """Get notebook home directory (replacement for Path.home() in notebooks)"""
        return Path(self.get("notebook_home", "/_org/saliogen/ncraig"))

    @property
    def custom_scripts_directory(self) -> Path:
        """Get custom scripts directory"""
        scripts_dir = self.get("custom_scripts_directory")
        if scripts_dir:
            return Path(scripts_dir)
        # Fall back to default location if not configured
        return Path("/_org/saliogen/ws_saliogen/notebook/custom_scripts")

    @property
    def homer_bin_directory(self) -> Path:
        """Get HOMER bin directory"""
        homer_dir = self.get("homer_bin_directory")
        if homer_dir:
            return Path(homer_dir)
        # Fall back to default HOMER location
        return Path("/_org/saliogen/bin/bin")

    @property
    def dataset_directory(self) -> Path:
        """Get dataset directory for karyotype and other reference data"""
        dataset_dir = self.get("dataset_directory")
        if dataset_dir:
            return Path(dataset_dir)
        # Fall back to default dataset location
        return Path("/_org/saliogen/ncraig/dataset")

    def save(self, config_path: Path = None):
        """Save configuration to file"""
        if config_path is None:
            config_path = Path("/_org/saliogen/bluegenomics_config.json")

        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, 'w') as f:
            json.dump(self._config, f, indent=2)


config = Config()


def notebook_home() -> Path:
    """
    Returns the configured notebook home directory.
    Use this instead of Path.home() in notebooks to ensure portability.

    Returns:
        Path: The configured notebook home directory (default: /_org/saliogen/ncraig)
    """
    return config.notebook_home
