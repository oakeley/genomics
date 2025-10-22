#!/bin/bash

# Function to print usage
print_usage() {
    echo "Usage: $0 -f <seedfile> -t <threads_per_job> -r <ram_per_job_gb>"
    echo "  -f: Input file containing commands (one per line)"
    echo "  -t: Number of threads to allocate per job"
    echo "  -r: Amount of RAM in GB to allocate per job"
    exit 1
}

# Parse command line arguments
while getopts "f:t:r:" opt; do
    case $opt in
        f) SEEDFILE="$OPTARG";;
        t) THREADS_PER_JOB="$OPTARG";;
        r) RAM_PER_JOB="$OPTARG";;
        *) print_usage;;
    esac
done

# Validate inputs
if [ -z "$SEEDFILE" ] || [ -z "$THREADS_PER_JOB" ] || [ -z "$RAM_PER_JOB" ]; then
    print_usage
fi

if [ ! -f "$SEEDFILE" ]; then
    echo "Error: Seed file '$SEEDFILE' not found"
    exit 1
fi

# Get system resources
TOTAL_THREADS=$(nproc)
TOTAL_RAM=$(free -g | awk '/^Mem:/{print $2}')
RESERVED_THREADS=2
RESERVED_RAM=4

# Calculate available resources
AVAILABLE_THREADS=$((TOTAL_THREADS - RESERVED_THREADS))
AVAILABLE_RAM=$((TOTAL_RAM - RESERVED_RAM))

echo "System resources:"
echo "Total CPU threads: $TOTAL_THREADS (reserving $RESERVED_THREADS)"
echo "Total RAM (GB): $TOTAL_RAM (reserving $RESERVED_RAM GB)"
echo "Available threads: $AVAILABLE_THREADS"
echo "Available RAM (GB): $AVAILABLE_RAM"

# Directory for job tracking
JOBDIR=".jobs_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$JOBDIR"

# Function to count active jobs
count_active_jobs() {
    ls "$JOBDIR"/*.pid 2>/dev/null | wc -l
}

# Function to get available resources
get_available_resources() {
    local active_jobs=$(count_active_jobs)
    local used_threads=$((active_jobs * THREADS_PER_JOB))
    local used_ram=$((active_jobs * RAM_PER_JOB))
    
    echo "$((AVAILABLE_THREADS - used_threads)) $((AVAILABLE_RAM - used_ram))"
}

# Function to clean up completed jobs
cleanup_completed_jobs() {
    for pidfile in "$JOBDIR"/*.pid; do
        if [ -f "$pidfile" ]; then
            pid=$(cat "$pidfile")
            if ! kill -0 "$pid" 2>/dev/null; then
                rm "$pidfile"
            fi
        fi
    done
}

# Function to launch a job
launch_job() {
    local cmd="$1"
    local job_id="$2"
    
    # Launch the command in background
    bash -c "$cmd" > "$JOBDIR/job_${job_id}.out" 2> "$JOBDIR/job_${job_id}.err" & 
    local pid=$!
    echo $pid > "$JOBDIR/job_${job_id}.pid"
    echo "Launched job $job_id (PID: $pid): $cmd"
}

# Main job processing loop
job_id=1
while IFS= read -r cmd || [ -n "$cmd" ]; do
    # Skip empty lines
    [ -z "$cmd" ] && continue
    
    while true; do
        # Clean up completed jobs
        cleanup_completed_jobs
        
        # Get available resources
        read avail_threads avail_ram <<< $(get_available_resources)
        
        # Check if we have enough resources
        if [ "$avail_threads" -ge "$THREADS_PER_JOB" ] && [ "$avail_ram" -ge "$RAM_PER_JOB" ]; then
            launch_job "$cmd" "$job_id"
            job_id=$((job_id + 1))
            break
        else
            echo "Waiting for resources (need ${THREADS_PER_JOB} threads and ${RAM_PER_JOB}GB RAM)"
            sleep 5
        fi
    done
done < "$SEEDFILE"

# Wait for all jobs to complete
echo "Waiting for all jobs to complete..."
while [ $(count_active_jobs) -gt 0 ]; do
    cleanup_completed_jobs
    sleep 5
done

echo "All jobs completed!"
echo "Output files are in $JOBDIR/"
