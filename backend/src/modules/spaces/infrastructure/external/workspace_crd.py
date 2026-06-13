"""HyperPod Workspace CRD 标识常量 (K8s 基础设施细节)。

集中定义 Workspace/WorkspaceConnection CRD 的 API group/version/kind,
供 K8sWorkspaceClient (拼 URL path) 和 HyperPodSpaceBackend (拼 apiVersion) 共用。

放在 infrastructure 层而非 domain 层: CRD apiVersion 是 Kubernetes 部署细节,
非领域概念 (遵循 Clean Architecture)。

字符串源自 AWS 文档 (task-governance/create-manage-spaces),
Phase B 安装 add-on 后需对照真实集群 CRD schema 核验。
"""

# Workspace CRD 标识
WORKSPACE_API_GROUP = "workspace.jupyter.org"
WORKSPACE_API_VERSION = "v1alpha1"
WORKSPACE_KIND = "Workspace"

# WorkspaceConnection CRD 标识
CONNECTION_API_GROUP = "connection.workspace.jupyter.org"
CONNECTION_API_VERSION = "v1alpha1"
CONNECTION_KIND = "WorkspaceConnection"

# apiVersion 完整形式 (group/version),用于 CRD body
WORKSPACE_API_VERSION_FULL = f"{WORKSPACE_API_GROUP}/{WORKSPACE_API_VERSION}"
CONNECTION_API_VERSION_FULL = f"{CONNECTION_API_GROUP}/{CONNECTION_API_VERSION}"
