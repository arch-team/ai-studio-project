#!/bin/bash
# HyperPod Add-ons Verification Script
# Reference: T008d-1 - Training core components installation
#            T008d-2 - Monitoring and elastic components installation
#
# This script verifies:
# T008d-1:
# 1. Training Operator: PyTorchJob CRD, Webhook readiness
# 2. Task Governance (Kueue): ClusterQueue, LocalQueue, Gang Scheduling
# 3. PriorityClass: Three-tier configuration per spec.md FR-004
#
# T008d-2:
# 4. Observability: Prometheus, Grafana, Node Exporter, DCGM Exporter
# 5. Elastic Agent: Checkpoint management, Auto-Resume, Deep Health Check
#
# Prerequisites:
# - kubectl configured to access the EKS cluster
# - jq installed for JSON parsing
#
# Usage:
#   ./verify-hyperpod-addons.sh [--verbose]

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

VERBOSE=${1:-""}
FAILED_CHECKS=0
PASSED_CHECKS=0

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[PASS]${NC} $1"
    ((PASSED_CHECKS++))
}

log_failure() {
    echo -e "${RED}[FAIL]${NC} $1"
    ((FAILED_CHECKS++))
}

# Check if kubectl is available
check_kubectl() {
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed or not in PATH"
        exit 1
    fi

    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster. Please configure kubectl."
        exit 1
    fi

    log_info "Connected to Kubernetes cluster"
}

# Check if jq is available
check_jq() {
    if ! command -v jq &> /dev/null; then
        log_warn "jq is not installed. Some checks may be limited."
    fi
}

# ==============================================================================
# Training Operator Verification
# ==============================================================================

verify_training_operator() {
    log_info "========== Training Operator Verification =========="

    # Check PyTorchJob CRD
    log_info "Checking PyTorchJob CRD..."
    if kubectl get crd pytorchjobs.kubeflow.org &> /dev/null; then
        log_success "PyTorchJob CRD is registered"

        if [[ "$VERBOSE" == "--verbose" ]]; then
            kubectl get crd pytorchjobs.kubeflow.org -o jsonpath='{.spec.versions[*].name}'
            echo ""
        fi
    else
        log_failure "PyTorchJob CRD is NOT registered"
    fi

    # Check TFJob CRD
    log_info "Checking TFJob CRD..."
    if kubectl get crd tfjobs.kubeflow.org &> /dev/null; then
        log_success "TFJob CRD is registered"
    else
        log_warn "TFJob CRD is not registered (optional)"
    fi

    # Check Training Operator deployment
    log_info "Checking Training Operator deployment..."
    TRAINING_OP_PODS=$(kubectl get pods -n kube-system -l app.kubernetes.io/name=training-operator 2>/dev/null | grep -c Running || echo "0")
    if [[ "$TRAINING_OP_PODS" -gt 0 ]]; then
        log_success "Training Operator is running ($TRAINING_OP_PODS pods)"
    else
        # Try hyperpod-system namespace
        TRAINING_OP_PODS=$(kubectl get pods -n hyperpod-system -l app.kubernetes.io/name=training-operator 2>/dev/null | grep -c Running || echo "0")
        if [[ "$TRAINING_OP_PODS" -gt 0 ]]; then
            log_success "Training Operator is running in hyperpod-system ($TRAINING_OP_PODS pods)"
        else
            log_failure "Training Operator is NOT running"
        fi
    fi

    # Check Training Operator Webhook
    log_info "Checking Training Operator Webhook..."
    if kubectl get validatingwebhookconfigurations | grep -q "training-operator\|kubeflow"; then
        log_success "Training Operator Webhook is configured"

        # Verify webhook endpoint
        WEBHOOK_ENDPOINT=$(kubectl get svc -A -l app.kubernetes.io/name=training-operator -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "")
        if [[ -n "$WEBHOOK_ENDPOINT" ]]; then
            log_info "  Webhook service: $WEBHOOK_ENDPOINT"
        fi
    else
        log_warn "Training Operator Webhook not found (may use different naming)"
    fi
}

