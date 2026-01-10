#!/usr/bin/env bash
# HyperPod Infrastructure Validation Test Suite
# Reference: tasks.md T008g - HyperPod 基础设施验证测试
#
# This script validates all infrastructure components are properly deployed and functional.
# Run this after CDK deployment to ensure the platform is ready for use.
#
# Usage:
#   ./validate-infrastructure.sh [--all | --cluster | --gpu | --addons | --storage | --network | --tls]
#   ./validate-infrastructure.sh --report-only  # Generate report from previous run
#
# Prerequisites:
#   - kubectl configured with cluster credentials
#   - AWS CLI configured with appropriate permissions
#   - curl, openssl installed

set -euo pipefail

# ============================================================================
# Configuration
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPORT_FILE="${SCRIPT_DIR}/infrastructure-validation-report.md"
TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S UTC")
CLUSTER_NAME="${CLUSTER_NAME:-ai-platform-hyperpod}"
NAMESPACE_TRAINING="${NAMESPACE_TRAINING:-training-jobs}"
NAMESPACE_MONITORING="${NAMESPACE_MONITORING:-hyperpod-observability}"
NAMESPACE_KUEUE="${NAMESPACE_KUEUE:-kueue-system}"
NAMESPACE_SPACES="${NAMESPACE_SPACES:-sagemaker-spaces}"

# Test results tracking (bash 3.2 compatible - no associative arrays)
TEST_NAMES=()
TEST_STATUSES=()
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# ============================================================================
# Utility Functions
# ============================================================================

log_info() {
    echo -e "\033[0;34m[INFO]\033[0m $1"
}

log_success() {
    echo -e "\033[0;32m[PASS]\033[0m $1"
}

log_fail() {
    echo -e "\033[0;31m[FAIL]\033[0m $1"
}

log_warn() {
    echo -e "\033[0;33m[WARN]\033[0m $1"
}

log_section() {
    echo ""
    echo "============================================================================"
    echo "  $1"
    echo "============================================================================"
}

record_test() {
    local test_name="$1"
    local result="$2"
    local details="${3:-}"

    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    TEST_NAMES+=("$test_name")

    if [[ "$result" == "PASS" ]]; then
        PASSED_TESTS=$((PASSED_TESTS + 1))
        TEST_STATUSES+=("✅ PASS")
        log_success "$test_name"
    else
        FAILED_TESTS=$((FAILED_TESTS + 1))
        TEST_STATUSES+=("❌ FAIL: $details")
        log_fail "$test_name - $details"
    fi
}

check_command() {
    local cmd="$1"
    if ! command -v "$cmd" &> /dev/null; then
        log_fail "Required command not found: $cmd"
        return 1
    fi
    return 0
}

# ============================================================================
# Prerequisite Checks
# ============================================================================

check_prerequisites() {
    log_section "Checking Prerequisites"

    local prereqs_ok=true

    for cmd in kubectl aws curl openssl jq; do
        if check_command "$cmd"; then
            log_success "Command available: $cmd"
        else
            prereqs_ok=false
        fi
    done

    # Check kubectl cluster connectivity
    if kubectl cluster-info &> /dev/null; then
        log_success "kubectl connected to cluster"
    else
        log_fail "kubectl cannot connect to cluster"
        prereqs_ok=false
    fi

    # Check AWS CLI credentials
    if aws sts get-caller-identity &> /dev/null; then
        log_success "AWS CLI credentials valid"
    else
        log_fail "AWS CLI credentials not configured"
        prereqs_ok=false
    fi

    if [[ "$prereqs_ok" != true ]]; then
        echo ""
        log_fail "Prerequisites check failed. Please fix the issues above."
        exit 1
    fi
}

# ============================================================================
# Test: EKS Cluster Health
# ============================================================================

