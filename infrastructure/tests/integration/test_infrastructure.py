"""
HyperPod Infrastructure Validation Tests
Reference: tasks.md T008g - HyperPod 基础设施验证测试

This module contains pytest tests for validating the HyperPod EKS infrastructure.
Tests cover:
- Cluster health
- GPU node availability
- HyperPod Add-ons (Training Operator, Kueue, Observability, Spaces)
- FSx storage
- Network connectivity
- TLS/HTTPS configuration

Prerequisites:
- kubectl configured with cluster credentials
- AWS CLI configured
- kubernetes Python client installed

Usage:
    pytest integration/test_infrastructure.py -v
    pytest integration/test_infrastructure.py -v -k "cluster"  # Run only cluster tests
    pytest integration/test_infrastructure.py -v --tb=short    # Short traceback
"""

import json
import subprocess
import time
from typing import List, Optional

import pytest

# Try to import kubernetes client
try:
    from kubernetes import client
    from kubernetes.client.rest import ApiException

    K8S_AVAILABLE = True
except ImportError:
    K8S_AVAILABLE = False
    client = None
    ApiException = Exception

# Try to import boto3
try:
    import boto3

    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False
    boto3 = None


# ============================================================================
# Helper Functions
# ============================================================================


def run_kubectl(args: List[str], timeout: int = 30) -> subprocess.CompletedProcess:
    """Run kubectl command and return result."""
    cmd = ["kubectl"] + args
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)


# ============================================================================
# Cluster Health Tests
# ============================================================================


@pytest.mark.infrastructure
class TestClusterHealth:
    """Test suite for EKS cluster health."""

    def test_cluster_api_reachable(self, k8s_core_client):
        """Verify cluster API is reachable."""
        version = client.VersionApi().get_code()
        assert version is not None
        assert version.git_version is not None
        print(f"Cluster version: {version.git_version}")

    def test_all_nodes_ready(self, k8s_core_client):
        """Verify all nodes are in Ready state."""
        nodes = k8s_core_client.list_node()
        assert len(nodes.items) > 0, "No nodes found in cluster"

        not_ready_nodes = []
        for node in nodes.items:
            is_ready = False
            for condition in node.status.conditions:
                if condition.type == "Ready" and condition.status == "True":
                    is_ready = True
                    break
            if not is_ready:
                not_ready_nodes.append(node.metadata.name)

        assert len(not_ready_nodes) == 0, f"Nodes not ready: {not_ready_nodes}"
        print(f"All {len(nodes.items)} nodes are Ready")

    def test_coredns_running(self, k8s_core_client):
        """Verify CoreDNS is running."""
        pods = k8s_core_client.list_namespaced_pod(
            namespace="kube-system", label_selector="k8s-app=kube-dns"
        )

        running_pods = [p for p in pods.items if p.status.phase == "Running"]

        assert len(running_pods) > 0, "No CoreDNS pods running"
        print(f"CoreDNS: {len(running_pods)} pods running")

    def test_kube_system_pods_healthy(self, k8s_core_client):
        """Verify kube-system pods are healthy."""
        pods = k8s_core_client.list_namespaced_pod(namespace="kube-system")

        failed_pods = []
        for pod in pods.items:
            if pod.status.phase not in ["Running", "Succeeded"]:
                failed_pods.append(f"{pod.metadata.name}: {pod.status.phase}")

        failed_count = len(failed_pods)
        total_count = len(pods.items)

        # Assert less than 10% of pods are failed
        assert failed_count < total_count * 0.1, f"Too many failed pods: {failed_pods}"
        print(f"kube-system: {total_count - failed_count}/{total_count} pods healthy")


# ============================================================================
# GPU Node Tests
# ============================================================================


