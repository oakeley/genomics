"""
Utility functions for BlueGenomics
"""

from pathlib import Path
from typing import Any, List, Union, Iterable
from datetime import datetime
import collections.abc


def listify(obj: Any) -> List[Any]:
    """
    Convert an object to a list if it is not already a list or tuple.

    Args:
        obj: Any object to listify

    Returns:
        List containing the object(s)
    """
    if obj is None:
        return []
    if isinstance(obj, (list, tuple)):
        return list(obj)
    return [obj]


def flatten(lst: Iterable) -> List[Any]:
    """
    Flatten a nested list structure.

    Args:
        lst: Nested list or iterable to flatten

    Returns:
        Flattened list
    """
    result = []
    for item in lst:
        if isinstance(item, collections.abc.Iterable) and not isinstance(item, (str, bytes, Path)):
            result.extend(flatten(item))
        else:
            result.append(item)
    return result


def _flatten_if_needed(obj: Any) -> List[Any]:
    """
    Flatten object if it's a nested list, otherwise listify it.

    Args:
        obj: Object to process

    Returns:
        Flattened or listified object
    """
    if isinstance(obj, list) and len(obj) > 0 and isinstance(obj[0], list):
        return flatten(obj)
    return listify(obj)


def pathify(path: Union[str, Path]) -> Path:
    """
    Convert a string path to a Path object.

    Args:
        path: String or Path object

    Returns:
        Path object
    """
    if isinstance(path, Path):
        return path
    return Path(path)


def iso_timestamp(timestamp: float = None) -> str:
    """
    Generate ISO format timestamp.

    Args:
        timestamp: Unix timestamp, or None for current time

    Returns:
        ISO formatted timestamp string
    """
    if timestamp is None:
        dt = datetime.now()
    else:
        dt = datetime.fromtimestamp(timestamp)
    return dt.isoformat()


def create_download_link(df, title: str = "Download CSV file", filename: str = "data.csv"):
    """
    Create a download link for a pandas DataFrame in Jupyter notebooks.

    Args:
        df: pandas DataFrame to download
        title: Link text to display
        filename: Filename for the downloaded file

    Returns:
        IPython HTML object with download link
    """
    import base64
    try:
        from IPython.display import HTML
    except ImportError:
        raise ImportError("create_download_link requires IPython to be installed")

    csv = df.to_csv()
    b64 = base64.b64encode(csv.encode())
    payload = b64.decode()
    html = f'<a download="{filename}" href="data:text/csv;base64,{payload}" target="_blank">{title}</a>'
    return HTML(html)


def flatten_multiindex_columns(df, sep='_'):
    """
    Flatten MultiIndex columns to simple string column names.

    When creating DataFrames with tuple keys (common in stats dictionaries),
    pandas creates MultiIndex columns. This function flattens them to simple
    strings, which is necessary for operations like melt() to work correctly.

    Handles the case where reset_index() has been called on a DataFrame with
    MultiIndex columns, which creates index column names like ('sequence_id', '', '').

    Args:
        df: DataFrame with MultiIndex columns or regular columns
        sep: Separator for joining tuple elements (default: '_')

    Returns:
        DataFrame with flattened column names

    Example:
        >>> stats = {
        ...     'sample1': {('genome', 'raw', 'reads'): 1000},
        ...     'sample2': {('genome', 'raw', 'reads'): 2000}
        ... }
        >>> df = pd.DataFrame(stats).T
        >>> df = flatten_multiindex_columns(df)
        >>> # Columns are now like 'genome_raw_reads' instead of ('genome', 'raw', 'reads')
    """
    try:
        import pandas as pd
    except ImportError:
        raise ImportError("flatten_multiindex_columns requires pandas to be installed")

    df = df.copy()

    if isinstance(df.columns, pd.MultiIndex):
        # Join tuple elements, filtering out empty strings
        new_columns = []
        for col in df.columns:
            if isinstance(col, tuple):
                # Filter out empty strings and join
                non_empty = [str(c).strip() for c in col if str(c).strip()]
                new_columns.append(sep.join(non_empty) if non_empty else 'unknown')
            else:
                new_columns.append(str(col))
        df.columns = new_columns

    return df


def prepare_stats_dataframe(stats_dict, index_name='sequence_id', flatten_columns=True):
    """
    Prepare a statistics DataFrame from nested dict with tuple keys.

    This function handles the common pattern in genomics workflows where
    statistics are collected in nested dictionaries with tuple keys
    (e.g., (genome, stage, metric)) and need to be converted to DataFrames
    for visualization and analysis.

    Handles MultiIndex columns correctly for subsequent reset_index().melt()
    operations, which are commonly used to reshape data for plotting.

    Args:
        stats_dict: Dictionary where keys are sample IDs and values are
                   dicts with tuple keys mapping to numeric values
        index_name: Name for the index column (default: 'sequence_id')
        flatten_columns: Whether to flatten MultiIndex columns (default: True)

    Returns:
        DataFrame ready for reset_index().melt() operations

    Example:
        >>> stats = {
        ...     'sample1': {
        ...         ('donor', 'raw', 'read_pairs'): 1000,
        ...         ('donor', 'raw', 'mapped_pairs'): 900,
        ...     },
        ...     'sample2': {
        ...         ('donor', 'raw', 'read_pairs'): 2000,
        ...         ('donor', 'raw', 'mapped_pairs'): 1800,
        ...     }
        ... }
        >>> df = prepare_stats_dataframe(stats)
        >>> # Can now use: df.reset_index().melt(id_vars='sequence_id')
    """
    try:
        import pandas as pd
    except ImportError:
        raise ImportError("prepare_stats_dataframe requires pandas to be installed")

    df = pd.DataFrame(stats_dict).T

    if flatten_columns:
        df = flatten_multiindex_columns(df)

    df.index.name = index_name
    return df


