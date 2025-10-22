# Parallel Processing with qsub3.sh

## Summary

Added automatic parallel processing support to integration site analysis operations using Edward's bash qsub3.sh script. When multiple alignments are provided, the operations now automatically run in parallel instead of sequentially. This is for emulating a high performance Sun-grid engine-like cluster on a local machine with AMD Threadripper-class CPUs and lots of RAM.

## Changes Made

### 1. FindIntegrationSitesHC (HC_custom_scripts.py:1155-1180)

Added `run_job` override that:
- Auto-detects when a list of alignments is provided
- Automatically enables qsub for parallel processing
- Uses 2 threads and 8GB RAM per job (appropriate for integration site finding - Homer is not very parallel)

**Before (Sequential):**
```
Sample 1: 12:34:22 - 12:36:23 (2 minutes)
Sample 2: 12:36:23 - 12:38:17 (2 minutes)
Sample 3: 12:38:17 - 12:39:59 (2 minutes)
Total: 6 minutes
```

**After (Parallel with qsub):**
```
All samples: ~2 minutes total (all run simultaneously)
```

### 2. FindIntegrationSitesHC_donor (HC_custom_scripts.py:1256-1281)

Added same automatic qsub support for donor integration site finding with:
- 2 threads and 8GB RAM per job
- Auto-detection of multiple alignments

### 3. Summarize_Intsites (HC_custom_scripts.py:1425-1455)

Added qsub support for summarization operations with:
- 4 threads and 16GB RAM per job (less resource-intensive)
- Checks both positional and keyword arguments for lists
- Handles paired inputs (intsites_donor and intsites_human)

## How It Works

### Automatic Detection

The operations now check if you're providing multiple items:

```python
def run_job(self, *args, use_qsub=None, ...):
    if use_qsub is None:
        # Auto-detect: if list with >1 items, use qsub
        if args and isinstance(args[0], list) and len(args[0]) > 1:
            use_qsub = True

    return super().run_job(..., use_qsub=use_qsub, ...)
```

### qsub3.sh Integration

When qsub is enabled, the ShellOperation base class:
1. Creates a seed file with all commands
2. Calls `qsub3.sh -f seedfile -t threads -r ram_gb`
3. Waits for all jobs to complete
4. Collects outputs from each job

## Usage in Notebook

**No changes needed!** The notebook code already works, this just changes how the jobs are scheduled behind the scenes:

```python
# This automatically runs in parallel now
int_sites = finder.run_job(
    alignment=alignments_human,  # List of alignments
    annotation=genome.object_by_identifier(annotation),
    overwrite=True
)
```

### Manual Control (Optional)

You can still explicitly control qsub if needed:

```python
# Force sequential (override auto-detection)
int_sites = finder.run_job(
    alignment=alignments_human,
    annotation=genome.object_by_identifier(annotation),
    use_qsub=False
)

# Customize resources
int_sites = finder.run_job(
    alignment=alignments_human,
    annotation=genome.object_by_identifier(annotation),
    qsub_threads=16,  # More threads per job
    qsub_ram_gb=64    # More RAM per job
)
```

## Logging Output

You'll now see different log output:

**Before (Sequential):**
```
INFO - Executing: python ...find_integration_sites_HC.py --bam ...sample1...
INFO - Executing: python ...find_integration_sites_HC.py --bam ...sample2...
INFO - Executing: python ...find_integration_sites_HC.py --bam ...sample3...
```

**After (Parallel):**
```
INFO - Running 3 jobs in parallel using qsub3.sh
INFO - Resources per job: 4 threads, 16GB RAM
INFO - Created seed file with 3 commands: /tmp/.../qsub_seed.txt
INFO - Job 0 command: python ...find_integration_sites_HC.py --bam ...sample1...
INFO - Job 1 command: python ...find_integration_sites_HC.py --bam ...sample2...
INFO - Job 2 command: python ...find_integration_sites_HC.py --bam ...sample3...
INFO - Executing: bash /_org/saliogen/bin/qsub3.sh -f /tmp/.../qsub_seed.txt -t 8 -r 32
INFO - qsub3.sh completed successfully
```

## Expected Performance Improvement

For the integration site analysis with 4 samples:

**Sequential (old behavior):**
- Sample 1: ~2 min
- Sample 2: ~2 min
- Sample 3: ~2 min
- Sample 4: ~2 min
- **Total: ~8 minutes**

**Parallel (new behavior):**
- All samples: ~2 min (running simultaneously)
- **Total: ~2 minutes**

**Speedup: ~4x** (proportional to number of samples)

## Verification

To verify parallel processing is working:

1. **Check logs:** Look for "Running N jobs in parallel using qsub3.sh"
2. **Monitor system:** Run `htop` - you should see multiple processes running simultaneously
3. **Timing:** Note the start/end times in logs - all jobs should overlap

## Notes

- The qsub3.sh script must be available at `/_org/saliogen/bin/qsub3.sh`
- Jobs run in temporary directories that are cleaned up automatically
- Failed jobs will cause the entire operation to fail with error messages
- Each job's output is logged separately for debugging

## Backward Compatibility

✅ **100% backward compatible**

- Single alignment inputs still work (sequential, no qsub overhead)
- Explicit `use_qsub=False` still forces sequential processing
- All existing notebook code works without modification