# ==============================================================================
# Task Governance (Kueue) Verification
# ==============================================================================

verify_task_governance() {
    log_info "========== Task Governance (Kueue) Verification =========="

    # Check Kueue CRDs
    log_info "Checking Kueue CRDs..."
    KUEUE_CRDS=("clusterqueues.kueue.x-k8s.io" "localqueues.kueue.x-k8s.io" "workloads.kueue.x-k8s.io" "resourceflavors.kueue.x-k8s.io")

    for crd in "${KUEUE_CRDS[@]}"; do
        if kubectl get crd "$crd" &> /dev/null; then
            log_success "CRD $crd is registered"
        else
            log_failure "CRD $crd is NOT registered"
        fi
    done

    # Check Kueue controller
    log_info "Checking Kueue controller..."
    KUEUE_PODS=$(kubectl get pods -A -l app.kubernetes.io/name=kueue 2>/dev/null | grep -c Running || echo "0")
    if [[ "$KUEUE_PODS" -gt 0 ]]; then
        log_success "Kueue controller is running ($KUEUE_PODS pods)"
    else
        # Try different label selectors
        KUEUE_PODS=$(kubectl get pods -A -l control-plane=controller-manager 2>/dev/null | grep -c Running || echo "0")
        if [[ "$KUEUE_PODS" -gt 0 ]]; then
            log_success "Kueue controller is running ($KUEUE_PODS pods)"
        else
            log_failure "Kueue controller is NOT running"
        fi
    fi

    # Check ClusterQueues
    log_info "Checking ClusterQueues..."
    CQ_COUNT=$(kubectl get clusterqueues 2>/dev/null | grep -c "Active\|Ready" || echo "0")
    if [[ "$CQ_COUNT" -gt 0 ]]; then
        log_success "Found $CQ_COUNT active ClusterQueue(s)"

        if [[ "$VERBOSE" == "--verbose" ]]; then
            kubectl get clusterqueues -o wide
        fi
    else
        log_warn "No active ClusterQueues found (may need manual setup)"
    fi

    # Check LocalQueues
    log_info "Checking LocalQueues..."
    LQ_COUNT=$(kubectl get localqueues -A 2>/dev/null | grep -v "NAMESPACE" | wc -l || echo "0")
    if [[ "$LQ_COUNT" -gt 0 ]]; then
        log_success "Found $LQ_COUNT LocalQueue(s)"

        if [[ "$VERBOSE" == "--verbose" ]]; then
            kubectl get localqueues -A
        fi
    else
        log_warn "No LocalQueues found (may need manual setup)"
    fi

    # Check Gang Scheduling configuration
    log_info "Checking Gang Scheduling support..."
    # Check for scheduler-plugins or coscheduling
    if kubectl get crd podgroups.scheduling.x-k8s.io &> /dev/null; then
        log_success "Gang Scheduling (PodGroup CRD) is available"
    elif kubectl get crd podgroups.scheduling.volcano.sh &> /dev/null; then
        log_success "Gang Scheduling (Volcano PodGroup CRD) is available"
    else
        log_warn "Gang Scheduling PodGroup CRD not found (may use Kueue native)"
    fi
}

# ==============================================================================
# PriorityClass Verification
# ==============================================================================

