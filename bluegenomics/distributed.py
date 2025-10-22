"""
Distributed computing module for BlueGenomics
Executes jobs in parallel using the local qsub3.sh script
"""

import subprocess
import tempfile
from pathlib import Path
from typing import List, Callable, Any
import os
from .logging import LOG

QSUB_SCRIPT = Path("/_org/saliogen/bin/qsub3.sh")


class Client:
    """
    Simple client for distributed job execution using qsub3.sh.
    Mimics basic dask.distributed.Client interface.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialize the distributed client.

        Args:
            *args: Ignored (for compatibility)
            **kwargs: Ignored (for compatibility)
        """
        LOG.info("Initialized distributed client using qsub3.sh")
        self._default_threads = kwargs.get('threads_per_worker', 4)
        self._default_ram = kwargs.get('memory_limit', 8)

    def map(self, func: Callable, *iterables, threads: int = None, ram: int = None) -> List[Any]:
        """
        Map a function over iterables in parallel.

        Args:
            func: Function to execute
            *iterables: Iterables to map over
            threads: Threads per job (default from init)
            ram: RAM per job in GB (default from init)

        Returns:
            List of results
        """
        if threads is None:
            threads = self._default_threads
        if ram is None:
            ram = self._default_ram

        # For simple function calls, just execute sequentially
        # In a real implementation, this would serialize tasks to qsub3.sh
        LOG.warning("Distributed.map executing sequentially (qsub3.sh integration not yet implemented)")

        results = []
        for args in zip(*iterables):
            result = func(*args)
            results.append(result)

        return results

    def submit(self, func: Callable, *args, **kwargs) -> 'Future':
        """
        Submit a single function for execution.

        Args:
            func: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Future object representing the computation
        """
        LOG.warning("Distributed.submit executing synchronously")
        result = func(*args, **kwargs)
        return Future(result)

    def gather(self, futures):
        """
        Gather results from futures.

        Args:
            futures: Future or list of futures

        Returns:
            Result or list of results
        """
        if isinstance(futures, list):
            return [f.result() for f in futures]
        return futures.result()

    def close(self):
        """Close the client"""
        LOG.info("Closed distributed client")


class Future:
    """
    Represents a future result of a computation.
    Simple synchronous implementation.
    """

    def __init__(self, result):
        self._result = result

    def result(self):
        """Get the result of the computation"""
        return self._result

    def done(self):
        """Check if computation is complete"""
        return True


def run_jobs_with_qsub(commands: List[str], threads_per_job: int = 4,
                       ram_per_job: int = 8) -> bool:
    """
    Execute a list of commands in parallel using qsub3.sh.

    Args:
        commands: List of shell commands to execute
        threads_per_job: CPU threads to allocate per job
        ram_per_job: RAM in GB to allocate per job

    Returns:
        True if all jobs completed successfully

    Raises:
        RuntimeError: If qsub3.sh execution fails
    """
    if not QSUB_SCRIPT.exists():
        raise RuntimeError(f"qsub3.sh not found at {QSUB_SCRIPT}")

    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        seedfile = Path(f.name)
        for cmd in commands:
            f.write(f"{cmd}\n")

    try:
        LOG.info(f"Executing {len(commands)} jobs with qsub3.sh")
        LOG.info(f"Resources per job: {threads_per_job} threads, {ram_per_job}GB RAM")

        result = subprocess.run(
            ['bash', str(QSUB_SCRIPT),
             '-f', str(seedfile),
             '-t', str(threads_per_job),
             '-r', str(ram_per_job)],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            LOG.error(f"qsub3.sh failed: {result.stderr}")
            raise RuntimeError(f"Job execution failed: {result.stderr}")

        LOG.info("All jobs completed successfully")
        return True

    finally:
        if seedfile.exists():
            seedfile.unlink()


# Create a default client instance for compatibility
_default_client = None


def get_client():
    """
    Get or create the default distributed client.

    Returns:
        Client instance
    """
    global _default_client
    if _default_client is None:
        _default_client = Client()
    return _default_client
