#!/usr/bin/env bash
# Quick HyperPod Infrastructure Validation
# Reference: tasks.md T008g

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TESTS_DIR="$(dirname "$SCRIPT_DIR")"
REPORT_FILE="${TESTS_DIR}/reports/infrastructure-validation-report.md"

# Ensure reports directory exists
mkdir -p "${TESTS_DIR}/reports"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Counters
PASSED=0
FAILED=0
WARNINGS=0

pass() {
    printf "${GREEN}[✅ PASS]${NC} %s\n" "$1"
    PASSED=$((PASSED + 1))
}

fail() {
    printf "${RED}[❌ FAIL]${NC} %s\n" "$1"
    FAILED=$((FAILED + 1))
}

warn() {
    printf "${YELLOW}[⚠️ WARN]${NC} %s\n" "$1"
    WARNINGS=$((WARNINGS + 1))
}

info() {
    printf "${BLUE}[INFO]${NC} %s\n" "$1"
}

echo ""
echo "╔═══════════════════════════════════════════════════════════════════════════╗"
echo "║        HyperPod Quick Infrastructure Validation                           ║"
echo "║        Reference: tasks.md T008g                                          ║"
echo "╚═══════════════════════════════════════════════════════════════════════════╝"
echo ""

# Start report
TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S %Z")
CLUSTER_CTX=$(kubectl config current-context 2>/dev/null || echo "Unknown")

echo "# HyperPod Infrastructure Validation Report" > "$REPORT_FILE"
echo "" >> "$REPORT_FILE"
echo "**Reference**: tasks.md T008g" >> "$REPORT_FILE"
echo "**Generated**: $TIMESTAMP" >> "$REPORT_FILE"
echo "**Cluster**: $CLUSTER_CTX" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"
echo "---" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

# ============================================================================
# 1. Cluster Health
# ============================================================================
info "========== 1. Cluster Health Check =========="

echo "## 1. Cluster Health" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"
echo "| Check | Status |" >> "$REPORT_FILE"
echo "|-------|--------|" >> "$REPORT_FILE"

# Check kubectl connectivity
if kubectl cluster-info > /dev/null 2>&1; then
    pass "Cluster API reachable"
    echo "| Cluster API | ✅ Reachable |" >> "$REPORT_FILE"
else
    fail "Cannot connect to cluster"
    echo "| Cluster API | ❌ Unreachable |" >> "$REPORT_FILE"
fi

# Check nodes
TOTAL_NODES=$(kubectl get nodes --no-headers 2>/dev/null | wc -l | tr -d ' ')
READY_NODES=$(kubectl get nodes --no-headers 2>/dev/null | grep -c " Ready" 2>/dev/null || echo "0")

if [ "$TOTAL_NODES" -gt 0 ] && [ "$READY_NODES" = "$TOTAL_NODES" ]; then
    pass "All $TOTAL_NODES nodes Ready"
    echo "| Nodes | ✅ $READY_NODES/$TOTAL_NODES Ready |" >> "$REPORT_FILE"
else
    fail "Nodes not ready: $READY_NODES/$TOTAL_NODES"
    echo "| Nodes | ❌ $READY_NODES/$TOTAL_NODES Ready |" >> "$REPORT_FILE"
fi

# Check CoreDNS
COREDNS_PODS=$(kubectl get pods -n kube-system -l k8s-app=kube-dns --no-headers 2>/dev/null | grep -c "Running" 2>/dev/null || echo "0")
if [ "$COREDNS_PODS" -gt 0 ]; then
    pass "CoreDNS running ($COREDNS_PODS pods)"
    echo "| CoreDNS | ✅ $COREDNS_PODS pods |" >> "$REPORT_FILE"
else
    fail "CoreDNS not running"
    echo "| CoreDNS | ❌ Not running |" >> "$REPORT_FILE"
fi

echo ""

