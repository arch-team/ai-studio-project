"""HyperPod Workspace CRD 标识常量 (K8s 基础设施细节)。

集中定义 Workspace CRD 的 API group/version/kind,
供 K8sWorkspaceClient (拼 URL path) 和 HyperPodSpaceBackend (拼 apiVersion) 共用。

放在 infrastructure 层而非 domain 层: CRD apiVersion 是 Kubernetes 部署细节,
非领域概念 (遵循 Clean Architecture)。

字符串对照真实集群核验确认 (Phase B Task 15):
- 真实 add-on (amazon-sagemaker-spaces v0.1.6) 仅有 workspace.jupyter.org 一个 group
- 无独立 connection.workspace.jupyter.org CRD; 访问 URL 在 Workspace status.accessURL
"""

# Workspace CRD 标识
WORKSPACE_API_GROUP = "workspace.jupyter.org"
WORKSPACE_API_VERSION = "v1alpha1"
WORKSPACE_KIND = "Workspace"

# apiVersion 完整形式 (group/version),用于 CRD body
WORKSPACE_API_VERSION_FULL = f"{WORKSPACE_API_GROUP}/{WORKSPACE_API_VERSION}"

# add-on 安装的系统命名空间: 预置 WorkspaceTemplate / WorkspaceAccessStrategy 所在处
WORKSPACE_TEMPLATE_NAMESPACE = "jupyter-k8s-system"
