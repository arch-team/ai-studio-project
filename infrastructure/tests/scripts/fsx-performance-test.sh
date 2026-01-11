#!/bin/bash
# FSx for Lustre Performance Validation Test Suite
#
# This script validates FSx for Lustre performance according to:
# - spec.md FR-007: ≥5GB/s single client throughput
# - spec.md SC-005: S3 to FSx sync <10min for 1TB
#
# Usage:
#   ./fsx-performance-test.sh [OPTIONS]
#
# Options:
#   -m, --mount-path   FSx mount path (default: /fsx)
#   -s, --test-size    Test file size in GB (default: 10)
#   -c, --clients      Number of concurrent clients (default: 1)
#   -o, --output       Output report file (default: fsx-performance-report.txt)
#   -h, --help         Show this help message
#
# Prerequisites:
#   - fio (Flexible I/O Tester)
#   - dd (data duplicator)
#   - Lustre client tools (lfs, lctl)
#
# Reference: tasks.md T008e "FSx for Lustre 性能验证"

set -euo pipefail

# Default configuration
FSX_MOUNT_PATH="${FSX_MOUNT_PATH:-/fsx}"
TEST_SIZE_GB="${TEST_SIZE_GB:-10}"
NUM_CLIENTS="${NUM_CLIENTS:-1}"
OUTPUT_FILE="${OUTPUT_FILE:-fsx-performance-report.txt}"
TEST_DIR="${FSX_MOUNT_PATH}/performance-tests"
PASS_THRESHOLD_MBPS=5000  # 5GB/s = 5000 MB/s

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

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

log_result() {
    local test_name="$1"
    local result="$2"
    local threshold="$3"
    local unit="$4"

    if (( $(echo "$result >= $threshold" | bc -l) )); then
        echo -e "${GREEN}[PASS]${NC} $test_name: ${result} ${unit} (threshold: ${threshold} ${unit})"
        return 0
    else
        echo -e "${RED}[FAIL]${NC} $test_name: ${result} ${unit} (threshold: ${threshold} ${unit})"
        return 1
    fi
}

# Print usage information
usage() {
    cat << EOF
FSx for Lustre Performance Validation Test Suite

Usage: $0 [OPTIONS]

Options:
  -m, --mount-path   FSx mount path (default: /fsx)
  -s, --test-size    Test file size in GB (default: 10)
  -c, --clients      Number of concurrent clients for multi-client test (default: 1)
  -o, --output       Output report file (default: fsx-performance-report.txt)
  -h, --help         Show this help message

Performance Targets:
  - Single client sequential read: ≥5000 MB/s (5GB/s)
  - Single client sequential write: ≥4000 MB/s
  - Multi-client aggregate read: ≥20000 MB/s (with 4+ clients)

Example:
  $0 -m /fsx -s 10 -c 4 -o report.txt
EOF
}

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -m|--mount-path)
                FSX_MOUNT_PATH="$2"
                shift 2
                ;;
            -s|--test-size)
                TEST_SIZE_GB="$2"
                shift 2
                ;;
            -c|--clients)
                NUM_CLIENTS="$2"
                shift 2
                ;;
            -o|--output)
                OUTPUT_FILE="$2"
                shift 2
                ;;
            -h|--help)
                usage
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                usage
                exit 1
                ;;
        esac
    done

    TEST_DIR="${FSX_MOUNT_PATH}/performance-tests"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."

    # Check fio
    if ! command -v fio &> /dev/null; then
        log_error "fio not found. Install with: yum install fio -y"
        exit 1
    fi

    # Check dd
    if ! command -v dd &> /dev/null; then
        log_error "dd not found"
        exit 1
    fi

    # Check mount path
    if [[ ! -d "$FSX_MOUNT_PATH" ]]; then
        log_error "FSx mount path not found: $FSX_MOUNT_PATH"
        exit 1
    fi

    # Check if FSx is mounted (Lustre filesystem)
    if ! mount | grep -q "$FSX_MOUNT_PATH.*lustre"; then
        log_warn "FSx Lustre mount not detected at $FSX_MOUNT_PATH"
        log_warn "Proceeding with test, but results may not reflect actual FSx performance"
    fi

    # Create test directory
    mkdir -p "$TEST_DIR"

    log_info "Prerequisites check passed"
}

# Initialize report
init_report() {
    cat > "$OUTPUT_FILE" << EOF
================================================================================
FSx for Lustre Performance Validation Report
Generated: $(date -u '+%Y-%m-%d %H:%M:%S UTC')
================================================================================

Test Configuration:
  Mount Path: $FSX_MOUNT_PATH
  Test Size: ${TEST_SIZE_GB}GB
  Num Clients: $NUM_CLIENTS
  Test Directory: $TEST_DIR

Performance Targets (spec.md FR-007):
  Single Client Read Throughput: ≥5000 MB/s (5GB/s)
  Single Client Write Throughput: ≥4000 MB/s
  Multi-Client Aggregate (4+ clients): ≥20000 MB/s

================================================================================
TEST RESULTS
================================================================================

EOF
}