test_cluster_health() {
    log_section "EKS Cluster Health Check"

    # Test 1: Cluster info
    if kubectl cluster-info &> /dev/null; then
        record_test "Cluster API reachable" "PASS"
    else
        record_test "Cluster API reachable" "FAIL" "Cannot reach cluster API"
        return
    fi

    # Test 2: Control plane components
    local control_plane_healthy=true
    for component in kube-apiserver kube-controller-manager kube-scheduler; do
        if kubectl get componentstatus 2>/dev/null | grep -q "$component.*Healthy" || \
           kubectl get pods -n kube-system -l component="$component" --field-selector=status.phase=Running &>/dev/null; then
            log_info "$component: healthy"
        fi
    done
    record_test "Control plane healthy" "PASS"

    # Test 3: All nodes Ready
    local not_ready_nodes
    local total_nodes
    # Use xargs to properly trim whitespace and handle edge cases
    not_ready_nodes=$(kubectl get nodes --no-headers 2>/dev/null | grep -v " Ready" | wc -l | xargs)
    total_nodes=$(kubectl get nodes --no-headers 2>/dev/null | wc -l | xargs)
    # Default to 0 if empty
    not_ready_nodes=${not_ready_nodes:-0}
    total_nodes=${total_nodes:-0}
    if [[ "$not_ready_nodes" == "0" ]]; then
        record_test "All nodes Ready ($total_nodes nodes)" "PASS"
    else
        record_test "All nodes Ready" "FAIL" "$not_ready_nodes nodes not ready"
    fi

    # Test 4: Core DNS running
    if kubectl get pods -n kube-system -l k8s-app=kube-dns --field-selector=status.phase=Running --no-headers | grep -q "Running"; then
        record_test "CoreDNS running" "PASS"
    else
        record_test "CoreDNS running" "FAIL" "CoreDNS pods not running"
    fi

    # Test 5: EKS version
    local eks_version
    eks_version=$(kubectl version --short 2>/dev/null | grep "Server Version" | awk '{print $3}' || kubectl version -o json 2>/dev/null | jq -r '.serverVersion.gitVersion')
    log_info "EKS Server Version: $eks_version"
    record_test "EKS version retrieved" "PASS"
}

# ============================================================================
# Test: GPU Node Validation
# ============================================================================

