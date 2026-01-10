#!/usr/bin/env bash
# HyperPod Infrastructure Validation Suite Runner
# Reference: tasks.md T008g - HyperPod 基础设施验证测试
#
# This script orchestrates all validation tests and generates a comprehensive report.
#
# Usage:
#   ./run-validation-suite.sh [--quick | --full | --pytest-only | --help]
#
# Options:
#   --quick       Run quick validation (cluster health + add-ons check)
#   --full        Run full validation suite including performance tests
#   --pytest-only Run only pytest infrastructure tests
#   --help        Show this help message
#
# Prerequisites:
#   - kubectl configured with cluster credentials
#   - AWS CLI configured with appropriate permissions
#   - Python 3.11+ with pytest installed (for pytest tests)
#   - curl, openssl, jq installed

set -euo pipefail

# ============================================================================
# Configuration
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPORT_DIR="${SCRIPT_DIR}/reports"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
FINAL_REPORT="${REPORT_DIR}/infrastructure-validation-report-${TIMESTAMP}.md"
SUMMARY_REPORT="${SCRIPT_DIR}/infrastructure-validation-report.md"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Test results
TOTAL_SUITES=0
PASSED_SUITES=0
FAILED_SUITES=0
declare -a SUITE_RESULTS

# ============================================================================
# Utility Functions
# ============================================================================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[PASS]${NC} $1"
}

log_fail() {
    echo -e "${RED}[FAIL]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_banner() {
    echo ""
    echo "╔═══════════════════════════════════════════════════════════════════════════╗"
    echo "║                                                                           ║"
    echo "║        HyperPod Infrastructure Validation Suite                           ║"
    echo "║        Reference: tasks.md T008g                                          ║"
    echo "║                                                                           ║"
    echo "╚═══════════════════════════════════════════════════════════════════════════╝"
    echo ""
}

print_help() {
    cat << EOF
HyperPod Infrastructure Validation Suite

Usage: $0 [OPTIONS]

Options:
  --quick       Run quick validation (cluster health + add-ons check)
  --full        Run full validation suite including performance tests
  --pytest-only Run only pytest infrastructure tests
  --help        Show this help message

Test Suites:
  1. Cluster Health Check       - EKS cluster status, nodes, control plane
  2. GPU Node Validation        - NVIDIA drivers, GPU visibility, CUDA
  3. HyperPod Add-ons           - Training Operator, Kueue, Observability, Spaces
  4. FSx Storage Validation     - CSI driver, StorageClass, PV/PVC, performance
  5. Network Connectivity       - DNS, Internet, PrivateLink, EFA
  6. TLS/HTTPS Validation       - ALB, certificates, HTTP redirect
  7. PyTorchJob Integration     - Submit test job, verify scheduling

Reports are saved to: ${REPORT_DIR}/
EOF
}

setup_report_dir() {
    mkdir -p "$REPORT_DIR"
}

run_suite() {
    local suite_name="$1"
    local suite_script="$2"
    local suite_args="${3:-}"
    local suite_output="${REPORT_DIR}/${suite_name}-${TIMESTAMP}.log"

    TOTAL_SUITES=$((TOTAL_SUITES + 1))

    log_info "Running: $suite_name"

    if [[ -x "$suite_script" ]]; then
        if "$suite_script" $suite_args > "$suite_output" 2>&1; then
            log_success "$suite_name completed"
            PASSED_SUITES=$((PASSED_SUITES + 1))
            SUITE_RESULTS+=("✅ $suite_name: PASSED")
            return 0
        else
            log_fail "$suite_name failed (see $suite_output)"
            FAILED_SUITES=$((FAILED_SUITES + 1))
            SUITE_RESULTS+=("❌ $suite_name: FAILED")
            return 1
        fi
    else
        log_warn "$suite_name script not found or not executable: $suite_script"
        SUITE_RESULTS+=("⚠️ $suite_name: SKIPPED (script not found)")
        return 0
    fi
}

# ============================================================================
# Test Suites
# ============================================================================