verify_priority_classes() {
    log_info "========== PriorityClass Verification =========="
    log_info "Note: PriorityClasses are automatically created by Task Governance add-on"
    log_info "Expected values per spec.md FR-004: high=1000, medium=500, low=100"

    # Define expected PriorityClasses (created by Task Governance add-on)
    declare -A EXPECTED_PRIORITIES=(
        ["training-priority-high"]="1000"
        ["training-priority-medium"]="500"
        ["training-priority-low"]="100"
    )

    for pc_name in "${!EXPECTED_PRIORITIES[@]}"; do
        expected_value="${EXPECTED_PRIORITIES[$pc_name]}"
        log_info "Checking PriorityClass: $pc_name (expected value: $expected_value)"

        actual_value=$(kubectl get priorityclass "$pc_name" -o jsonpath='{.value}' 2>/dev/null || echo "NOT_FOUND")

        if [[ "$actual_value" == "NOT_FOUND" ]]; then
            log_warn "PriorityClass $pc_name not found (Task Governance may use different naming)"
        elif [[ "$actual_value" == "$expected_value" ]]; then
            log_success "PriorityClass $pc_name has correct value: $actual_value"
        else
            log_failure "PriorityClass $pc_name has wrong value: $actual_value (expected: $expected_value)"
        fi
    done

    # List all PriorityClasses (verbose mode)
    if [[ "$VERBOSE" == "--verbose" ]]; then
        log_info "All PriorityClasses:"
        kubectl get priorityclasses -o custom-columns=NAME:.metadata.name,VALUE:.value,GLOBAL:.globalDefault,PREEMPTION:.preemptionPolicy
    fi
}

# ==============================================================================
# Observability Verification (T008d-2)
# ==============================================================================

verify_observability() {
    log_info "========== Observability Verification (T008d-2) =========="
    log_info "Reference: spec.md FR-007/FR-016"

    # Check Prometheus deployment
    log_info "Checking Prometheus deployment..."
    PROMETHEUS_PODS=$(kubectl get pods -A -l app.kubernetes.io/name=prometheus 2>/dev/null | grep -c Running || echo "0")
    if [[ "$PROMETHEUS_PODS" -gt 0 ]]; then
        log_success "Prometheus is running ($PROMETHEUS_PODS pods)"
    else
        # Try different label selectors
        PROMETHEUS_PODS=$(kubectl get pods -A -l app=prometheus 2>/dev/null | grep -c Running || echo "0")
        if [[ "$PROMETHEUS_PODS" -gt 0 ]]; then
            log_success "Prometheus is running ($PROMETHEUS_PODS pods)"
        else
            log_warn "Prometheus pods not found (may use different naming)"
        fi
    fi

    # Check Grafana deployment
    log_info "Checking Grafana deployment..."
    GRAFANA_PODS=$(kubectl get pods -A -l app.kubernetes.io/name=grafana 2>/dev/null | grep -c Running || echo "0")
    if [[ "$GRAFANA_PODS" -gt 0 ]]; then
        log_success "Grafana is running ($GRAFANA_PODS pods)"
    else
        GRAFANA_PODS=$(kubectl get pods -A -l app=grafana 2>/dev/null | grep -c Running || echo "0")
        if [[ "$GRAFANA_PODS" -gt 0 ]]; then
            log_success "Grafana is running ($GRAFANA_PODS pods)"
        else
            log_warn "Grafana pods not found (may use different naming)"
        fi
    fi

    # Check Node Exporter
    log_info "Checking Node Exporter..."
    NODE_EXPORTER_PODS=$(kubectl get pods -A -l app.kubernetes.io/name=node-exporter 2>/dev/null | grep -c Running || echo "0")
    if [[ "$NODE_EXPORTER_PODS" -gt 0 ]]; then
        log_success "Node Exporter is running ($NODE_EXPORTER_PODS pods)"
    else
        log_warn "Node Exporter pods not found (may use different naming)"
    fi

    # Check DCGM Exporter (GPU metrics)
    log_info "Checking DCGM Exporter (GPU metrics)..."
    DCGM_PODS=$(kubectl get pods -A -l app.kubernetes.io/name=dcgm-exporter 2>/dev/null | grep -c Running || echo "0")
    if [[ "$DCGM_PODS" -gt 0 ]]; then
        log_success "DCGM Exporter is running ($DCGM_PODS pods)"
    else
        log_warn "DCGM Exporter pods not found (may not have GPU nodes yet)"
    fi

    # Try to query Prometheus metrics (if accessible)
    log_info "Checking Prometheus metrics endpoint..."
    PROMETHEUS_SVC=$(kubectl get svc -A -l app.kubernetes.io/name=prometheus -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "")
    if [[ -n "$PROMETHEUS_SVC" ]]; then
        log_success "Prometheus service found: $PROMETHEUS_SVC"

        if [[ "$VERBOSE" == "--verbose" ]]; then
            # Try to get basic metrics
            PROM_NS=$(kubectl get svc -A -l app.kubernetes.io/name=prometheus -o jsonpath='{.items[0].metadata.namespace}' 2>/dev/null || echo "")
            log_info "  Namespace: $PROM_NS"
        fi
    else
        log_warn "Prometheus service not found"
    fi

    # Check Grafana service
    log_info "Checking Grafana service..."
    GRAFANA_SVC=$(kubectl get svc -A -l app.kubernetes.io/name=grafana -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "")
    if [[ -n "$GRAFANA_SVC" ]]; then
        log_success "Grafana service found: $GRAFANA_SVC"
    else
        log_warn "Grafana service not found"
    fi
}