# ============================================================================
# 2. HyperPod Add-ons
# ============================================================================
info "========== 2. HyperPod Add-ons =========="

echo "" >> "$REPORT_FILE"
echo "## 2. HyperPod Add-ons" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"
echo "| Component | Status |" >> "$REPORT_FILE"
echo "|-----------|--------|" >> "$REPORT_FILE"

# Training Operator
if kubectl get crd pytorchjobs.kubeflow.org > /dev/null 2>&1; then
    pass "Training Operator - PyTorchJob CRD"
    echo "| Training Operator | ✅ PyTorchJob CRD |" >> "$REPORT_FILE"
else
    fail "Training Operator - PyTorchJob CRD not found"
    echo "| Training Operator | ❌ CRD not found |" >> "$REPORT_FILE"
fi

# Kueue
if kubectl get crd clusterqueues.kueue.x-k8s.io > /dev/null 2>&1; then
    KUEUE_PODS=$(kubectl get pods -n kueue-system --no-headers 2>/dev/null | grep -c "Running" 2>/dev/null || echo "0")
    pass "Kueue - CRD registered ($KUEUE_PODS pods)"
    echo "| Kueue | ✅ CRD + $KUEUE_PODS pods |" >> "$REPORT_FILE"
else
    fail "Kueue CRD not found"
    echo "| Kueue | ❌ CRD not found |" >> "$REPORT_FILE"
fi

# ClusterQueues
CQ_COUNT=$(kubectl get clusterqueues --no-headers 2>/dev/null | wc -l | tr -d ' ')
if [ "$CQ_COUNT" -gt 0 ]; then
    pass "ClusterQueues ($CQ_COUNT configured)"
    echo "| ClusterQueues | ✅ $CQ_COUNT configured |" >> "$REPORT_FILE"
else
    warn "No ClusterQueues configured"
    echo "| ClusterQueues | ⚠️ None |" >> "$REPORT_FILE"
fi

# Observability
OBS_PODS=$(kubectl get pods -n hyperpod-observability --no-headers 2>/dev/null | grep -c "Running" 2>/dev/null || echo "0")
if [ "$OBS_PODS" -gt 0 ]; then
    pass "HyperPod Observability ($OBS_PODS pods)"
    echo "| Observability | ✅ $OBS_PODS pods |" >> "$REPORT_FILE"
else
    fail "HyperPod Observability not running"
    echo "| Observability | ❌ Not running |" >> "$REPORT_FILE"
fi

echo ""

# ============================================================================
# 3. GPU Nodes
# ============================================================================
info "========== 3. GPU Nodes =========="

echo "" >> "$REPORT_FILE"
echo "## 3. GPU Resources" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

GPU_TOTAL=$(kubectl get nodes -o json 2>/dev/null | jq '[.items[].status.allocatable["nvidia.com/gpu"] // "0" | tonumber] | add' 2>/dev/null || echo "0")
if [ "$GPU_TOTAL" -gt 0 ]; then
    pass "GPU resources ($GPU_TOTAL GPUs)"
    echo "| GPU Total | ✅ $GPU_TOTAL GPUs |" >> "$REPORT_FILE"
else
    warn "No GPU nodes (0 GPUs) - CPU-only cluster"
    echo "| GPU Total | ⚠️ 0 (CPU cluster) |" >> "$REPORT_FILE"
fi

echo ""

# ============================================================================
# 4. FSx Storage
# ============================================================================
info "========== 4. FSx for Lustre =========="

echo "" >> "$REPORT_FILE"
echo "## 4. FSx for Lustre" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"
echo "| Check | Status |" >> "$REPORT_FILE"
echo "|-------|--------|" >> "$REPORT_FILE"

# FSx CSI Driver
FSX_CSI=$(kubectl get pods -n kube-system -l app.kubernetes.io/name=aws-fsx-csi-driver --no-headers 2>/dev/null | grep -c "Running" 2>/dev/null || echo "0")
if [ "$FSX_CSI" -gt 0 ]; then
    pass "FSx CSI Driver ($FSX_CSI pods)"
    echo "| FSx CSI | ✅ $FSX_CSI pods |" >> "$REPORT_FILE"