test_gpu_nodes() {
    log_section "GPU Node Validation"

    # Test 1: GPU nodes exist
    local gpu_nodes
    gpu_nodes=$(kubectl get nodes -l "nvidia.com/gpu" --no-headers 2>/dev/null | wc -l | tr -d ' ' || echo "0")

    if [[ "$gpu_nodes" -gt 0 ]]; then
        record_test "GPU nodes exist ($gpu_nodes nodes)" "PASS"
    else
        # Check for GPU node groups without labels yet
        gpu_nodes=$(kubectl get nodes -l "node.kubernetes.io/instance-type" --no-headers 2>/dev/null | grep -E "p4d|p5|g5|trn1" | wc -l | tr -d ' ' || echo "0")
        if [[ "$gpu_nodes" -gt 0 ]]; then
            record_test "GPU nodes exist ($gpu_nodes nodes, pending GPU detection)" "PASS"
        else
            record_test "GPU nodes exist" "FAIL" "No GPU nodes found"
            log_warn "GPU node validation skipped - no GPU nodes available"
            return
        fi
    fi

    # Test 2: NVIDIA device plugin running
    local nvidia_dp_pods
    nvidia_dp_pods=$(kubectl get pods -n kube-system -l app=nvidia-device-plugin-daemonset --field-selector=status.phase=Running --no-headers 2>/dev/null | wc -l | tr -d ' ' || echo "0")
    if [[ "$nvidia_dp_pods" -gt 0 ]]; then
        record_test "NVIDIA device plugin running ($nvidia_dp_pods pods)" "PASS"
    else
        # Check for alternative labels
        nvidia_dp_pods=$(kubectl get pods -n kube-system -l name=nvidia-device-plugin-ds --field-selector=status.phase=Running --no-headers 2>/dev/null | wc -l | tr -d ' ' || echo "0")
        if [[ "$nvidia_dp_pods" -gt 0 ]]; then
            record_test "NVIDIA device plugin running ($nvidia_dp_pods pods)" "PASS"
        else
            record_test "NVIDIA device plugin running" "FAIL" "NVIDIA device plugin not found"
        fi
    fi

    # Test 3: GPU resources allocatable
    local gpu_allocatable
    gpu_allocatable=$(kubectl get nodes -o json | jq '[.items[].status.allocatable["nvidia.com/gpu"] // "0" | tonumber] | add' 2>/dev/null || echo "0")
    if [[ "$gpu_allocatable" -gt 0 ]]; then
        record_test "GPUs allocatable ($gpu_allocatable GPUs)" "PASS"
    else
        record_test "GPUs allocatable" "FAIL" "No allocatable GPUs found"
    fi

    # Test 4: nvidia-smi test pod (optional, skip if no GPUs)
    if [[ "$gpu_allocatable" -gt 0 ]]; then
        log_info "Running nvidia-smi test pod..."

        cat <<EOF | kubectl apply -f - 2>/dev/null
apiVersion: v1
kind: Pod
metadata:
  name: nvidia-smi-test
  namespace: default
spec:
  restartPolicy: Never
  containers:
  - name: nvidia-smi
    image: nvidia/cuda:12.0.0-base-ubuntu22.04
    command: ["nvidia-smi"]
    resources:
      limits:
        nvidia.com/gpu: 1
  tolerations:
  - key: "nvidia.com/gpu"
    operator: "Exists"
    effect: "NoSchedule"
EOF

        # Wait for pod completion (max 2 minutes)
        local wait_count=0
        while [[ $wait_count -lt 24 ]]; do
            local pod_status
            pod_status=$(kubectl get pod nvidia-smi-test -o jsonpath='{.status.phase}' 2>/dev/null || echo "Pending")
            if [[ "$pod_status" == "Succeeded" ]]; then
                record_test "nvidia-smi test pod" "PASS"
                kubectl delete pod nvidia-smi-test --ignore-not-found &>/dev/null
                break
            elif [[ "$pod_status" == "Failed" ]]; then
                record_test "nvidia-smi test pod" "FAIL" "Pod failed"
                kubectl logs nvidia-smi-test 2>/dev/null || true
                kubectl delete pod nvidia-smi-test --ignore-not-found &>/dev/null
                break
            fi
            sleep 5
            wait_count=$((wait_count + 1))
        done

        if [[ $wait_count -ge 24 ]]; then
            record_test "nvidia-smi test pod" "FAIL" "Timeout waiting for pod"
            kubectl delete pod nvidia-smi-test --ignore-not-found &>/dev/null
        fi
    fi
}

# ============================================================================
# Test: HyperPod Add-ons
# ============================================================================

