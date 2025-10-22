# BlueGenomics Module

## Overview
BlueGenomics is a replacement module for some legacy dependencies in Blue Marlin notebooks. It provides equivalent functionality for bioinformatics workflow management while maintaining compatibility with existing code. It does not depend on any of the legacy code and was reverse engineered by trial and error based on the legacy outputs in the old notebooks. Claude code was used to generate the initial structure and interface.

## Installation
The following command-line tools must be installed and available in PATH:

1. **Python** - Version 3.11 via CONDA (preferred)
2. **picard** - For duplicate marking and other operations
3. **BWA** (Burrows-Wheeler Aligner) - For read alignment
4. **samtools** - For SAM/BAM file manipulation
5. **FastQC** - For quality control
6. **MultiQC** - For aggregating QC reports
7. **UMI-tools** - For handling unique molecular identifiers
8. **Python dependencies** - Various python packages
9. **R and some dependencies** - R is needed for Homer
10. **Homer** - For peak-finding and integration site analysis

### 1. Create Conda Environment (Python 3.11)

```bash
conda create -n saliogen python=3.11
conda activate saliogen
conda install pip
```

**Note**: Python 3.11 was chosen for better compatibility with bioinformatics tools.

### Required Bioinformatics Tools


## Bioinformatics Tools Installation

### 2. Install Picard (Java-based tool)

```bash
# Install JDK 25
sudo dpkg -i /_org/saliogen/bin/jdk-25_linux-x64_bin.deb

# Fix Java path in conda environment
mv /home/edward/anaconda3/bin/java /home/edward/anaconda3/bin/java.bak
ln -s /usr/lib/jvm/jdk-25-oracle-x64/bin/java /home/edward/anaconda3/bin/java
```

### 3. Install BWA (Burrows-Wheeler Aligner)

```bash
sudo apt install bwa
```

### 4. Install samtools

```bash
sudo apt install samtools
```

### 5. Install FastQC

```bash
sudo apt install fastqc
```

### 6. Install MultiQC

```bash
conda install multiqc
```

### 7. Install UMI-tools

```bash
conda install bioconda::umi_tools
```

### 8. Install Required Python Packages

```bash
pip install numpy pandas pysam biopython pyranges plotly matplotlib seaborn jupyter ipython ipywidgets scipy scikit-learn tables tqdm upsetplot
```

## 9. Install R and dependencies
```bash
sudo apt install r-base
R
if (!requireNamespace("BiocManager", quietly = TRUE))
    install.packages("BiocManager")
BiocManager::install(c("DESeq2", "edgeR"))
BiocManager::install(c("SummarizedExperiment", "tximport", "biomaRt"))
```

## 10. Install HOMER
```bash
cd /_opt/saliogen/bin
wget http://homer.ucsd.edu/homer/configureHomer.pl
conda activate saliogen
perl configureHomer.pl -install homer
```

## Quick Start

```bash
# Activate environment
conda activate saliogen

# Start Jupyter
cd /_org/saliogen
jupyter notebook

# In notebook, add to first cell:
import sys
sys.path.insert(0, '/_org/saliogen')
import bluegenomics as ws
```

## Module Structure

```
bluegenomics/
├── __init__.py                  # Main package entry point
├── config.py                    # Avoid hard-coded paths by defining where things are on your system
├── distributed.py               # Queue, submit and monitor parallel jobs with reserved CPU and RAM
├── knob.py                      # Interactive parameter input
├── logging.py                   # Always nice to keep a log for debugging
├── plotting.py                  # General purpose graph and karyotype plotting functions
├── style.py                     # Color definitions for visualization
├── utils.py                     # Utility functions (listify, flatten, pathify)
└── v2/                          # Version 2 API
    ├── __init__.py
    ├── alignment.py             # Alignment data (BAM)
    ├── annotation.py            # Genome annotations (GTF/GFF)
    ├── data_object.py           # Base class for data management
    ├── genome_index.py          # Genome indices (BWA, etc.)
    ├── genome.py                # Reference genomes
    ├── logging.py               # v2 logging utilities
    ├── sequence.py              # Sequencing data (FASTQ)
    └── operations/
        ├── __init__.py
        ├── sequence_qc.py       # Base class for FASTQC and MultiQC operations
        ├── shell_operation.py   # Base class for shell operations
        └── umi_dedup.py         # Test code for UMI operations
```

## Core Classes

### DataObject
Base class for managing data files and metadata. Provides:
- File storage and retrieval
- Metadata management (JSON-based)
- Hierarchical organization
- Type-based file filtering

### Sequence
Manages FASTQ sequencing data:
- Paired-end and single-end support
- Lane and read number tracking
- Import from existing FASTQ files

### Alignment
Manages BAM alignment files:
- Multiple alignment types (raw, final, mark_duplicate)
- Index file management
- Quality control integration

### Genome
Reference genome management:
- FASTA file handling
- Chromosome information
- Organism metadata

### GenomeIndex
Genome index files for aligners:
- BWA index support
- Multi-file index management

### Annotation
Genome annotation data:
- GTF/GFF file handling
- Gene and feature annotations

### ShellOperation
Base class for bioinformatics operations:
- Input/output specification
- Parameter management
- Command execution with proper error handling
- Temporary directory management

## Key Functions

### Utility Functions
- `listify(obj)` - Convert object to list
- `flatten(lst)` - Flatten nested lists
- `pathify(path)` - Convert string to Path object
- `knob(default, choices, config)` - Interactive parameter input

### Logging
- `configure_log_level(logger_name, level)` - Configure logging

## Usage Example

```python
import bluegenomics as ws
from bluegenomics.v2 import Sequence, Alignment, Genome

# Create or load a sequence
seq = ws.v2.Sequence.object_by_identifier("BG0168_GX_GY0008_1")

# Get FASTQ files
fastq_files = seq.fastq_list

# Check if paired-end
is_paired = seq.is_paired

# Use utility functions
files_list = ws.listify(seq.files())