def melt_stats_dataframe(df, index_name='sequence_id', column_names=None, sep='_'):
    """
    Reset index, flatten MultiIndex columns, and melt a stats DataFrame.

    This function handles the complete workflow of converting a stats DataFrame
    with MultiIndex columns into a long-format DataFrame suitable for plotting.
    It automatically handles the case where reset_index() creates tuple column
    names when MultiIndex columns are present.

    Args:
        df: DataFrame with stats (may have MultiIndex columns)
        index_name: Name of the index column (default: 'sequence_id')
        column_names: List of column names for the melted result. If None,
                     attempts to infer from the MultiIndex levels or uses
                     ['sequence_id', 'variable', 'value']
        sep: Separator used in flattened column names (default: '_')

    Returns:
        Melted DataFrame in long format

    Example:
        >>> stats = {
        ...     'sample1': {
        ...         ('donor', 'raw', 'read_pairs'): 1000,
        ...         ('donor', 'raw', 'mapped_pairs'): 900,
        ...     },
        ...     'sample2': {
        ...         ('donor', 'raw', 'read_pairs'): 2000,
        ...         ('donor', 'raw', 'mapped_pairs'): 1800,
        ...     }
        ... }
        >>> df = pd.DataFrame(stats).T
        >>> df.index.name = 'sequence_id'
        >>> melted = melt_stats_dataframe(df, column_names=['sequence_id', 'genome', 'stage', 'variable', 'value'])
        >>> # Result has columns: sequence_id, genome, stage, variable, value
    """
    try:
        import pandas as pd
    except ImportError:
        raise ImportError("melt_stats_dataframe requires pandas to be installed")

    # Determine number of levels in the MultiIndex if present
    nlevels = df.columns.nlevels if isinstance(df.columns, pd.MultiIndex) else 1

    # Reset the index to add it as a column
    df = df.reset_index()

    # Flatten the MultiIndex columns
    df = flatten_multiindex_columns(df, sep=sep)

    # Get the first column name (which should be the index_name after flattening)
    id_col = df.columns[0]

    # Melt the DataFrame
    melted = df.melt(id_vars=id_col)

    # If column_names provided and includes more than the default columns,
    # split the 'variable' column
    if column_names and len(column_names) > 3:
        # Split the variable column based on separator
        # Number of splits needed: len(column_names) - 3 (for id, var, value)
        n_splits = len(column_names) - 3
        split_vars = melted['variable'].str.split(sep, n=n_splits, expand=True)

        # Add the split columns
        for i, col_name in enumerate(column_names[1:-1]):  # Skip first (id) and last (value)
            melted[col_name] = split_vars[i] if i < len(split_vars.columns) else None

        # Reorder columns
        melted = melted[[column_names[0]] + column_names[1:-1] + [column_names[-1]]]

        # Drop the original 'variable' column if it's not in the final column names
        if 'variable' in melted.columns and 'variable' not in column_names:
            melted = melted.drop(columns=['variable'])

    # Rename the id column if needed
    if id_col != column_names[0] if column_names else index_name:
        melted = melted.rename(columns={id_col: column_names[0] if column_names else index_name})

    return melted


def clean_numeric_data(data, remove_nan=True, remove_inf=True):
    """
    Remove NaN and/or inf values from numeric data.

    This function is useful for cleaning data before statistical or plotting
    operations that cannot handle non-finite values, such as KDE plots or
    certain statistical tests.

    Args:
        data: Array-like numeric data (pandas Series, numpy array, or list)
        remove_nan: Whether to remove NaN values (default: True)
        remove_inf: Whether to remove inf and -inf values (default: True)

    Returns:
        Cleaned data with non-finite values removed, in the same type as input

    Example:
        >>> import numpy as np
        >>> import pandas as pd
        >>> data = pd.Series([1, 2, np.nan, np.inf, 5, -np.inf, 10])
        >>> clean_data = clean_numeric_data(data)
        >>> # Result: Series with values [1, 2, 5, 10]
    """
    try:
        import numpy as np
        import pandas as pd
    except ImportError:
        raise ImportError("clean_numeric_data requires numpy and pandas to be installed")

    if isinstance(data, pd.Series):
        mask = pd.Series([True] * len(data), index=data.index)
        if remove_nan:
            mask = mask & ~data.isna()
        if remove_inf:
            mask = mask & np.isfinite(data)
        return data[mask]
    else:
        data_array = np.asarray(data)
        mask = np.ones(len(data_array), dtype=bool)
        if remove_nan:
            mask = mask & ~np.isnan(data_array)
        if remove_inf:
            mask = mask & np.isfinite(data_array)
        return data_array[mask]
