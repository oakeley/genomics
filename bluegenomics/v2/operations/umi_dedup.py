"""
UMI-based deduplication for paired-end sequencing data
"""

from pathlib import Path
from typing import Dict, Any
from .shell_operation import ShellOperation
from ..sequence import Sequence


class DeduplicateByUMI(ShellOperation):
    """
    Deduplicate paired-end reads using UMI from fastq headers.
    UMIs are extracted from the last field of the read ID (colon-separated).
    Uses hash table to track seen UMIs and filter duplicates.
    """

    def input_spec(self) -> dict:
        return {
            "sequence": Sequence,
        }

    def output_spec(self) -> dict:
        return {
            "deduped_sequence": {
                "type": Sequence,
                "parent": "sequence",
                "files": {
                    "*_R1_dedup.fastq": {
                        "type": "fastq",
                        "subtypes": {"read": 0, "lane": 0},
                    },
                    "*_R2_dedup.fastq": {
                        "type": "fastq",
                        "subtypes": {"read": 1, "lane": 0},
                    },
                    "*_dedup_stats.log": {
                        "type": "log",
                    }
                }
            }
        }

    def params(self) -> dict:
        return {}

    def cmd(self, inputs: Dict[str, Any], params: Dict[str, Any]) -> dict:
        """
        Generate command to deduplicate reads by UMI using hash table approach.
        """
        import base64

        sequence = inputs["sequence"]
        fastq1 = sequence.files('fastq', subtypes={'read': 0})
        fastq2 = sequence.files('fastq', subtypes={'read': 1})

        # Python script for UMI-based deduplication
        script = f"""#!/usr/bin/env python3
import gzip
import sys

def extract_umi_from_header(header):
    read_id = header.strip().split()[0][1:]
    fields = read_id.split(':')
    return fields[-1] if fields else None

def deduplicate_fastq_by_umi(r1_path, r2_path, r1_out_path, r2_out_path, log_path):
    seen_umis = set()
    total_reads = 0
    unique_reads = 0
    duplicate_reads = 0

    r1_open = gzip.open if r1_path.endswith('.gz') else open
    r2_open = gzip.open if r2_path.endswith('.gz') else open

    with r1_open(r1_path, 'rt') as r1_in, \\
         r2_open(r2_path, 'rt') as r2_in, \\
         open(r1_out_path, 'w') as r1_out, \\
         open(r2_out_path, 'w') as r2_out, \\
         open(log_path, 'w') as log:

        log.write('Starting UMI-based deduplication\\n')
        log.write(f'R1 input: {{r1_path}}\\n')
        log.write(f'R2 input: {{r2_path}}\\n\\n')

        while True:
            r1_header = r1_in.readline()
            if not r1_header:
                break
            r1_seq = r1_in.readline()
            r1_plus = r1_in.readline()
            r1_qual = r1_in.readline()

            r2_header = r2_in.readline()
            r2_seq = r2_in.readline()
            r2_plus = r2_in.readline()
            r2_qual = r2_in.readline()

            total_reads += 1

            umi = extract_umi_from_header(r1_header)

            if umi and umi not in seen_umis:
                seen_umis.add(umi)
                unique_reads += 1

                r1_out.write(r1_header)
                r1_out.write(r1_seq)
                r1_out.write(r1_plus)
                r1_out.write(r1_qual)

                r2_out.write(r2_header)
                r2_out.write(r2_seq)
                r2_out.write(r2_plus)
                r2_out.write(r2_qual)
            else:
                duplicate_reads += 1

            if total_reads % 100000 == 0:
                log.write(f'Processed {{total_reads:,}} reads, {{unique_reads:,}} unique, {{duplicate_reads:,}} duplicates\\n')
                log.flush()

        log.write('\\nDeduplication complete\\n')
        log.write(f'Total reads: {{total_reads:,}}\\n')
        log.write(f'Unique reads: {{unique_reads:,}}\\n')
        log.write(f'Duplicate reads: {{duplicate_reads:,}}\\n')
        log.write(f'Deduplication rate: {{(duplicate_reads/total_reads*100) if total_reads > 0 else 0:.2f}}%\\n')
        log.write(f'Unique UMIs: {{len(seen_umis):,}}\\n')

if __name__ == '__main__':
    deduplicate_fastq_by_umi(
        r1_path='{fastq1}',
        r2_path='{fastq2}',
        r1_out_path='{sequence.identifier()}_R1_dedup.fastq',
        r2_out_path='{sequence.identifier()}_R2_dedup.fastq',
        log_path='{sequence.identifier()}_dedup_stats.log'
    )
"""

        encoded_script = base64.b64encode(script.encode()).decode()

        cmd = [
            "echo", encoded_script, "|", "base64", "-d", ">", "dedup_umi.py", ";",
            "python3", "dedup_umi.py", ";"
        ]

        return {
            "outputs": ["deduped_sequence"],
            "inputs": ["sequence"],
            "cmd": cmd
        }

    def task_display_name(self, inputs, params):
        return inputs["sequence"]._path.parts[5] if len(inputs["sequence"]._path.parts) > 5 else inputs["sequence"].identifier()