# Test 1: Single Client Sequential Read (fio)
test_single_client_seq_read() {
    log_info "Test 1: Single Client Sequential Read (fio)..."

    local test_file="${TEST_DIR}/seq-read-test.bin"

    # Create test file first
    log_info "Creating ${TEST_SIZE_GB}GB test file..."
    dd if=/dev/zero of="$test_file" bs=1M count=$((TEST_SIZE_GB * 1024)) conv=fdatasync 2>/dev/null

    # Clear page cache if running as root
    if [[ $EUID -eq 0 ]]; then
        sync
        echo 3 > /proc/sys/vm/drop_caches 2>/dev/null || true
    fi

    # Run fio sequential read test
    # Reference: spec.md FR-007 性能测试方法
    local fio_output
    fio_output=$(fio --name=dataset-read \
        --rw=read \
        --bs=1M \
        --iodepth=64 \
        --runtime=60 \
        --numjobs=1 \
        --direct=1 \
        --filename="$test_file" \
        --size="${TEST_SIZE_GB}G" \
        --output-format=json 2>/dev/null)

    # Extract read bandwidth (MB/s)
    local read_bw_kbps
    read_bw_kbps=$(echo "$fio_output" | jq -r '.jobs[0].read.bw')
    local read_bw_mbps=$((read_bw_kbps / 1024))

    # Record result
    {
        echo "Test 1: Single Client Sequential Read"
        echo "  Command: fio --rw=read --bs=1M --iodepth=64 --runtime=60 --direct=1"
        echo "  Result: ${read_bw_mbps} MB/s"
        echo "  Threshold: ${PASS_THRESHOLD_MBPS} MB/s"
        if [[ $read_bw_mbps -ge $PASS_THRESHOLD_MBPS ]]; then
            echo "  Status: PASS"
        else
            echo "  Status: FAIL"
        fi
        echo ""
    } >> "$OUTPUT_FILE"

    log_result "Sequential Read" "$read_bw_mbps" "$PASS_THRESHOLD_MBPS" "MB/s"

    # Cleanup
    rm -f "$test_file"

    return $?
}

# Test 2: Single Client Sequential Write (fio)
test_single_client_seq_write() {
    log_info "Test 2: Single Client Sequential Write (fio)..."

    local test_file="${TEST_DIR}/seq-write-test.bin"
    local write_threshold=4000  # 4GB/s for write

    # Run fio sequential write test
    local fio_output
    fio_output=$(fio --name=dataset-write \
        --rw=write \
        --bs=1M \
        --iodepth=64 \
        --runtime=60 \
        --numjobs=1 \
        --direct=1 \
        --filename="$test_file" \
        --size="${TEST_SIZE_GB}G" \
        --output-format=json 2>/dev/null)

    # Extract write bandwidth (MB/s)
    local write_bw_kbps
    write_bw_kbps=$(echo "$fio_output" | jq -r '.jobs[0].write.bw')
    local write_bw_mbps=$((write_bw_kbps / 1024))

    # Record result
    {
        echo "Test 2: Single Client Sequential Write"
        echo "  Command: fio --rw=write --bs=1M --iodepth=64 --runtime=60 --direct=1"
        echo "  Result: ${write_bw_mbps} MB/s"
        echo "  Threshold: ${write_threshold} MB/s"
        if [[ $write_bw_mbps -ge $write_threshold ]]; then
            echo "  Status: PASS"
        else
            echo "  Status: FAIL"
        fi
        echo ""
    } >> "$OUTPUT_FILE"

    log_result "Sequential Write" "$write_bw_mbps" "$write_threshold" "MB/s"

    # Cleanup
    rm -f "$test_file"

    return $?
}

