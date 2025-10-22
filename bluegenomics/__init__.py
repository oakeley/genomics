"""
BlueGenomics - A lightweight bioinformatics workflow framework
Replacement for watershed functionality in saliogen project
"""

__version__ = "0.1.0"

from . import utils
from . import v2
from . import logging
from . import style
from . import distributed
from . import config
from . import plotting
from .knob import knob
from .config import notebook_home

# Expose common functions at package level
from .utils import (listify, flatten, pathify, create_download_link,
                    flatten_multiindex_columns, prepare_stats_dataframe,
                    melt_stats_dataframe, clean_numeric_data)
from .plotting import plot_karyoplot

__all__ = ['utils', 'v2', 'logging', 'style', 'distributed', 'config', 'plotting', 'knob', 'notebook_home',
           'listify', 'flatten', 'pathify', 'create_download_link',
           'flatten_multiindex_columns', 'prepare_stats_dataframe', 'melt_stats_dataframe',
           'clean_numeric_data', 'plot_karyoplot']