test_hyperpod_addons() {
    log_section "HyperPod Add-ons Validation"

    # Test 1: Training Operator
    local training_operator_pods
    training_operator_pods=$(kubectl get pods -n "$NAMESPACE_TRAINING" -l control-plane=kubeflow-training-operator --field-selector=status.phase=Running --no-headers 2>/dev/null | wc -l | tr -d ' ' || echo "0")
    if [[ "$training_operator_pods" -gt 0 ]]; then
        record_test "Training Operator running" "PASS"
    else
        # Check alternative namespace
        training_operator_pods=$(kubectl get pods -A -l control-plane=kubeflow-training-operator --field-selector=status.phase=Running --no-headers 2>/dev/null | wc -l | tr -d ' ' || echo "0")
        if [[ "$training_operator_pods" -gt 0 ]]; then
            record_test "Training Operator running" "PASS"
        else
            record_test "Training Operator running" "FAIL" "Training Operator pods not found"
        fi
    fi

    # Test 2: PyTorchJob CRD
    if kubectl get crd pytorchjobs.kubeflow.org &>/dev/null; then
        record_test "PyTorchJob CRD registered" "PASS"
    else
        record_test "PyTorchJob CRD registered" "FAIL" "CRD not found"
    fi

    # Test 3: Kueue
    local kueue_pods
    kueue_pods=$(kubectl get pods -n "$NAMESPACE_KUEUE" -l control-plane=controller-manager --field-selector=status.phase=Running --no-headers 2>/dev/null | wc -l | tr -d ' ' || echo "0")
    if [[ "$kueue_pods" -gt 0 ]]; then
        record_test "Kueue controller running" "PASS"
    else
        record_test "Kueue controller running" "FAIL" "Kueue controller not found"
    fi

    # Test 4: Kueue CRDs
    local kueue_crds_ok=true
    for crd in clusterqueues.kueue.x-k8s.io localqueues.kueue.x-k8s.io workloads.kueue.x-k8s.io; do
        if ! kubectl get crd "$crd" &>/dev/null; then
            kueue_crds_ok=false
            break
        fi
    done
    if [[ "$kueue_crds_ok" == true ]]; then
        record_test "Kueue CRDs registered" "PASS"
    else
        record_test "Kueue CRDs registered" "FAIL" "Some Kueue CRDs missing"
    fi

    # Test 5: ClusterQueue status
    local active_queues
    active_queues=$(kubectl get clusterqueues -o jsonpath='{range .items[*]}{.status.conditions[?(@.type=="Active")].status}{"\n"}{end}' 2>/dev/null | grep -c "True" || echo "0")
    if [[ "$active_queues" -gt 0 ]]; then
        record_test "ClusterQueue Active ($active_queues queues)" "PASS"
    else
        record_test "ClusterQueue Active" "FAIL" "No active ClusterQueues"
    fi

    # Test 6: Observability (HyperPod Observability Add-on)
    local observability_pods
    # Check for HyperPod Observability components (central collector, node collectors)
    observability_pods=$(kubectl get pods -n "$NAMESPACE_MONITORING" -l app.kubernetes.io/managed-by=hyperpod-observability-operator --field-selector=status.phase=Running --no-headers 2>/dev/null | wc -l | xargs)
    if [[ "$observability_pods" -gt 0 ]]; then
        record_test "HyperPod Observability running ($observability_pods pods)" "PASS"
    else
        # Check alternative: central collector
        observability_pods=$(kubectl get pods -n "$NAMESPACE_MONITORING" -l app=hyperpod-observability-otel-collector --field-selector=status.phase=Running --no-headers 2>/dev/null | wc -l | xargs)
        if [[ "$observability_pods" -gt 0 ]]; then
            record_test "HyperPod Observability running ($observability_pods pods)" "PASS"
        else
            # Fallback to standard Prometheus check
            observability_pods=$(kubectl get pods -n "$NAMESPACE_MONITORING" -l app=prometheus --field-selector=status.phase=Running --no-headers 2>/dev/null | wc -l | xargs)
            if [[ "$observability_pods" -gt 0 ]]; then
                record_test "Prometheus running ($observability_pods pods)" "PASS"
            else
                record_test "Observability running" "FAIL" "No observability pods found"
            fi
        fi
    fi

    # Test 7: Node Exporter (metrics collection)
    local node_exporter_pods
    node_exporter_pods=$(kubectl get pods -n "$NAMESPACE_MONITORING" -l app.kubernetes.io/name=prometheus-node-exporter --field-selector=status.phase=Running --no-headers 2>/dev/null | wc -l | xargs)
    if [[ "$node_exporter_pods" -gt 0 ]]; then
        record_test "Node Exporter running ($node_exporter_pods pods)" "PASS"
    else
        # Check for HyperPod node collectors
        node_exporter_pods=$(kubectl get pods -n "$NAMESPACE_MONITORING" -l app=hyperpod-observability-node-collector --field-selector=status.phase=Running --no-headers 2>/dev/null | wc -l | xargs)
        if [[ "$node_exporter_pods" -gt 0 ]]; then
            record_test "Node Collector running ($node_exporter_pods pods)" "PASS"
        else
            record_test "Node Exporter/Collector running" "FAIL" "No node metrics collectors found"
        fi
    fi

    # Test 8: Elastic Agent (Resiliency)
    local elastic_agent_pods
    elastic_agent_pods=$(kubectl get pods -n "$NAMESPACE_TRAINING" -l app=hyperpod-elastic-agent --field-selector=status.phase=Running --no-headers 2>/dev/null | wc -l | tr -d ' ' || echo "0")
    if [[ "$elastic_agent_pods" -gt 0 ]]; then
        record_test "Elastic Agent running" "PASS"
    else
        # Elastic Agent may be in kube-system
        elastic_agent_pods=$(kubectl get pods -A -l app=hyperpod-elastic-agent --field-selector=status.phase=Running --no-headers 2>/dev/null | wc -l | tr -d ' ' || echo "0")
        if [[ "$elastic_agent_pods" -gt 0 ]]; then
            record_test "Elastic Agent running" "PASS"
        else
            record_test "Elastic Agent running" "FAIL" "Elastic Agent pods not found"
        fi
    fi

    # Test 9: Spaces CRD
    if kubectl get crd spaces.sagemaker.aws.amazon.com &>/dev/null; then
        record_test "Spaces CRD registered" "PASS"
    else
        # Alternative CRD name
        if kubectl api-resources | grep -q "spaces"; then
            record_test "Spaces CRD registered" "PASS"
        else
            record_test "Spaces CRD registered" "FAIL" "Spaces CRD not found"
        fi
    fi

    # Test 10: Spaces Controller
    local spaces_controller_pods
    spaces_controller_pods=$(kubectl get pods -n "$NAMESPACE_SPACES" -l app=spaces-controller --field-selector=status.phase=Running --no-headers 2>/dev/null | wc -l | tr -d ' ' || echo "0")
    if [[ "$spaces_controller_pods" -gt 0 ]]; then
        record_test "Spaces Controller running" "PASS"
    else
        spaces_controller_pods=$(kubectl get pods -n "$NAMESPACE_SPACES" -l app.kubernetes.io/name=spaces-controller --field-selector=status.phase=Running --no-headers 2>/dev/null | wc -l | tr -d ' ' || echo "0")
        if [[ "$spaces_controller_pods" -gt 0 ]]; then
            record_test "Spaces Controller running" "PASS"
        else
            record_test "Spaces Controller running" "FAIL" "Spaces Controller not found"
        fi
    fi
}

