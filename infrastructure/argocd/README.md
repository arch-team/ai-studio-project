# ArgoCD GitOps 配置

## 概述

本目录包含 AI Training Platform 的 ArgoCD GitOps 配置。

## 目录结构

```
argocd/
├── install.yaml              # ArgoCD 安装清单 (Namespace + Helm)
├── argocd-values.yaml        # ArgoCD Helm Values
├── projects/                 # ArgoCD AppProject 定义
│   ├── dev.yaml
│   ├── staging.yaml
│   └── prod.yaml
└── applications/             # ArgoCD Application 定义
    ├── backend-app.yaml
    └── frontend-app.yaml
```

## 安装步骤

```bash
# 1. 安装 ArgoCD
kubectl apply -f install.yaml

# 2. 等待 ArgoCD 就绪
kubectl wait --for=condition=available deployment/argocd-server -n argocd --timeout=300s

# 3. 创建 AppProjects
kubectl apply -f projects/

# 4. 创建 Applications
kubectl apply -f applications/

# 5. 获取初始密码
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
```
