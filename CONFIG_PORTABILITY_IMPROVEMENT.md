# Configuration-Based Path Management

## Overview

Replaced hard-coded paths in `HC_custom_scripts.py` with configuration-based paths for better portability.

## Changes Made

### 1. Added Custom Scripts Directory to Config

**File:** `/_org/saliogen/bluegenomics_config.json`

Added new configuration parameter:
```json
{
  ...
  "custom_scripts_directory": "/_org/saliogen/ws_saliogen/notebook/custom_scripts"
}
```

### 2. Added Config Property

**File:** `bluegenomics/config.py`

Added new property:
```python
@property
def custom_scripts_directory(self) -> Path:
    """Get custom scripts directory"""
    scripts_dir = self.get("custom_scripts_directory")
    if scripts_dir:
        return Path(scripts_dir)
    # Fall back to default location if not configured
    return Path("/_org/saliogen/ws_saliogen/notebook/custom_scripts")
```

### 3. Updated HC_custom_scripts.py

**File:** `ws_saliogen/notebook/custom_scripts/HC_custom_scripts.py`

**Before (Hard-coded paths):**
```python
FIND_INT_SITES_HC_PATH = "/_org/saliogen/ws_saliogen/notebook/custom_scripts/find_integration_sites_HC.py"
FIND_INT_SITES_DONOR_HC_PATH = "/_org/saliogen/ws_saliogen/notebook/custom_scripts/find_integration_sites_donor_HC.py"
SUMMARIZE_INT_SITES_HC_PATH = "/_org/saliogen/ws_saliogen/notebook/custom_scripts/summarize_integration_sites_HC.py"
...
```

**After (Config-based paths):**
```python
from bluegenomics.config import config

# Get custom scripts base directory from config
_SCRIPTS_BASE = config.custom_scripts_directory

# HC custom scripts - using config-based paths for portability
FIND_INT_SITES_HC_PATH = _SCRIPTS_BASE / "find_integration_sites_HC.py"
FIND_INT_SITES_DONOR_HC_PATH = _SCRIPTS_BASE / "find_integration_sites_donor_HC.py"
SUMMARIZE_INT_SITES_HC_PATH = _SCRIPTS_BASE / "summarize_integration_sites_HC.py"
...
```

## Benefits

### Portability
 **Easy relocation** - Change one config file instead of editing code
 **Multi-environment support** - Different paths for dev/production
 **User-specific paths** - Each user can configure their own paths

### Maintainability
 **Centralized configuration** - All paths in one place
 **Clear separation** - Config vs code
 **Type-safe** - Using Path objects instead of strings

### Backward Compatibility
 **Fallback defaults** - Works even without config file
 **No breaking changes** - Existing functionality preserved
 **Automatic migration** - Hard-coded defaults match current setup

## Configuration

### For New Installations

Create `/_org/saliogen/bluegenomics_config.json`:
```json
{
  "data_directory": "/path/to/data",
  "genome_directory": "/path/to/genomes",
  "custom_scripts_directory": "/path/to/custom_scripts",
  ...
}
```

### For Different Environments

**Development:**
```json
{
  "custom_scripts_directory": "/home/dev/saliogen/scripts"
}
```

**Production:**
```json
{
  "custom_scripts_directory": "/_org/saliogen/ws_saliogen/notebook/custom_scripts"
}
```

### For Testing

```json
{
  "custom_scripts_directory": "/tmp/test_scripts"
}
```

## Scripts Now Using Config

All HC (HighChrome) custom scripts now use config-based paths:

 **Integration Site Finding:**
- `FIND_INT_SITES_HC_PATH`
- `FIND_INT_SITES_DONOR_HC_PATH`
- `FIND_INT_SITES_DONOR_byname_HC_PATH`

 **Summarization:**
- `SUMMARIZE_INT_SITES_HC_PATH`
- `SUMMARIZE_INT_SITES_HC_LP_PATH`
- `SUMMARIZE_INT_SITES_HC_SB_PATH`

 **Utilities:**
- `DEDUP_BY_UMI_PATH`
- `CUSTOM_SCRIPTS_PATH`
- `ADD_REF_BASES_PATH`
- `FIND_INT_SITES_PATH`
- `TABULATOR_PATH`

## Migration Guide

### For Users on Default Setup
No action needed - fallback defaults match current paths.

### For Users with Custom Paths

1. **Create config file** (if not exists):
   ```bash
   cp /_org/saliogen/bluegenomics_config.json ~/.bluegenomics/config.json
   ```

2. **Update custom_scripts_directory**:
   ```json
   {
     "custom_scripts_directory": "/your/custom/path/to/scripts"
   }
   ```

3. **Restart notebook kernel**

### For Moving to New Server

1. **Copy scripts** to new location
2. **Update config**:
   ```json
   {
     "custom_scripts_directory": "/new/server/path/to/scripts"
   }
   ```
3. **No code changes needed!**

## Verification

Run verification script:
```bash
python3 -c "
from ws_saliogen.notebook.custom_scripts.HC_custom_scripts import _SCRIPTS_BASE
print(f'Scripts directory: {_SCRIPTS_BASE}')
print(f'Directory exists: {_SCRIPTS_BASE.exists()}')
"
```

Expected output:
```
Scripts directory: /_org/saliogen/ws_saliogen/notebook/custom_scripts
Directory exists: True
```

## Config File Locations

Config is loaded from (in order of priority):
1. `/_org/saliogen/bluegenomics_config.json`
2. `~/.bluegenomics/config.json`
3. `./bluegenomics_config.json` (current directory)
4. Built-in defaults (if no config file found)

## Future Improvements

Potential additional config parameters:
- `tabu_scripts_directory` - For TABU-specific scripts
- `bin_directory` - For executables like qsub3.sh, picard.jar
- `temp_directory` - For temporary files
- `log_directory` - For operation logs

## Related Documentation

- `bluegenomics_config.json` - Config file
- `bluegenomics/config.py` - Config system code
- `PATH_FIX_SUMMARY.md` - Initial path fix
- `COMPLETE_FIX_SUMMARY.md` - All fixes applied

---

**Date:** 2025-10-19