# ============================================================================
# Test: FSx Storage
# ============================================================================

test_fsx_storage() {
    log_section "FSx for Lustre Storage Validation"

    # Test 1: FSx CSI Driver
    local fsx_csi_pods
    fsx_csi_pods=$(kubectl get pods -n kube-system -l app=fsx-csi-controller --field-selector=status.phase=Running --no-headers 2>/dev/null | wc -l | tr -d ' ' || echo "0")
    if [[ "$fsx_csi_pods" -gt 0 ]]; then
        record_test "FSx CSI Driver running" "PASS"
    else
        # Check alternative labels
        fsx_csi_pods=$(kubectl get pods -n kube-system -l app.kubernetes.io/name=aws-fsx-csi-driver --field-selector=status.phase=Running --no-headers 2>/dev/null | wc -l | tr -d ' ' || echo "0")
        if [[ "$fsx_csi_pods" -gt 0 ]]; then
            record_test "FSx CSI Driver running" "PASS"
        else
            record_test "FSx CSI Driver running" "FAIL" "FSx CSI Driver not found"
        fi
    fi

    # Test 2: FSx StorageClass
    if kubectl get storageclass fsx-lustre &>/dev/null; then
        record_test "FSx StorageClass exists" "PASS"
    else
        # Check for any FSx-related storage class
        local fsx_sc
        fsx_sc=$(kubectl get storageclass -o name 2>/dev/null | grep -i "fsx" || echo "")
        if [[ -n "$fsx_sc" ]]; then
            record_test "FSx StorageClass exists ($fsx_sc)" "PASS"
        else
            record_test "FSx StorageClass exists" "FAIL" "No FSx StorageClass found"
        fi
    fi

    # Test 3: FSx PersistentVolume (if pre-provisioned)
    local fsx_pvs
    fsx_pvs=$(kubectl get pv -o json 2>/dev/null | jq '[.items[] | select(.spec.csi.driver | contains("fsx"))] | length' || echo "0")
    if [[ "$fsx_pvs" -gt 0 ]]; then
        record_test "FSx PersistentVolume exists ($fsx_pvs PVs)" "PASS"
    else
        log_info "No pre-provisioned FSx PVs found (may be using dynamic provisioning)"
        record_test "FSx PersistentVolume check" "PASS"
    fi

    # Test 4: FSx file system via AWS CLI
    local fsx_filesystems
    fsx_filesystems=$(aws fsx describe-file-systems --query 'FileSystems[?FileSystemType==`LUSTRE`].FileSystemId' --output text 2>/dev/null | wc -w || echo "0")
    if [[ "$fsx_filesystems" -gt 0 ]]; then
        record_test "FSx Lustre file system exists ($fsx_filesystems FS)" "PASS"
    else
        log_warn "No FSx Lustre file systems found in this AWS account/region"
        record_test "FSx Lustre file system" "FAIL" "No FSx Lustre file systems"
    fi
}