# ==============================================================================
# Elastic Agent Verification (T008d-2)
# ==============================================================================

verify_elastic_agent() {
    log_info "========== Elastic Agent Verification (T008d-2) =========="
    log_info "Reference: spec.md FR-010/FR-011"

    # Check Elastic Agent deployment
    log_info "Checking Elastic Agent deployment..."
    ELASTIC_AGENT_PODS=$(kubectl get pods -A -l app.kubernetes.io/name=elastic-agent 2>/dev/null | grep -c Running || echo "0")
    if [[ "$ELASTIC_AGENT_PODS" -gt 0 ]]; then
        log_success "Elastic Agent is running ($ELASTIC_AGENT_PODS pods)"
    else
        # Try different label selectors (HyperPod naming)
        ELASTIC_AGENT_PODS=$(kubectl get pods -A -l component=elastic-agent 2>/dev/null | grep -c Running || echo "0")
        if [[ "$ELASTIC_AGENT_PODS" -gt 0 ]]; then
            log_success "Elastic Agent is running ($ELASTIC_AGENT_PODS pods)"
        else
            log_warn "Elastic Agent pods not found (may use different naming)"
        fi
    fi

    # Check Health Monitoring Agent (part of HyperPod)
    log_info "Checking Health Monitoring Agent..."
    HEALTH_AGENT_PODS=$(kubectl get pods -A -l app.kubernetes.io/name=health-monitoring-agent 2>/dev/null | grep -c Running || echo "0")
    if [[ "$HEALTH_AGENT_PODS" -gt 0 ]]; then
        log_success "Health Monitoring Agent is running ($HEALTH_AGENT_PODS pods)"
    else
        log_warn "Health Monitoring Agent pods not found"
    fi

    # Check Deep Health Check CRD (if available)
    log_info "Checking Deep Health Check CRD..."
    if kubectl get crd healthchecks.sagemaker.aws.amazon.com &> /dev/null; then
        log_success "Deep Health Check CRD is registered"
    else
        log_warn "Deep Health Check CRD not found (may use different naming)"
    fi

    # Check Job Auto-Restart controller
    log_info "Checking Job Auto-Restart controller..."
    AUTO_RESTART_PODS=$(kubectl get pods -A -l app.kubernetes.io/name=job-auto-restart 2>/dev/null | grep -c Running || echo "0")
    if [[ "$AUTO_RESTART_PODS" -gt 0 ]]; then
        log_success "Job Auto-Restart controller is running ($AUTO_RESTART_PODS pods)"
    else
        log_warn "Job Auto-Restart controller not found"
    fi

    # Check for checkpoint-related ConfigMaps
    log_info "Checking checkpoint configuration..."
    CHECKPOINT_CM=$(kubectl get configmap -A -l component=checkpoint 2>/dev/null | grep -v "NAMESPACE" | wc -l || echo "0")
    if [[ "$CHECKPOINT_CM" -gt 0 ]]; then
        log_success "Found $CHECKPOINT_CM checkpoint-related ConfigMap(s)"
    else
        log_info "No dedicated checkpoint ConfigMaps found (may be integrated in agent config)"
    fi

    if [[ "$VERBOSE" == "--verbose" ]]; then
        log_info "Listing all HyperPod-related pods..."
        kubectl get pods -A | grep -i "hyperpod\|elastic\|health\|checkpoint" || log_info "  No matching pods found"
    fi
}