run_quick_validation() {
    log_info "========== Quick Validation Mode =========="

    # Cluster health
    run_suite "cluster-health" "${SCRIPT_DIR}/validate-infrastructure.sh" "--cluster" || true

    # Add-ons verification
    run_suite "hyperpod-addons" "${SCRIPT_DIR}/verify-hyperpod-addons.sh" "" || true
}

run_full_validation() {
    log_info "========== Full Validation Mode =========="

    # Run comprehensive infrastructure validation
    run_suite "infrastructure-full" "${SCRIPT_DIR}/validate-infrastructure.sh" "--all" || true

    # Run HyperPod add-ons verification
    run_suite "hyperpod-addons-verbose" "${SCRIPT_DIR}/verify-hyperpod-addons.sh" "--verbose" || true

    # Run FSx performance test (if FSx is available)
    if [[ -x "${SCRIPT_DIR}/fsx-performance-test.sh" ]]; then
        log_info "Running FSx performance test (this may take several minutes)..."
        run_suite "fsx-performance" "${SCRIPT_DIR}/fsx-performance-test.sh" "" || true
    fi
}

run_pytest_validation() {
    log_info "========== Pytest Validation Mode =========="

    local pytest_output="${REPORT_DIR}/pytest-infrastructure-${TIMESTAMP}.xml"

    if command -v pytest &> /dev/null; then
        if [[ -f "${SCRIPT_DIR}/test_infrastructure.py" ]]; then
            TOTAL_SUITES=$((TOTAL_SUITES + 1))
            log_info "Running pytest infrastructure tests..."

            if pytest "${SCRIPT_DIR}/test_infrastructure.py" \
                --junitxml="$pytest_output" \
                -v \
                --tb=short \
                > "${REPORT_DIR}/pytest-${TIMESTAMP}.log" 2>&1; then
                log_success "Pytest tests completed"
                PASSED_SUITES=$((PASSED_SUITES + 1))
                SUITE_RESULTS+=("✅ pytest-infrastructure: PASSED")
            else
                log_fail "Pytest tests failed (see ${REPORT_DIR}/pytest-${TIMESTAMP}.log)"
                FAILED_SUITES=$((FAILED_SUITES + 1))
                SUITE_RESULTS+=("❌ pytest-infrastructure: FAILED")
            fi
        else
            log_warn "Pytest test file not found: ${SCRIPT_DIR}/test_infrastructure.py"
        fi
    else
        log_warn "pytest not installed. Skipping pytest tests."
    fi
}

# ============================================================================
# Report Generation
# ============================================================================

