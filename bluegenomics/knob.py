"""
Knob - Interactive parameter input for Jupyter notebooks
"""

from typing import Any, List, Dict, Union
import numpy as np


def knob(default: Any, choices: Union[List, Dict] = None, config: Dict = None) -> Any:
    """
    Create an interactive parameter input (simplified for non-interactive use).

    In the original watershed, this creates interactive widgets in Jupyter.
    For this implementation, it simply returns the default value.

    Args:
        default: Default value for the parameter
        choices: List of possible choices (optional)
        config: Configuration dict with options like 'label', 'multi', etc.

    Returns:
        The default value (in interactive mode, would return user selection)
    """
    if config is None:
        config = {}

    label = config.get('label', '')
    multi = config.get('multi', False)

    # Convert numpy arrays to lists to avoid broadcasting issues
    if choices is not None and isinstance(choices, np.ndarray):
        choices = choices.tolist()

    # Check if default is in choices (skip for multi-select or dict choices)
    if choices is not None and not multi and isinstance(choices, list):
        try:
            # Use a safe check that works with lists, numpy arrays, etc.
            if len(choices) > 0 and default not in choices:
                print(f"Warning: Default value '{default}' not in choices, using first choice")
                return choices[0]
        except (ValueError, TypeError):
            # If comparison fails (e.g., comparing incompatible types), just return default
            pass

    return default