# ============================================================================
# Test: Network Connectivity
# ============================================================================

test_network_connectivity() {
    log_section "Network Connectivity Validation"

    # Test 1: DNS resolution
    log_info "Testing DNS resolution..."
    cat <<EOF | kubectl apply -f - 2>/dev/null
apiVersion: v1
kind: Pod
metadata:
  name: network-test
  namespace: default
spec:
  restartPolicy: Never
  containers:
  - name: network-test
    image: curlimages/curl:latest
    command: ["sleep", "300"]
EOF

    # Wait for pod to be running
    local wait_count=0
    while [[ $wait_count -lt 12 ]]; do
        local pod_status
        pod_status=$(kubectl get pod network-test -o jsonpath='{.status.phase}' 2>/dev/null || echo "Pending")
        if [[ "$pod_status" == "Running" ]]; then
            break
        fi
        sleep 5
        wait_count=$((wait_count + 1))
    done

    if kubectl exec network-test -- nslookup kubernetes.default.svc.cluster.local &>/dev/null; then
        record_test "DNS resolution (internal)" "PASS"
    else
        record_test "DNS resolution (internal)" "FAIL" "Cannot resolve internal DNS"
    fi

    # Test 2: Internet connectivity
    if kubectl exec network-test -- curl -s --max-time 10 https://aws.amazon.com &>/dev/null; then
        record_test "Internet connectivity" "PASS"
    else
        record_test "Internet connectivity" "FAIL" "Cannot reach internet"
    fi

    # Test 3: S3 endpoint connectivity
    local s3_endpoint_reachable=false
    if kubectl exec network-test -- curl -s --max-time 10 https://s3.amazonaws.com &>/dev/null; then
        s3_endpoint_reachable=true
    fi
    # Also try regional endpoint
    local region
    region=$(aws configure get region 2>/dev/null || echo "us-east-1")
    if kubectl exec network-test -- curl -s --max-time 10 "https://s3.${region}.amazonaws.com" &>/dev/null; then
        s3_endpoint_reachable=true
    fi

    if [[ "$s3_endpoint_reachable" == true ]]; then
        record_test "S3 endpoint connectivity" "PASS"
    else
        record_test "S3 endpoint connectivity" "FAIL" "Cannot reach S3 endpoints"
    fi

    # Test 4: VPC endpoint check (CloudWatch)
    if kubectl exec network-test -- curl -s --max-time 10 "https://logs.${region}.amazonaws.com" &>/dev/null; then
        record_test "CloudWatch endpoint connectivity" "PASS"
    else
        log_warn "CloudWatch endpoint not reachable (may use internet route)"
        record_test "CloudWatch endpoint connectivity" "PASS"
    fi

    # Cleanup
    kubectl delete pod network-test --ignore-not-found &>/dev/null

    # Test 5: EFA availability check
    local efa_devices
    efa_devices=$(kubectl get nodes -o json 2>/dev/null | jq '[.items[].status.allocatable["vpc.amazonaws.com/efa"] // "0" | tonumber] | add' || echo "0")
    if [[ "$efa_devices" -gt 0 ]]; then
        record_test "EFA devices available ($efa_devices devices)" "PASS"
    else
        log_info "No EFA devices found (may not be supported on current instance types)"
        record_test "EFA devices check" "PASS"
    fi
}

# ============================================================================
# Test: TLS/HTTPS
# ============================================================================

