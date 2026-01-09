#!/bin/bash
# HyperPod Lifecycle Script - on_create.sh
# This script runs when instances are created in the HyperPod cluster

set -e

echo "Starting HyperPod instance initialization..."
echo "Timestamp: $(date)"
echo "Hostname: $(hostname)"

# Log instance metadata
echo "Instance initialization complete."
