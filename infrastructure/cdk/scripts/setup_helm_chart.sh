#!/bin/bash
# =============================================================================
# HyperPod Helm Chart Setup Script
# =============================================================================
# This script downloads and prepares the HyperPod Helm Chart for CDK deployment.
# Run this script before deploying EksStack to ensure Helm Chart is available.
#
# Usage: ./scripts/setup_helm_chart.sh
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CDK_DIR="$(dirname "$SCRIPT_DIR")"
HELM_CHARTS_DIR="$CDK_DIR/helm_charts"
TEMP_DIR="$CDK_DIR/.tmp_hyperpod_cli"
HYPERPOD_CLI_REPO="https://github.com/aws/sagemaker-hyperpod-cli.git"

echo "=============================================="
echo "HyperPod Helm Chart Setup"
echo "=============================================="

# Check if helm is installed
if ! command -v helm &> /dev/null; then
    echo "❌ Error: helm is not installed. Please install helm first."
    echo "   Install with: brew install helm (macOS) or see https://helm.sh/docs/intro/install/"
    exit 1
fi

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo "❌ Error: git is not installed. Please install git first."
    exit 1
fi

# Create helm_charts directory if not exists
mkdir -p "$HELM_CHARTS_DIR"

# Clean up any existing temp directory
rm -rf "$TEMP_DIR"

echo "📦 Cloning sagemaker-hyperpod-cli repository..."
git clone --depth 1 "$HYPERPOD_CLI_REPO" "$TEMP_DIR"

echo "📂 Copying Helm Chart to helm_charts directory..."
rm -rf "$HELM_CHARTS_DIR/HyperPodHelmChart"
cp -r "$TEMP_DIR/helm_chart/HyperPodHelmChart" "$HELM_CHARTS_DIR/"

echo "🔧 Updating Helm dependencies..."
cd "$HELM_CHARTS_DIR/HyperPodHelmChart"
helm dependency update

echo "🧹 Cleaning up temporary files..."
rm -rf "$TEMP_DIR"

echo ""
echo "=============================================="
echo "✅ HyperPod Helm Chart setup complete!"
echo "=============================================="
echo ""
echo "Helm Chart location: $HELM_CHARTS_DIR/HyperPodHelmChart"
echo ""
echo "Next steps:"
echo "  1. Deploy EksStack: cdk deploy EksStack"
echo "  2. HelmChart will be automatically installed during EKS deployment"
echo ""