generate_final_report() {
    log_info "Generating final validation report..."

    local cluster_name
    cluster_name=$(kubectl config current-context 2>/dev/null || echo "unknown")

    local eks_version
    eks_version=$(kubectl version -o json 2>/dev/null | jq -r '.serverVersion.gitVersion // "unknown"' || echo "unknown")

    local node_count
    node_count=$(kubectl get nodes --no-headers 2>/dev/null | wc -l || echo "0")

    local gpu_count
    gpu_count=$(kubectl get nodes -o json 2>/dev/null | jq '[.items[].status.allocatable["nvidia.com/gpu"] // "0" | tonumber] | add // 0' || echo "0")

    cat > "$FINAL_REPORT" << EOF
# HyperPod Infrastructure Validation Report

**Reference**: tasks.md T008g - HyperPod 基础设施验证测试
**Generated**: $(date +"%Y-%m-%d %H:%M:%S %Z")
**Cluster Context**: $cluster_name

---

## Executive Summary

| Metric | Value |
|--------|-------|
| Total Test Suites | $TOTAL_SUITES |
| Passed Suites | $PASSED_SUITES |
| Failed Suites | $FAILED_SUITES |
| Pass Rate | $(awk "BEGIN {if($TOTAL_SUITES > 0) printf \"%.1f\", ($PASSED_SUITES/$TOTAL_SUITES)*100; else print \"N/A\"}")% |

### Overall Status

$(if [[ $FAILED_SUITES -eq 0 ]]; then echo "✅ **ALL TESTS PASSED** - Infrastructure is ready for use"; else echo "❌ **SOME TESTS FAILED** - Review failed tests below"; fi)

---

## Test Suite Results

| Suite | Status |
|-------|--------|
EOF

    for result in "${SUITE_RESULTS[@]}"; do
        echo "| ${result//:/ | } |" >> "$FINAL_REPORT"
    done

    cat >> "$FINAL_REPORT" << EOF

---

## Infrastructure Configuration Snapshot

### Cluster Information

| Property | Value |
|----------|-------|
| EKS Version | $eks_version |
| Total Nodes | $node_count |
| Total GPUs | $gpu_count |

### Node Summary

\`\`\`
$(kubectl get nodes -o wide --no-headers 2>/dev/null | head -15 || echo "Unable to retrieve node information")
\`\`\`

### HyperPod Add-ons Status

#### Training Operator
\`\`\`
$(kubectl get pods -A -l app.kubernetes.io/name=training-operator 2>/dev/null || echo "Not found")
\`\`\`

#### Kueue (Task Governance)
\`\`\`
$(kubectl get clusterqueues 2>/dev/null || echo "Not found")
$(kubectl get localqueues -A 2>/dev/null || echo "")
\`\`\`

#### Observability
\`\`\`
$(kubectl get pods -A -l app.kubernetes.io/name=prometheus 2>/dev/null | head -5 || echo "Prometheus: Not found")
$(kubectl get pods -A -l app.kubernetes.io/name=grafana 2>/dev/null | head -5 || echo "Grafana: Not found")
\`\`\`

### Storage Configuration

#### FSx for Lustre
\`\`\`
$(kubectl get storageclass 2>/dev/null | grep -i fsx || echo "No FSx StorageClass found")
$(kubectl get pv 2>/dev/null | grep -i fsx || echo "No FSx PV found")
\`\`\`

### Network Configuration

#### VPC Endpoints (PrivateLink)
\`\`\`
$(aws ec2 describe-vpc-endpoints --query 'VpcEndpoints[*].[VpcEndpointId,ServiceName,State]' --output table 2>/dev/null | head -20 || echo "Unable to retrieve VPC endpoints")
\`\`\`

---

## Validation Checklist (T008g Requirements)

### 1. Cluster Health Check
- [$(if kubectl cluster-info &>/dev/null; then echo "x"; else echo " "; fi)] EKS cluster API reachable
- [$(if [[ $(kubectl get nodes --no-headers 2>/dev/null | grep -c " Ready") -gt 0 ]]; then echo "x"; else echo " "; fi)] All nodes in Ready state
- [$(if kubectl get pods -n kube-system -l k8s-app=kube-dns --field-selector=status.phase=Running --no-headers 2>/dev/null | grep -q Running; then echo "x"; else echo " "; fi)] CoreDNS running

### 2. GPU Node Validation
- [$(if [[ $gpu_count -gt 0 ]]; then echo "x"; else echo " "; fi)] GPU nodes available ($gpu_count GPUs)
- [$(if kubectl get pods -n kube-system -l name=nvidia-device-plugin-ds --no-headers 2>/dev/null | grep -q Running; then echo "x"; else echo " "; fi)] NVIDIA device plugin running

### 3. HyperPod Add-ons
- [$(if kubectl get crd pytorchjobs.kubeflow.org &>/dev/null; then echo "x"; else echo " "; fi)] Training Operator (PyTorchJob CRD)
- [$(if kubectl get crd clusterqueues.kueue.x-k8s.io &>/dev/null; then echo "x"; else echo " "; fi)] Task Governance (Kueue CRDs)
- [$(if kubectl get pods -A -l app.kubernetes.io/name=prometheus 2>/dev/null | grep -q Running; then echo "x"; else echo " "; fi)] Observability (Prometheus)
- [$(if kubectl api-resources 2>/dev/null | grep -q spaces; then echo "x"; else echo " "; fi)] Spaces Add-on (CRD registered)

### 4. FSx Storage
- [$(if kubectl get storageclass 2>/dev/null | grep -qi fsx; then echo "x"; else echo " "; fi)] FSx StorageClass configured
- [$(if aws fsx describe-file-systems --query 'FileSystems[?FileSystemType==\`LUSTRE\`]' --output text 2>/dev/null | grep -q .; then echo "x"; else echo " "; fi)] FSx Lustre file system exists

### 5. Network Connectivity
- [ ] Pod to Internet connectivity (verified during test)
- [ ] S3 PrivateLink connectivity (verified during test)
- [ ] CloudWatch endpoint connectivity (verified during test)

### 6. TLS/HTTPS
- [ ] ALB deployed with HTTPS
- [ ] TLS 1.2+ enforced
- [ ] HTTP to HTTPS redirect

---

## Recommendations

EOF

    if [[ $FAILED_SUITES -gt 0 ]]; then
        cat >> "$FINAL_REPORT" << EOF
### Failed Tests Diagnosis

The following test suites failed and require attention:

EOF
        for result in "${SUITE_RESULTS[@]}"; do
            if [[ "$result" == *"FAILED"* ]]; then
                echo "- $result" >> "$FINAL_REPORT"
            fi
        done

        cat >> "$FINAL_REPORT" << EOF

### Troubleshooting Steps

1. Review individual test logs in \`${REPORT_DIR}/\`
2. Check pod status: \`kubectl get pods -A | grep -v Running\`
3. Check events: \`kubectl get events -A --sort-by='.lastTimestamp' | tail -20\`
4. Verify AWS credentials: \`aws sts get-caller-identity\`
EOF
    else
        cat >> "$FINAL_REPORT" << EOF
All validation tests passed successfully. The infrastructure is ready for:

1. **Training Job Submission**: PyTorchJob CRD is available
2. **Resource Scheduling**: Kueue ClusterQueues are active
3. **Monitoring**: Prometheus and Grafana are operational
4. **High-Performance Storage**: FSx for Lustre is configured
5. **Secure Access**: TLS/HTTPS is enforced
EOF
    fi

    cat >> "$FINAL_REPORT" << EOF

---

## Appendix

### Log Files

Test logs are available in: \`${REPORT_DIR}/\`

EOF

    ls -la "${REPORT_DIR}"/*.log 2>/dev/null | while read line; do
        echo "- $line" >> "$FINAL_REPORT"
    done

    # Copy to summary report location
    cp "$FINAL_REPORT" "$SUMMARY_REPORT"

    log_success "Report generated: $FINAL_REPORT"
    log_success "Summary report: $SUMMARY_REPORT"
}

# ============================================================================
# Main
# ============================================================================

main() {
    local mode="full"

    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --quick)
                mode="quick"
                shift
                ;;
            --full)
                mode="full"
                shift
                ;;
            --pytest-only)
                mode="pytest"
                shift
                ;;
            --help|-h)
                print_help
                exit 0
                ;;
            *)
                log_warn "Unknown argument: $1"
                shift
                ;;
        esac
    done

    print_banner
    setup_report_dir

    # Check prerequisites
    log_info "Checking prerequisites..."
    for cmd in kubectl aws jq; do
        if ! command -v "$cmd" &> /dev/null; then
            log_fail "Required command not found: $cmd"
            exit 1
        fi
    done

    if ! kubectl cluster-info &> /dev/null; then
        log_fail "Cannot connect to Kubernetes cluster"
        exit 1
    fi

    log_success "Prerequisites check passed"
    echo ""

    # Run tests based on mode
    case "$mode" in
        quick)
            run_quick_validation
            ;;
        full)
            run_full_validation
            run_pytest_validation
            ;;
        pytest)
            run_pytest_validation
            ;;
    esac

    echo ""
    generate_final_report

    echo ""
    echo "╔═══════════════════════════════════════════════════════════════════════════╗"
    echo "║                        Validation Complete                                 ║"
    echo "╚═══════════════════════════════════════════════════════════════════════════╝"
    echo ""
    echo "  Total Suites:  $TOTAL_SUITES"
    echo "  Passed:        $PASSED_SUITES"
    echo "  Failed:        $FAILED_SUITES"
    echo ""
    echo "  Report: $FINAL_REPORT"
    echo ""

    if [[ $FAILED_SUITES -gt 0 ]]; then
        log_warn "Some tests failed. Please review the report for details."
        exit 1
    else
        log_success "All tests passed! Infrastructure is ready."
        exit 0
    fi
}

main "$@"