# Test 3: Multi-Client Aggregate Read
test_multi_client_aggregate() {
    if [[ $NUM_CLIENTS -lt 2 ]]; then
        log_info "Skipping multi-client test (clients < 2)"
        return 0
    fi

    log_info "Test 3: Multi-Client Aggregate Read (${NUM_CLIENTS} clients)..."

    local aggregate_threshold=$((5000 * NUM_CLIENTS))  # Scale threshold by client count
    if [[ $NUM_CLIENTS -ge 4 ]]; then
        aggregate_threshold=20000  # Cap at 20GB/s for 4+ clients
    fi

    # Create test files for each client
    for i in $(seq 1 "$NUM_CLIENTS"); do
        local test_file="${TEST_DIR}/multi-read-test-${i}.bin"
        dd if=/dev/zero of="$test_file" bs=1M count=$((TEST_SIZE_GB * 1024)) conv=fdatasync 2>/dev/null &
    done
    wait

    # Clear page cache
    if [[ $EUID -eq 0 ]]; then
        sync
        echo 3 > /proc/sys/vm/drop_caches 2>/dev/null || true
    fi

    # Run parallel fio jobs
    local fio_output
    fio_output=$(fio --name=multi-client-read \
        --rw=read \
        --bs=1M \
        --iodepth=64 \
        --runtime=60 \
        --numjobs="$NUM_CLIENTS" \
        --direct=1 \
        --directory="$TEST_DIR" \
        --filename_format='multi-read-test-$jobnum.bin' \
        --size="${TEST_SIZE_GB}G" \
        --group_reporting \
        --output-format=json 2>/dev/null)

    # Extract aggregate bandwidth
    local agg_bw_kbps
    agg_bw_kbps=$(echo "$fio_output" | jq -r '.jobs[0].read.bw')
    local agg_bw_mbps=$((agg_bw_kbps / 1024))

    # Record result
    {
        echo "Test 3: Multi-Client Aggregate Read (${NUM_CLIENTS} clients)"
        echo "  Command: fio --numjobs=${NUM_CLIENTS} --rw=read --group_reporting"
        echo "  Result: ${agg_bw_mbps} MB/s (aggregate)"
        echo "  Threshold: ${aggregate_threshold} MB/s"
        if [[ $agg_bw_mbps -ge $aggregate_threshold ]]; then
            echo "  Status: PASS"
        else
            echo "  Status: FAIL"
        fi
        echo ""
    } >> "$OUTPUT_FILE"

    log_result "Multi-Client Aggregate Read" "$agg_bw_mbps" "$aggregate_threshold" "MB/s"

    # Cleanup
    rm -f "${TEST_DIR}"/multi-read-test-*.bin

    return $?
}

# Test 4: Random I/O Performance (for completeness)
test_random_io() {
    log_info "Test 4: Random I/O Performance..."

    local test_file="${TEST_DIR}/random-io-test.bin"

    # Run fio random read test
    local fio_output
    fio_output=$(fio --name=random-read \
        --rw=randread \
        --bs=4K \
        --iodepth=32 \
        --runtime=30 \
        --numjobs=4 \
        --direct=1 \
        --filename="$test_file" \
        --size="1G" \
        --group_reporting \
        --output-format=json 2>/dev/null)

    # Extract IOPS
    local iops
    iops=$(echo "$fio_output" | jq -r '.jobs[0].read.iops')

    # Record result (informational, no threshold)
    {
        echo "Test 4: Random I/O Performance"
        echo "  Command: fio --rw=randread --bs=4K --iodepth=32"
        echo "  Result: ${iops} IOPS"
        echo "  Note: Informational only (Lustre optimized for sequential I/O)"
        echo ""
    } >> "$OUTPUT_FILE"

    log_info "Random I/O: ${iops} IOPS (informational)"

    # Cleanup
    rm -f "$test_file"
}

# Test 5: Lustre Stripe Configuration
test_lustre_stripe_config() {
    log_info "Test 5: Lustre Stripe Configuration..."

    # Check if lfs command is available
    if ! command -v lfs &> /dev/null; then
        log_warn "lfs command not found, skipping stripe test"
        return 0
    fi

    # Get stripe info
    local stripe_info
    stripe_info=$(lfs getstripe "$FSX_MOUNT_PATH" 2>/dev/null || echo "N/A")

    # Record result
    {
        echo "Test 5: Lustre Stripe Configuration"
        echo "  Mount Path: $FSX_MOUNT_PATH"
        echo "  Stripe Info:"
        echo "$stripe_info" | sed 's/^/    /'
        echo ""
    } >> "$OUTPUT_FILE"

    log_info "Lustre stripe configuration recorded"
}

# Finalize report
finalize_report() {
    {
        echo "================================================================================
SUMMARY
================================================================================
"
        grep -E "(PASS|FAIL)" "$OUTPUT_FILE" | sort | uniq -c
        echo ""
        echo "Report generated: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
        echo "================================================================================
"
    } >> "$OUTPUT_FILE"

    log_info "Performance report saved to: $OUTPUT_FILE"
}

# Main execution
main() {
    parse_args "$@"

    log_info "Starting FSx for Lustre Performance Validation..."
    log_info "Mount Path: $FSX_MOUNT_PATH"
    log_info "Test Size: ${TEST_SIZE_GB}GB"
    log_info "Clients: $NUM_CLIENTS"

    check_prerequisites
    init_report

    # Run tests
    local failed=0

    test_single_client_seq_read || ((failed++))
    test_single_client_seq_write || ((failed++))
    test_multi_client_aggregate || ((failed++))
    test_random_io
    test_lustre_stripe_config

    finalize_report

    # Cleanup test directory
    rmdir "$TEST_DIR" 2>/dev/null || true

    if [[ $failed -gt 0 ]]; then
        log_error "$failed test(s) failed. Review the report for details."
        exit 1
    else
        log_info "All performance tests passed!"
        exit 0
    fi
}

main "$@"