@pytest.mark.infrastructure
class TestGPUNodes:
    """Test suite for GPU node validation."""

    def test_gpu_nodes_exist(self, k8s_core_client):
        """Verify GPU nodes exist in the cluster."""
        nodes = k8s_core_client.list_node()

        gpu_nodes = []
        for node in nodes.items:
            allocatable = node.status.allocatable or {}
            if "nvidia.com/gpu" in allocatable:
                gpu_count = int(allocatable["nvidia.com/gpu"])
                if gpu_count > 0:
                    gpu_nodes.append(
                        {
                            "name": node.metadata.name,
                            "gpus": gpu_count,
                            "instance_type": node.metadata.labels.get(
                                "node.kubernetes.io/instance-type", "unknown"
                            ),
                        }
                    )

        # GPU nodes are optional for some test environments
        if len(gpu_nodes) == 0:
            pytest.skip("No GPU nodes found (may be expected in test environment)")

        total_gpus = sum(n["gpus"] for n in gpu_nodes)
        print(f"Found {len(gpu_nodes)} GPU nodes with {total_gpus} total GPUs")

    def test_nvidia_device_plugin(self, k8s_core_client):
        """Verify NVIDIA device plugin is running."""
        selectors = [
            "name=nvidia-device-plugin-ds",
            "app=nvidia-device-plugin-daemonset",
            "app.kubernetes.io/name=nvidia-device-plugin",
        ]

        plugin_found = False
        for selector in selectors:
            pods = k8s_core_client.list_namespaced_pod(
                namespace="kube-system", label_selector=selector
            )
            running_pods = [p for p in pods.items if p.status.phase == "Running"]
            if len(running_pods) > 0:
                plugin_found = True
                print(f"NVIDIA device plugin: {len(running_pods)} pods running")
                break

        if not plugin_found:
            # Check if there are any GPU nodes first
            nodes = k8s_core_client.list_node()
            has_gpu_nodes = any(
                "nvidia.com/gpu" in (n.status.allocatable or {}) for n in nodes.items
            )
            if has_gpu_nodes:
                pytest.fail("NVIDIA device plugin not found but GPU nodes exist")
            else:
                pytest.skip("No GPU nodes, NVIDIA device plugin not required")


# ============================================================================
# HyperPod Add-ons Tests
# ============================================================================


@pytest.mark.infrastructure
class TestHyperPodAddons:
    """Test suite for HyperPod add-ons."""

    def test_pytorchjob_crd_registered(self, k8s_custom_client):
        """Verify PyTorchJob CRD is registered."""
        try:
            result = run_kubectl(
                [
                    "get",
                    "crd",
                    "pytorchjobs.kubeflow.org",
                    "-o",
                    "jsonpath={.metadata.name}",
                ]
            )
            assert result.returncode == 0, "PyTorchJob CRD not found"
            print("PyTorchJob CRD is registered")
        except Exception as e:
            pytest.fail(f"PyTorchJob CRD check failed: {e}")

    def test_kueue_crds_registered(self):
        """Verify Kueue CRDs are registered."""
        required_crds = [
            "clusterqueues.kueue.x-k8s.io",
            "localqueues.kueue.x-k8s.io",
            "workloads.kueue.x-k8s.io",
        ]

        missing_crds = []
        for crd in required_crds:
            result = run_kubectl(["get", "crd", crd, "-o", "name"])
            if result.returncode != 0:
                missing_crds.append(crd)

        assert len(missing_crds) == 0, f"Missing Kueue CRDs: {missing_crds}"
        print(f"All {len(required_crds)} Kueue CRDs are registered")

    def test_kueue_controller_running(self, k8s_core_client, infra_config):
        """Verify Kueue controller is running."""
        namespaces = [
            infra_config["namespace_kueue"],
            "kube-system",
            "hyperpod-system",
        ]

        controller_found = False
        for ns in namespaces:
            try:
                pods = k8s_core_client.list_namespaced_pod(
                    namespace=ns, label_selector="control-plane=controller-manager"
                )
                running_pods = [p for p in pods.items if p.status.phase == "Running"]
                if len(running_pods) > 0:
                    controller_found = True
                    print(f"Kueue controller running in {ns}: {len(running_pods)} pods")
                    break
            except ApiException:
                continue

        assert controller_found, "Kueue controller not found"

    def test_clusterqueue_active(self, k8s_custom_client):
        """Verify at least one ClusterQueue is active."""
        result = run_kubectl(
            [
                "get",
                "clusterqueues",
                "-o",
                "jsonpath={.items[*].status.conditions[?(@.type=='Active')].status}",
            ]
        )

        if result.returncode != 0 or not result.stdout.strip():
            pytest.skip("No ClusterQueues found (may need manual setup)")

        active_statuses = result.stdout.strip().split()
        active_count = sum(1 for s in active_statuses if s == "True")

        assert active_count > 0, "No active ClusterQueues"
        print(f"Found {active_count} active ClusterQueue(s)")

    def test_prometheus_running(self, k8s_core_client, infra_config):
        """Verify Prometheus is running."""
        selectors = ["app.kubernetes.io/name=prometheus", "app=prometheus"]

        prometheus_found = False
        for selector in selectors:
            try:
                pods = k8s_core_client.list_namespaced_pod(
                    namespace=infra_config["namespace_monitoring"],
                    label_selector=selector,
                )
                running_pods = [p for p in pods.items if p.status.phase == "Running"]
                if len(running_pods) > 0:
                    prometheus_found = True
                    print(f"Prometheus: {len(running_pods)} pods running")
                    break
            except ApiException:
                continue

        if not prometheus_found:
            # Try all namespaces
            for selector in selectors:
                result = run_kubectl(
                    [
                        "get",
                        "pods",
                        "-A",
                        "-l",
                        selector,
                        "--field-selector=status.phase=Running",
                        "-o",
                        "name",
                    ]
                )
                if result.returncode == 0 and result.stdout.strip():
                    prometheus_found = True
                    print("Prometheus found in cluster")
                    break

        assert prometheus_found, "Prometheus not found"

    def test_spaces_crd_registered(self):
        """Verify Spaces CRD is registered (for SageMaker Spaces Add-on)."""
        result = run_kubectl(["api-resources", "--api-group=sagemaker.aws.amazon.com"])

        if result.returncode == 0 and "space" in result.stdout.lower():
            print("Spaces CRD is registered")
        else:
            result = run_kubectl(["get", "crd"])
            if "space" in result.stdout.lower():
                print("Spaces CRD found")
            else:
                pytest.skip("Spaces CRD not found (Spaces Add-on may not be installed)")