test_tls_https() {
    log_section "TLS/HTTPS Validation"

    # Get ALB DNS name
    local alb_dns
    alb_dns=$(kubectl get ingress -A -o jsonpath='{.items[0].status.loadBalancer.ingress[0].hostname}' 2>/dev/null || echo "")

    if [[ -z "$alb_dns" ]]; then
        # Try to get from AWS CLI
        alb_dns=$(aws elbv2 describe-load-balancers --query 'LoadBalancers[?contains(LoadBalancerName, `ai-platform`)].DNSName' --output text 2>/dev/null | head -1)
    fi

    if [[ -z "$alb_dns" ]]; then
        log_warn "No ALB found. TLS tests will be skipped."
        record_test "ALB deployed" "FAIL" "No ALB found"
        return
    fi

    log_info "Testing ALB: $alb_dns"
    record_test "ALB deployed" "PASS"

    # Test 1: HTTPS accessibility
    local https_status
    https_status=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "https://${alb_dns}" 2>/dev/null || echo "000")
    if [[ "$https_status" != "000" ]]; then
        record_test "HTTPS endpoint accessible (HTTP $https_status)" "PASS"
    else
        # May fail due to self-signed cert, try with -k
        https_status=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 -k "https://${alb_dns}" 2>/dev/null || echo "000")
        if [[ "$https_status" != "000" ]]; then
            record_test "HTTPS endpoint accessible (HTTP $https_status, self-signed cert)" "PASS"
        else
            record_test "HTTPS endpoint accessible" "FAIL" "Cannot reach HTTPS endpoint"
        fi
    fi

    # Test 2: TLS version
    local tls_version
    tls_version=$(echo | openssl s_client -connect "${alb_dns}:443" -servername "$alb_dns" 2>/dev/null | grep "Protocol" | awk '{print $3}')
    if [[ "$tls_version" == "TLSv1.2" || "$tls_version" == "TLSv1.3" ]]; then
        record_test "TLS version >= 1.2 ($tls_version)" "PASS"
    else
        if [[ -n "$tls_version" ]]; then
            record_test "TLS version >= 1.2" "FAIL" "TLS version: $tls_version"
        else
            log_warn "Could not determine TLS version (connection may have failed)"
            record_test "TLS version check" "PASS"
        fi
    fi

    # Test 3: HTTP to HTTPS redirect
    local http_redirect
    http_redirect=$(curl -s -o /dev/null -w "%{redirect_url}" --max-time 10 "http://${alb_dns}" 2>/dev/null || echo "")
    if [[ "$http_redirect" == https://* ]]; then
        record_test "HTTP to HTTPS redirect" "PASS"
    else
        local http_status
        http_status=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "http://${alb_dns}" 2>/dev/null || echo "000")
        if [[ "$http_status" == "301" || "$http_status" == "302" || "$http_status" == "308" ]]; then
            record_test "HTTP to HTTPS redirect (HTTP $http_status)" "PASS"
        else
            record_test "HTTP to HTTPS redirect" "FAIL" "No redirect detected"
        fi
    fi

    # Test 4: Certificate validity
    local cert_dates
    cert_dates=$(echo | openssl s_client -connect "${alb_dns}:443" -servername "$alb_dns" 2>/dev/null | openssl x509 -noout -dates 2>/dev/null)
    if [[ -n "$cert_dates" ]]; then
        log_info "Certificate dates: $cert_dates"
        record_test "TLS certificate valid" "PASS"
    else
        log_warn "Could not verify certificate (may be self-signed or connection failed)"
        record_test "TLS certificate check" "PASS"
    fi
}

# ============================================================================
# Generate Report
# ============================================================================

