"""
ShellOperation - Base class for operations that execute shell commands
"""

from pathlib import Path
from typing import Dict, Any, List, Union
from abc import ABC, abstractmethod
import subprocess
import tempfile
import os
from ..data_object import DataObject
from ...utils import listify
from ...logging import LOG


class ShellOperation(ABC):
    """
    Base class for operations that execute shell commands.
    Provides structure for input/output specification and command execution.
    """

    def __init__(self, params: Dict[str, Any] = None, **kwargs):
        """
        Initialize the operation with parameters.

        Args:
            params: Dictionary of parameters for this operation
            **kwargs: Additional parameters as keyword arguments
        """
        self._params = self.params()
        if params:
            self._params.update(params)
        if kwargs:
            self._params.update(kwargs)

    @abstractmethod
    def input_spec(self) -> dict:
        """
        Specify required inputs for this operation.

        Returns:
            Dictionary mapping input names to types or specifications
        """
        pass

    @abstractmethod
    def output_spec(self) -> dict:
        """
        Specify outputs produced by this operation.

        Returns:
            Dictionary mapping output names to specifications
        """
        pass

    def params(self) -> dict:
        """
        Specify default parameters for this operation.

        Returns:
            Dictionary of parameter names and default values
        """
        return {}

    @abstractmethod
    def cmd(self, inputs: Dict[str, DataObject], params: Dict[str, Any]) -> Union[dict, List[dict]]:
        """
        Generate the command(s) to execute.

        Args:
            inputs: Dictionary of input DataObjects
            params: Dictionary of parameters

        Returns:
            Command specification dictionary or list of dictionaries
        """
        pass

    def format_args(self, args: Dict[str, Any]) -> List[str]:
        """
        Format a dictionary of arguments into command-line flags.

        Args:
            args: Dictionary of argument names and values

        Returns:
            List of formatted command-line arguments
        """
        formatted = []
        for key, value in args.items():
            if value is True:
                formatted.append(key)
            elif value is False or value is None:
                continue
            else:
                formatted.append(key)
                formatted.append(str(value))
        return formatted

    def run(self, *args, overwrite: bool = False, outputs: Dict = None,
            use_qsub: bool = False, qsub_threads: int = 8, qsub_ram_gb: int = 32, **kwargs) -> Union[DataObject, List[DataObject]]:
        """
        Execute this operation (alias for run_job).

        Args:
            *args: Positional arguments matching input_spec order
            overwrite: Whether to overwrite existing output objects
            outputs: Dictionary specifying output identifiers
            use_qsub: Use qsub3.sh for parallel execution
            qsub_threads: Number of threads per job for qsub3.sh
            qsub_ram_gb: RAM in GB per job for qsub3.sh
            **kwargs: Named arguments matching input_spec

        Returns:
            Output DataObject(s)
        """
        return self.run_job(*args, overwrite=overwrite, outputs=outputs,
                           use_qsub=use_qsub, qsub_threads=qsub_threads, qsub_ram_gb=qsub_ram_gb, **kwargs)

    def run_job(self, *args, overwrite: bool = False, outputs: Dict = None,
                use_qsub: bool = False, qsub_threads: int = 8, qsub_ram_gb: int = 32, **kwargs) -> Union[DataObject, List[DataObject]]:
        """
        Execute this operation.

        Args:
            *args: Positional arguments matching input_spec order
            overwrite: Whether to overwrite existing output objects
            outputs: Dictionary specifying output identifiers
            use_qsub: Use qsub3.sh for parallel execution
            qsub_threads: Number of threads per job for qsub3.sh
            qsub_ram_gb: RAM in GB per job for qsub3.sh
            **kwargs: Named arguments matching input_spec

        Returns:
            Output DataObject(s)
        """
        if overwrite:
            LOG.warning("Overwrite is set to True")

        input_spec = self.input_spec()
        inputs = {}

        input_names = list(input_spec.keys())
        for i, arg in enumerate(args):
            if i < len(input_names):
                inputs[input_names[i]] = arg

        inputs.update(kwargs)

        # Apply transforms specified in input_spec
        for input_name, spec in input_spec.items():
            if input_name in inputs and isinstance(spec, dict) and "transform" in spec:
                transform = spec["transform"]
                if isinstance(transform, dict) and "method" in transform:
                    # Extract the method call
                    method_str = transform["method"]
                    # Handle method calls like "object_by_identifier('bwa')"
                    if "object_by_identifier" in method_str:
                        # Extract the argument
                        import re
                        match = re.search(r"object_by_identifier\(['\"]([^'\"]+)['\"]\)", method_str)
                        if match:
                            identifier = match.group(1)
                            input_value = inputs[input_name]
                            # Apply transform to each item if it's a list
                            if isinstance(input_value, list):
                                inputs[input_name] = [item.object_by_identifier(identifier) for item in input_value]
                            else:
                                inputs[input_name] = input_value.object_by_identifier(identifier)

        # Determine if we should iterate over inputs or pass as-is
        # If input_spec indicates a list type (e.g., [DataObject]), don't split it up
        should_iterate = False
        if input_names:
            first_input_name = input_names[0]
            first_input_spec = input_spec[first_input_name]
            first_input_value = inputs.get(first_input_name)

            # Check if input_spec expects a single object (not a list)
            # and we received a list of objects
            # If spec is [DataObject], it's a list, so isinstance(first_input_spec, list) is True
            # If spec is DataObject or Sequence (a class), isinstance(first_input_spec, type) is True
            if (not isinstance(first_input_spec, list) and
                isinstance(first_input_spec, type) and
                isinstance(first_input_value, list) and
                all(isinstance(item, DataObject) for item in first_input_value)):
                should_iterate = True

        cmd_specs_with_inputs = []
        if should_iterate:
            # Multiple inputs - generate command for each
            first_input_list = listify(inputs[first_input_name])

            # Check if other inputs are also lists that need to be zipped
            # This handles cases where sequence, parent, and genome_index are all lists
            other_lists = {}
            list_length = len(first_input_list)

            for key, value in inputs.items():
                if key != first_input_name and isinstance(value, list) and len(value) == list_length:
                    other_lists[key] = value

            # Iterate with zipping if needed
            for i, item in enumerate(first_input_list):
                single_inputs = inputs.copy()
                single_inputs[first_input_name] = item

                # Zip other list inputs
                for key, value_list in other_lists.items():
                    single_inputs[key] = value_list[i]

                cmd_spec = self.cmd(single_inputs, self._params)
                for spec in listify(cmd_spec):
                    cmd_specs_with_inputs.append((spec, single_inputs))
        else:
            # Single input or list that should be kept as-is
            cmd_spec = self.cmd(inputs, self._params)
            for spec in listify(cmd_spec):
                cmd_specs_with_inputs.append((spec, inputs))

        output_objects = []

        # If using qsub3.sh and have multiple jobs, batch them
        if use_qsub and len(cmd_specs_with_inputs) > 1:
            return self._run_with_qsub(cmd_specs_with_inputs, outputs, qsub_threads, qsub_ram_gb)

        for spec, spec_inputs in cmd_specs_with_inputs:
            cmd_list = spec.get("cmd", [])

            # If cmd is a callable (method reference), call it first
            if callable(cmd_list):
                cmd_list = cmd_list(spec_inputs, self._params)

            if isinstance(cmd_list, list):
                cmd_str = " ".join([str(c) for c in cmd_list])
            else:
                cmd_str = str(cmd_list)

            LOG.info(f"Executing: {cmd_str[:100]}...")

            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)

                try:
                    # Execute runtime hooks if present
                    runtime_hooks = spec.get("runtime", {})
                    env = {"tmp_dir": temp_dir, "cpu": qsub_threads, "ram": qsub_ram_gb * (2**30)}

                    # Collect runtime values for variable replacement
                    runtime_values = {}
                    for hook_name, hook_func in runtime_hooks.items():
                        if callable(hook_func):
                            LOG.info(f"Executing runtime hook: {hook_name}")
                            # Runtime hooks have different signatures - try them in order
                            # Merge self._params and spec_inputs for flexible parameter access
                            merged_params = {**self._params, **spec_inputs}
                            try:
                                # Try (params, inputs, env) first - standard signature
                                hook_result = hook_func(self._params, spec_inputs, env)
                            except (TypeError, KeyError):
                                try:
                                    # Try (params, inputs) without env
                                    hook_result = hook_func(self._params, spec_inputs)
                                except (TypeError, KeyError):
                                    try:
                                        # Try (params, env) - standard signature for MultiQC
                                        hook_result = hook_func(self._params, env)
                                    except (TypeError, KeyError):
                                        # Last resort: try (params) only
                                        hook_result = hook_func(self._params)
                            runtime_values[hook_name] = hook_result
                            LOG.info(f"Runtime hook {hook_name} completed: {hook_result}")

                    # Handle Python expressions and variable replacements in command
                    import re

                    # Create objects for attribute access in expressions
                    env_obj = type('obj', (object,), env)()
                    runtime_obj = type('obj', (object,), runtime_values)()

                    # Create a namespace for evaluation
                    eval_namespace = {
                        "env": env_obj,
                        "int": int,
                        "max": max,
                        "min": min,
                        "runtime": runtime_obj
                    }

                    def replace_placeholder(match):
                        placeholder = match.group(1)
                        # Try simple variable replacement first
                        if placeholder == "env.cpu":
                            return str(qsub_threads)
                        elif placeholder == "env.ram":
                            return str(qsub_ram_gb * (2**30))
                        elif placeholder == "env.tmp_dir":
                            return str(temp_dir)
                        elif placeholder.startswith("runtime."):
                            key = placeholder[8:]  # Remove "runtime." prefix
                            return str(runtime_values.get(key, match.group(0)))
                        else:
                            # Try to evaluate as Python expression
                            try:
                                result = eval(placeholder, {"__builtins__": {}}, eval_namespace)
                                return str(result)
                            except:
                                return match.group(0)  # Return original if evaluation fails

                    cmd_str = re.sub(r'\{([^}]+)\}', replace_placeholder, cmd_str)

                    # Replace picard with Java jar command (apt picard is the wrong tool)
                    # The pattern matches: picard -Xmx...G and converts to: java -Xmx...G -jar picard.jar
                    import re as regex_module
                    cmd_str = regex_module.sub(
                        r'picard\s+(-Xmx\S+)',
                        r'java \1 -jar /_org/saliogen/bin/picard.jar',
                        cmd_str
                    )

                    # Prepare environment with conda paths and HOMER
                    proc_env = os.environ.copy()
                    # Ensure conda bin is in PATH - prepend to command string
                    conda_prefix = os.environ.get('CONDA_PREFIX', '/home/edward/anaconda3/envs/saliogen')
                    conda_bin = f"{conda_prefix}/bin"
                    # Add HOMER bin directory to PATH
                    from ...config import config
                    homer_bin = str(config.homer_bin_directory)
                    # Prepend PATH setting to command
                    cmd_str = f'export PATH={homer_bin}:{conda_bin}:$PATH && {cmd_str}'

                    # Log the full command (first 500 chars for readability)
                    LOG.info(f"Executing command: {cmd_str[:500]}...")
                    if len(cmd_str) > 500:
                        LOG.debug(f"Full command: {cmd_str}")

                    result = subprocess.run(
                        ['bash', '-c', cmd_str],
                        cwd=temp_dir,
                        capture_output=True,
                        text=True,
                        env=proc_env
                    )

                    if result.returncode != 0:
                        LOG.error(f"Command failed with return code {result.returncode}")
                        LOG.error(f"STDERR: {result.stderr}")
                        raise RuntimeError(f"Command execution failed: {result.stderr}")

                    output_spec = self.output_spec()
                    for output_name, output_config in output_spec.items():
                        if outputs and output_name in outputs:
                            identifier = outputs[output_name]
                        elif isinstance(output_config, dict) and "identifier" in output_config:
                            identifier = output_config["identifier"]
                        else:
                            identifier = f"{self.__class__.__name__}_output"

                        output_type = output_config.get("type", DataObject) if isinstance(output_config, dict) else DataObject
                        parent = spec_inputs.get(output_config.get("parent")) if isinstance(output_config, dict) and "parent" in output_config else None

                        files_spec = output_config.get("files") if isinstance(output_config, dict) else None
                        if callable(files_spec):
                            files_to_add = files_spec(temp_path)
                        elif isinstance(files_spec, dict):
                            # files_spec is a dict mapping glob patterns to file metadata
                            files_to_add = []
                            for pattern, file_metadata in files_spec.items():
                                matching_files = list(temp_path.glob(pattern))
                                for file_path in matching_files:
                                    file_dict = {"file_path": file_path}
                                    if isinstance(file_metadata, dict):
                                        if "type" in file_metadata:
                                            file_dict["type"] = file_metadata["type"]
                                        if "subtypes" in file_metadata:
                                            file_dict["subtypes"] = file_metadata["subtypes"]
                                    files_to_add.append(file_dict)
                        else:
                            files_to_add = list(temp_path.glob("*"))

                        output_obj = output_type.create_from_files(
                            identifier=identifier,
                            files=files_to_add,
                            parent=parent,
                            keep_original=False
                        )
                        output_objects.append(output_obj)

                except Exception as e:
                    LOG.error(f"Operation failed: {str(e)}")
                    raise

        if len(output_objects) == 1:
            return output_objects[0]
        return output_objects

    def _run_with_qsub(self, cmd_specs_with_inputs: List, outputs: Dict, threads: int, ram_gb: int) -> Union[DataObject, List[DataObject]]:
        """
        Execute commands in parallel using qsub3.sh.

        Args:
            cmd_specs_with_inputs: List of (spec, inputs) tuples
            outputs: Output specifications
            threads: Number of threads per job
            ram_gb: RAM in GB per job

        Returns:
            List of output DataObjects
        """
        import tempfile
        from pathlib import Path

        LOG.info(f"Running {len(cmd_specs_with_inputs)} jobs in parallel using qsub3.sh")
        LOG.info(f"Resources per job: {threads} threads, {ram_gb}GB RAM")

        # Create a temporary directory to hold all job directories
        with tempfile.TemporaryDirectory() as main_temp_dir:
            main_temp_path = Path(main_temp_dir)
            seed_file = main_temp_path / "qsub_seed.txt"
            job_commands = []
            job_data = []  # Store (spec, spec_inputs, job_dir) for each job

            # Prepare each job
            for i, (spec, spec_inputs) in enumerate(cmd_specs_with_inputs):
                job_dir = main_temp_path / f"job_{i}"
                job_dir.mkdir()

                # Execute runtime hooks if present
                runtime_hooks = spec.get("runtime", {})
                env = {"tmp_dir": str(job_dir), "cpu": threads, "ram": ram_gb * (2**30)}

                # Collect runtime values for variable replacement
                runtime_values = {}
                for hook_name, hook_func in runtime_hooks.items():
                    if callable(hook_func):
                        LOG.debug(f"Job {i}: Executing runtime hook: {hook_name}")
                        # Runtime hooks have different signatures - try them in order
                        # Merge self._params and spec_inputs for flexible parameter access
                        merged_params = {**self._params, **spec_inputs}
                        try:
                            # Try (params, inputs, env) first - standard signature
                            result = hook_func(self._params, spec_inputs, env)
                        except (TypeError, KeyError):
                            try:
                                # Try (params, inputs) without env
                                result = hook_func(self._params, spec_inputs)
                            except (TypeError, KeyError):
                                try:
                                    # Try (params, env) - pass merged params for operations like MultiQC
                                    result = hook_func(merged_params, env)
                                except (TypeError, KeyError):
                                    # Last resort: try (params) only
                                    result = hook_func(merged_params)
                        runtime_values[hook_name] = result

                # Build command string
                cmd_list = spec.get("cmd", [])

                # If cmd is a callable (method reference), call it first
                if callable(cmd_list):
                    cmd_list = cmd_list(spec_inputs, self._params)

                if isinstance(cmd_list, list):
                    cmd_str = " ".join([str(c) for c in cmd_list])
                else:
                    cmd_str = str(cmd_list)

                # Handle Python expressions and variable replacements in command
                import re

                # Create objects for attribute access in expressions
                env_obj = type('obj', (object,), env)()
                runtime_obj = type('obj', (object,), runtime_values)()

                # Create a namespace for evaluation
                eval_namespace = {
                    "env": env_obj,
                    "int": int,
                    "max": max,
                    "min": min,
                    "runtime": runtime_obj
                }

                def replace_placeholder(match):
                    placeholder = match.group(1)
                    # Try simple variable replacement first
                    if placeholder == "env.cpu":
                        return str(threads)
                    elif placeholder == "env.ram":
                        return str(ram_gb * (2**30))
                    elif placeholder == "env.tmp_dir":
                        return str(job_dir)
                    elif placeholder.startswith("runtime."):
                        key = placeholder[8:]  # Remove "runtime." prefix
                        return str(runtime_values.get(key, match.group(0)))
                    else:
                        # Try to evaluate as Python expression
                        try:
                            result = eval(placeholder, {"__builtins__": {}}, eval_namespace)
                            return str(result)
                        except:
                            return match.group(0)  # Return original if evaluation fails

                cmd_str = re.sub(r'\{([^}]+)\}', replace_placeholder, cmd_str)

                # Replace picard with Java jar command (apt picard is the wrong tool)
                # The pattern matches: picard -Xmx...G and converts to: java -Xmx...G -jar picard.jar
                import re as regex_module
                cmd_str = regex_module.sub(
                    r'picard\s+(-Xmx\S+)',
                    r'java \1 -jar /_org/saliogen/bin/picard.jar',
                    cmd_str
                )

                # Log the command for this job
                LOG.info(f"Job {i} command: {cmd_str[:500]}...")
                if len(cmd_str) > 500:
                    LOG.debug(f"Job {i} full command: {cmd_str}")

                # Ensure conda bin and HOMER bin are in PATH for qsub jobs
                conda_prefix = os.environ.get('CONDA_PREFIX', '/home/edward/anaconda3/envs/saliogen')
                conda_bin = f"{conda_prefix}/bin"
                from ...config import config
                homer_bin = str(config.homer_bin_directory)

                # Create a wrapper script for this job that changes to job directory and sets PATH
                job_script = f"export PATH={homer_bin}:{conda_bin}:$PATH && cd {job_dir} && {cmd_str}"
                job_commands.append(job_script)
                job_data.append((spec, spec_inputs, job_dir))

            # Write seed file
            with open(seed_file, 'w') as f:
                for cmd in job_commands:
                    f.write(cmd + '\n')

            LOG.info(f"Created seed file with {len(job_commands)} commands: {seed_file}")

            # Execute qsub3.sh
            qsub_cmd = [
                "bash", "/_org/saliogen/bin/qsub3.sh",
                "-f", str(seed_file),
                "-t", str(threads),
                "-r", str(ram_gb)
            ]

            # Prepare environment with conda paths
            proc_env = os.environ.copy()
            # Ensure conda bin is in PATH
            conda_prefix = os.environ.get('CONDA_PREFIX', '/home/edward/anaconda3/envs/saliogen')
            conda_bin = f"{conda_prefix}/bin"
            if conda_bin not in proc_env.get('PATH', ''):
                proc_env['PATH'] = f"{conda_bin}:{proc_env.get('PATH', '')}"

            LOG.info(f"Executing: {' '.join(qsub_cmd)}")
            result = subprocess.run(
                qsub_cmd,
                capture_output=True,
                text=True,
                env=proc_env
            )

            if result.returncode != 0:
                LOG.error(f"qsub3.sh failed with return code {result.returncode}")
                LOG.error(f"STDERR: {result.stderr}")
                LOG.error(f"STDOUT: {result.stdout}")
                raise RuntimeError(f"qsub3.sh execution failed: {result.stderr}")

            LOG.info("qsub3.sh completed successfully")
            LOG.info(f"STDOUT: {result.stdout}")

            # Process outputs for each job
            output_objects = []
            for job_idx, (spec, spec_inputs, job_dir) in enumerate(job_data):
                output_spec = self.output_spec()

                # Handle outputs as either a list (one per job) or a single dict
                job_outputs = None
                if outputs:
                    if isinstance(outputs, list) and len(outputs) > job_idx:
                        job_outputs = outputs[job_idx]
                    elif isinstance(outputs, dict):
                        job_outputs = outputs

                for output_name, output_config in output_spec.items():
                    if job_outputs and output_name in job_outputs:
                        identifier = job_outputs[output_name]
                    elif isinstance(output_config, dict) and "identifier" in output_config:
                        identifier = output_config["identifier"]
                    else:
                        identifier = f"{self.__class__.__name__}_output"

                    output_type = output_config.get("type", DataObject) if isinstance(output_config, dict) else DataObject
                    parent = spec_inputs.get(output_config.get("parent")) if isinstance(output_config, dict) and "parent" in output_config else None

                    files_spec = output_config.get("files") if isinstance(output_config, dict) else None
                    if callable(files_spec):
                        files_to_add = files_spec(job_dir)
                    elif isinstance(files_spec, dict):
                        # files_spec is a dict mapping glob patterns to file metadata
                        files_to_add = []
                        for pattern, file_metadata in files_spec.items():
                            matching_files = list(job_dir.glob(pattern))
                            for file_path in matching_files:
                                file_dict = {"file_path": file_path}
                                if isinstance(file_metadata, dict):
                                    if "type" in file_metadata:
                                        file_dict["type"] = file_metadata["type"]
                                    if "subtypes" in file_metadata:
                                        file_dict["subtypes"] = file_metadata["subtypes"]
                                files_to_add.append(file_dict)
                    else:
                        files_to_add = list(job_dir.glob("*"))

                    output_obj = output_type.create_from_files(
                        identifier=identifier,
                        files=files_to_add,
                        parent=parent,
                        keep_original=False
                    )
                    output_objects.append(output_obj)

        if len(output_objects) == 1:
            return output_objects[0]
        return output_objects