else
    fail "FSx CSI Driver not running"
    echo "| FSx CSI | ❌ Not running |" >> "$REPORT_FILE"
fi

# FSx StorageClass
if kubectl get storageclass fsx-lustre > /dev/null 2>&1; then
    pass "FSx StorageClass 'fsx-lustre'"
    echo "| StorageClass | ✅ fsx-lustre |" >> "$REPORT_FILE"
else
    warn "FSx StorageClass not found"
    echo "| StorageClass | ⚠️ Not found |" >> "$REPORT_FILE"
fi

# FSx filesystem via AWS CLI
FSX_FS=$(aws fsx describe-file-systems --query 'FileSystems[?FileSystemType==`LUSTRE`].FileSystemId' --output text 2>/dev/null | wc -w | tr -d ' ')
if [ "$FSX_FS" -gt 0 ]; then
    FSX_ID=$(aws fsx describe-file-systems --query 'FileSystems[?FileSystemType==`LUSTRE`].FileSystemId' --output text 2>/dev/null | awk '{print $1}')
    pass "FSx Lustre filesystem ($FSX_ID)"
    echo "| FSx Filesystem | ✅ $FSX_ID |" >> "$REPORT_FILE"
else
    warn "No FSx Lustre filesystem"
    echo "| FSx Filesystem | ⚠️ Not found |" >> "$REPORT_FILE"
fi

echo ""

# ============================================================================
# 5. VPC Endpoints
# ============================================================================
info "========== 5. Network =========="

echo "" >> "$REPORT_FILE"
echo "## 5. Network" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

VPC_ENDPOINTS=$(aws ec2 describe-vpc-endpoints --query 'VpcEndpoints[].VpcEndpointId' --output text 2>/dev/null | wc -w | tr -d ' ')
if [ "$VPC_ENDPOINTS" -gt 5 ]; then
    pass "VPC Endpoints ($VPC_ENDPOINTS configured)"
    echo "| VPC Endpoints | ✅ $VPC_ENDPOINTS |" >> "$REPORT_FILE"
else
    warn "Few VPC Endpoints ($VPC_ENDPOINTS)"
    echo "| VPC Endpoints | ⚠️ $VPC_ENDPOINTS |" >> "$REPORT_FILE"
fi

echo ""

# ============================================================================
# Summary
# ============================================================================
echo "============================================================================"
echo "                          Validation Summary"
echo "============================================================================"
echo ""
printf "  ${GREEN}Passed:${NC}   %d\n" "$PASSED"
printf "  ${RED}Failed:${NC}   %d\n" "$FAILED"
printf "  ${YELLOW}Warnings:${NC} %d\n" "$WARNINGS"
echo ""

# Complete report
echo "" >> "$REPORT_FILE"
echo "---" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"
echo "## Summary" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"
echo "| Metric | Count |" >> "$REPORT_FILE"
echo "|--------|-------|" >> "$REPORT_FILE"
echo "| ✅ Passed | $PASSED |" >> "$REPORT_FILE"
echo "| ❌ Failed | $FAILED |" >> "$REPORT_FILE"
echo "| ⚠️ Warnings | $WARNINGS |" >> "$REPORT_FILE"

if [ "$FAILED" -eq 0 ]; then
    printf "${GREEN}✅ All critical checks passed! Infrastructure is ready.${NC}\n"
    echo "" >> "$REPORT_FILE"
    echo "**Status**: ✅ All critical checks passed!" >> "$REPORT_FILE"
    exit 0
else
    printf "${RED}❌ Some critical checks failed.${NC}\n"
    echo "" >> "$REPORT_FILE"
    echo "**Status**: ❌ Some checks failed" >> "$REPORT_FILE"
    exit 1
fi