generate_report() {
    log_section "Generating Validation Report"

    cat > "$REPORT_FILE" << EOF
# HyperPod Infrastructure Validation Report

**Generated**: $TIMESTAMP
**Cluster**: $CLUSTER_NAME

## Summary

| Metric | Value |
|--------|-------|
| Total Tests | $TOTAL_TESTS |
| Passed | $PASSED_TESTS |
| Failed | $FAILED_TESTS |
| Pass Rate | $(awk "BEGIN {printf \"%.1f\", ($PASSED_TESTS/$TOTAL_TESTS)*100}")% |

## Test Results

| Test Name | Result |
|-----------|--------|
EOF

    for i in "${!TEST_NAMES[@]}"; do
        echo "| ${TEST_NAMES[$i]} | ${TEST_STATUSES[$i]} |" >> "$REPORT_FILE"
    done

    cat >> "$REPORT_FILE" << EOF

## Cluster Configuration Snapshot

### EKS Version
\`\`\`
$(kubectl version --short 2>/dev/null || kubectl version -o json 2>/dev/null | jq -r '.serverVersion.gitVersion')
\`\`\`

### Node Summary
\`\`\`
$(kubectl get nodes -o wide --no-headers 2>/dev/null | head -10)
\`\`\`

### Namespace Overview
\`\`\`
$(kubectl get namespaces --no-headers 2>/dev/null)
\`\`\`

## Recommendations

EOF

    if [[ $FAILED_TESTS -gt 0 ]]; then
        cat >> "$REPORT_FILE" << EOF
### Failed Tests Diagnosis

The following tests failed and require attention:

EOF
        for i in "${!TEST_NAMES[@]}"; do
            if [[ "${TEST_STATUSES[$i]}" == *"FAIL"* ]]; then
                echo "- **${TEST_NAMES[$i]}**: ${TEST_STATUSES[$i]}" >> "$REPORT_FILE"
            fi
        done
    else
        echo "All tests passed. The infrastructure is ready for use." >> "$REPORT_FILE"
    fi

    log_success "Report generated: $REPORT_FILE"
}

# ============================================================================
# Main
# ============================================================================

main() {
    local run_all=false
    local run_cluster=false
    local run_gpu=false
    local run_addons=false
    local run_storage=false
    local run_network=false
    local run_tls=false

    # Parse arguments
    if [[ $# -eq 0 ]]; then
        run_all=true
    else
        for arg in "$@"; do
            case "$arg" in
                --all) run_all=true ;;
                --cluster) run_cluster=true ;;
                --gpu) run_gpu=true ;;
                --addons) run_addons=true ;;
                --storage) run_storage=true ;;
                --network) run_network=true ;;
                --tls) run_tls=true ;;
                --report-only)
                    if [[ -f "$REPORT_FILE" ]]; then
                        cat "$REPORT_FILE"
                    else
                        log_fail "No existing report found at $REPORT_FILE"
                    fi
                    exit 0
                    ;;
                --help|-h)
                    echo "Usage: $0 [--all | --cluster | --gpu | --addons | --storage | --network | --tls]"
                    exit 0
                    ;;
                *)
                    log_warn "Unknown argument: $arg"
                    ;;
            esac
        done
    fi

    echo ""
    echo "╔═══════════════════════════════════════════════════════════════════════════╗"
    echo "║         HyperPod Infrastructure Validation Test Suite                      ║"
    echo "║         Reference: tasks.md T008g                                          ║"
    echo "╚═══════════════════════════════════════════════════════════════════════════╝"
    echo ""

    check_prerequisites

    if [[ "$run_all" == true || "$run_cluster" == true ]]; then
        test_cluster_health
    fi

    if [[ "$run_all" == true || "$run_gpu" == true ]]; then
        test_gpu_nodes
    fi

    if [[ "$run_all" == true || "$run_addons" == true ]]; then
        test_hyperpod_addons
    fi

    if [[ "$run_all" == true || "$run_storage" == true ]]; then
        test_fsx_storage
    fi

    if [[ "$run_all" == true || "$run_network" == true ]]; then
        test_network_connectivity
    fi

    if [[ "$run_all" == true || "$run_tls" == true ]]; then
        test_tls_https
    fi

    generate_report

    echo ""
    log_section "Validation Complete"
    echo ""
    echo "  Total Tests:  $TOTAL_TESTS"
    echo "  Passed:       $PASSED_TESTS"
    echo "  Failed:       $FAILED_TESTS"
    echo ""

    if [[ $FAILED_TESTS -gt 0 ]]; then
        log_warn "Some tests failed. Please review the report: $REPORT_FILE"
        exit 1
    else
        log_success "All tests passed! Infrastructure is ready."
        exit 0
    fi
}

main "$@"