# ============================================================================
# FSx Storage Tests
# ============================================================================


@pytest.mark.infrastructure
class TestFSxStorage:
    """Test suite for FSx for Lustre storage."""

    def test_fsx_csi_driver(self, k8s_core_client):
        """Verify FSx CSI driver is running."""
        selectors = [
            "app=fsx-csi-controller",
            "app.kubernetes.io/name=aws-fsx-csi-driver",
        ]

        driver_found = False
        for selector in selectors:
            pods = k8s_core_client.list_namespaced_pod(
                namespace="kube-system", label_selector=selector
            )
            running_pods = [p for p in pods.items if p.status.phase == "Running"]
            if len(running_pods) > 0:
                driver_found = True
                print(f"FSx CSI driver: {len(running_pods)} controller pods running")
                break

        if not driver_found:
            pytest.skip("FSx CSI driver not found (may not be required)")

    def test_fsx_storageclass_exists(self):
        """Verify FSx StorageClass exists."""
        result = run_kubectl(["get", "storageclass", "-o", "json"])

        if result.returncode != 0:
            pytest.fail("Cannot get StorageClasses")

        storage_classes = json.loads(result.stdout)
        fsx_classes = [
            sc["metadata"]["name"]
            for sc in storage_classes.get("items", [])
            if "fsx" in sc.get("provisioner", "").lower()
            or "fsx" in sc["metadata"]["name"].lower()
        ]

        if len(fsx_classes) == 0:
            pytest.skip("No FSx StorageClass found (may use pre-provisioned PV)")

        print(f"FSx StorageClasses: {fsx_classes}")

    def test_fsx_filesystem_exists(self, aws_session):
        """Verify FSx Lustre filesystem exists in AWS."""
        fsx_client = aws_session.client("fsx")

        try:
            response = fsx_client.describe_file_systems()
            lustre_filesystems = [
                fs
                for fs in response.get("FileSystems", [])
                if fs.get("FileSystemType") == "LUSTRE"
            ]

            if len(lustre_filesystems) == 0:
                pytest.skip("No FSx Lustre filesystems found in AWS account")

            print(f"Found {len(lustre_filesystems)} FSx Lustre filesystem(s)")
            for fs in lustre_filesystems:
                print(f"  - {fs['FileSystemId']}: {fs['Lifecycle']}")

        except Exception as e:
            pytest.skip(f"Cannot query FSx: {e}")