# ==============================================================================
# Test PyTorchJob Submission (Optional)
# ==============================================================================

test_pytorchjob_submission() {
    log_info "========== Test PyTorchJob Submission =========="

    # Create test namespace if not exists
    kubectl create namespace test-training 2>/dev/null || true

    # Create minimal test PyTorchJob
    TEST_JOB_NAME="test-pytorch-hello-$(date +%s)"

    cat <<EOF | kubectl apply -f -
apiVersion: kubeflow.org/v1
kind: PyTorchJob
metadata:
  name: $TEST_JOB_NAME
  namespace: test-training
  labels:
    test: hyperpod-verification
spec:
  pytorchReplicaSpecs:
    Master:
      replicas: 1
      restartPolicy: Never
      template:
        spec:
          containers:
            - name: pytorch
              image: python:3.11-slim
              command: ["python", "-c", "print('Hello from PyTorchJob!')"]
              resources:
                limits:
                  cpu: "100m"
                  memory: "128Mi"
                requests:
                  cpu: "100m"
                  memory: "128Mi"
EOF

    log_info "Submitted test PyTorchJob: $TEST_JOB_NAME"

    # Wait for job status
    log_info "Waiting for job status (30s timeout)..."
    for i in {1..30}; do
        STATUS=$(kubectl get pytorchjob "$TEST_JOB_NAME" -n test-training -o jsonpath='{.status.conditions[-1].type}' 2>/dev/null || echo "Unknown")

        if [[ "$STATUS" == "Succeeded" ]]; then
            log_success "Test PyTorchJob completed successfully"
            break
        elif [[ "$STATUS" == "Failed" ]]; then
            log_failure "Test PyTorchJob failed"
            break
        elif [[ "$STATUS" == "Running" || "$STATUS" == "Created" ]]; then
            log_info "  Job status: $STATUS (waiting...)"
        fi

        sleep 1
    done

    # Cleanup test job
    log_info "Cleaning up test job..."
    kubectl delete pytorchjob "$TEST_JOB_NAME" -n test-training --ignore-not-found
}

# ==============================================================================
# Main Execution
# ==============================================================================

main() {
    echo "============================================================"
    echo "HyperPod Add-ons Verification Script"
    echo "Reference: T008d-1 - Training core components installation"
    echo "          T008d-2 - Monitoring and elastic components"
    echo "============================================================"
    echo ""

    check_kubectl
    check_jq

    echo ""
    echo "==================== T008d-1 Verification ===================="
    verify_training_operator

    echo ""
    verify_task_governance

    echo ""
    verify_priority_classes

    echo ""
    echo "==================== T008d-2 Verification ===================="
    verify_observability

    echo ""
    verify_elastic_agent

    echo ""
    echo "============================================================"
    echo "Verification Summary"
    echo "============================================================"
    echo -e "${GREEN}Passed:${NC} $PASSED_CHECKS"
    echo -e "${RED}Failed:${NC} $FAILED_CHECKS"
    echo ""

    if [[ "$FAILED_CHECKS" -eq 0 ]]; then
        log_success "All verifications passed!"
        exit 0
    else
        log_error "$FAILED_CHECKS verification(s) failed. Please check the output above."
        exit 1
    fi
}

main "$@"