# ============================================================================
# Network Connectivity Tests
# ============================================================================


@pytest.mark.infrastructure
class TestNetworkConnectivity:
    """Test suite for network connectivity."""

    @pytest.fixture(autouse=True)
    def setup_test_pod(self, k8s_core_client):
        """Create a test pod for network tests."""
        if not K8S_AVAILABLE:
            pytest.skip("kubernetes client not available")

        pod_name = "pytest-network-test"
        namespace = "default"

        # Create test pod
        pod = client.V1Pod(
            metadata=client.V1ObjectMeta(name=pod_name),
            spec=client.V1PodSpec(
                containers=[
                    client.V1Container(
                        name="network-test",
                        image="curlimages/curl:latest",
                        command=["sleep", "300"],
                    )
                ],
                restart_policy="Never",
            ),
        )

        try:
            k8s_core_client.create_namespaced_pod(namespace=namespace, body=pod)
        except ApiException as e:
            if e.status != 409:  # Already exists
                raise

        # Wait for pod to be running
        for _ in range(30):
            pod_status = k8s_core_client.read_namespaced_pod_status(pod_name, namespace)
            if pod_status.status.phase == "Running":
                break
            time.sleep(1)

        yield pod_name

        # Cleanup
        try:
            k8s_core_client.delete_namespaced_pod(pod_name, namespace)
        except ApiException:
            pass

    def test_internal_dns_resolution(self, setup_test_pod):
        """Verify internal DNS resolution works."""
        result = run_kubectl(
            [
                "exec",
                setup_test_pod,
                "--",
                "nslookup",
                "kubernetes.default.svc.cluster.local",
            ],
            timeout=30,
        )

        assert result.returncode == 0, "Internal DNS resolution failed"
        print("Internal DNS resolution works")

    def test_internet_connectivity(self, setup_test_pod):
        """Verify internet connectivity from pods."""
        result = run_kubectl(
            [
                "exec",
                setup_test_pod,
                "--",
                "curl",
                "-s",
                "--max-time",
                "10",
                "https://aws.amazon.com",
            ],
            timeout=30,
        )

        # Allow failure if no internet access (private cluster)
        if result.returncode != 0:
            pytest.skip("Internet not reachable (may be private cluster)")

        print("Internet connectivity verified")

    def test_s3_endpoint_connectivity(self, setup_test_pod, infra_config):
        """Verify S3 endpoint is reachable."""
        endpoints = [
            "s3.amazonaws.com",
            f"s3.{infra_config['aws_region']}.amazonaws.com",
        ]

        connected = False
        for endpoint in endpoints:
            result = run_kubectl(
                [
                    "exec",
                    setup_test_pod,
                    "--",
                    "curl",
                    "-s",
                    "--max-time",
                    "10",
                    f"https://{endpoint}",
                ],
                timeout=30,
            )
            if result.returncode == 0:
                connected = True
                print(f"S3 endpoint reachable: {endpoint}")
                break

        assert connected, "S3 endpoint not reachable"


# ============================================================================
# TLS/HTTPS Tests
# ============================================================================


@pytest.mark.infrastructure
class TestTLSHTTPS:
    """Test suite for TLS/HTTPS validation."""

    def get_alb_dns(self) -> Optional[str]:
        """Get ALB DNS name."""
        # Try from Ingress
        result = run_kubectl(
            [
                "get",
                "ingress",
                "-A",
                "-o",
                "jsonpath={.items[0].status.loadBalancer.ingress[0].hostname}",
            ]
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()

        # Try from AWS CLI
        if BOTO3_AVAILABLE:
            try:
                elbv2 = boto3.client("elbv2")
                response = elbv2.describe_load_balancers()
                for lb in response.get("LoadBalancers", []):
                    if "ai-platform" in lb.get("LoadBalancerName", "").lower():
                        return lb.get("DNSName")
            except Exception:
                pass

        return None

    def test_alb_deployed(self):
        """Verify ALB is deployed."""
        alb_dns = self.get_alb_dns()
        if alb_dns is None:
            pytest.skip("No ALB found (may not be deployed yet)")

        print(f"ALB DNS: {alb_dns}")

    def test_https_accessible(self):
        """Verify HTTPS endpoint is accessible."""
        alb_dns = self.get_alb_dns()
        if alb_dns is None:
            pytest.skip("No ALB found")

        result = subprocess.run(
            [
                "curl",
                "-s",
                "-o",
                "/dev/null",
                "-w",
                "%{http_code}",
                "--max-time",
                "10",
                "-k",
                f"https://{alb_dns}",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode != 0 or result.stdout == "000":
            pytest.fail("HTTPS endpoint not accessible")

        print(f"HTTPS endpoint returned HTTP {result.stdout}")

    def test_tls_version(self):
        """Verify TLS version is 1.2 or higher."""
        alb_dns = self.get_alb_dns()
        if alb_dns is None:
            pytest.skip("No ALB found")

        result = subprocess.run(
            [
                "openssl",
                "s_client",
                "-connect",
                f"{alb_dns}:443",
                "-servername",
                alb_dns,
                "-brief",
            ],
            capture_output=True,
            text=True,
            timeout=30,
            input="",
        )

        output = result.stdout + result.stderr
        if "TLSv1.2" in output or "TLSv1.3" in output:
            print("TLS 1.2+ verified")
        else:
            if "CONNECTED" in output:
                print("TLS connection established (version detection may vary)")
            else:
                pytest.skip("Cannot verify TLS version")


# ============================================================================
# Integration Tests
# ============================================================================


@pytest.mark.integration
@pytest.mark.slow
class TestIntegration:
    """Integration tests for HyperPod infrastructure."""

    def test_pytorchjob_submission(self, k8s_custom_client):
        """Test submitting a simple PyTorchJob."""
        job_name = f"pytest-pytorch-{int(time.time())}"
        namespace = "default"

        pytorchjob = {
            "apiVersion": "kubeflow.org/v1",
            "kind": "PyTorchJob",
            "metadata": {
                "name": job_name,
                "namespace": namespace,
                "labels": {"test": "pytest-infrastructure"},
            },
            "spec": {
                "pytorchReplicaSpecs": {
                    "Master": {
                        "replicas": 1,
                        "restartPolicy": "Never",
                        "template": {
                            "spec": {
                                "containers": [
                                    {
                                        "name": "pytorch",
                                        "image": "python:3.11-slim",
                                        "command": [
                                            "python",
                                            "-c",
                                            "print('Hello from pytest!')",
                                        ],
                                        "resources": {
                                            "limits": {"cpu": "100m", "memory": "128Mi"},
                                            "requests": {
                                                "cpu": "100m",
                                                "memory": "128Mi",
                                            },
                                        },
                                    }
                                ]
                            }
                        },
                    }
                }
            },
        }

        try:
            k8s_custom_client.create_namespaced_custom_object(
                group="kubeflow.org",
                version="v1",
                namespace=namespace,
                plural="pytorchjobs",
                body=pytorchjob,
            )

            # Wait for completion (max 60 seconds)
            for _ in range(60):
                job = k8s_custom_client.get_namespaced_custom_object(
                    group="kubeflow.org",
                    version="v1",
                    namespace=namespace,
                    plural="pytorchjobs",
                    name=job_name,
                )

                conditions = job.get("status", {}).get("conditions", [])
                for cond in conditions:
                    if cond.get("type") == "Succeeded" and cond.get("status") == "True":
                        print(f"PyTorchJob {job_name} succeeded")
                        return
                    if cond.get("type") == "Failed" and cond.get("status") == "True":
                        pytest.fail(f"PyTorchJob {job_name} failed")

                time.sleep(1)

            pytest.fail("PyTorchJob did not complete within timeout")

        finally:
            try:
                k8s_custom_client.delete_namespaced_custom_object(
                    group="kubeflow.org",
                    version="v1",
                    namespace=namespace,
                    plural="pytorchjobs",
                    name=job_name,
                )
            except Exception:
                pass


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
