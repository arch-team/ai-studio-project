# Tasks: 企业级AI训练平台

**Input**: Design documents from `/specs/001-ai-training-platform/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/, quickstart.md

**Tests**: Tests are MANDATORY for production features per Constitution Principle X (Test Quality Assurance). Each user story MUST include unit tests, integration tests, and E2E tests.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `frontend/src/`
- Paths follow plan.md structure

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project root structure with backend/, frontend/, infra/ directories
- [X] T002 [P] Initialize Python 3.11+ backend project with FastAPI in backend/
- [X] T003 [P] Initialize TypeScript frontend project with React in frontend/
- [X] T004 [P] Configure Python linting (ruff) and formatting (black) in backend/pyproject.toml
- [X] T005 [P] Configure TypeScript linting (eslint) and formatting (prettier) in frontend/
- [X] T006 [P] Create backend dependency requirements in backend/requirements.txt
- [X] T007 [P] Create frontend package.json with dependencies in frontend/package.json
- [X] T008 Create Docker configuration files for local development (docker-compose.yml, Dockerfile.backend, Dockerfile.frontend)
- [X] T009 Configure environment variable management in backend/src/config/settings.py
- [X] T010 Setup logging configuration in backend/src/config/logging.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Database & ORM Setup

- [X] T011 Setup SQLAlchemy 2.0 async database connection in backend/src/config/database.py
- [X] T012 Create Alembic migration framework in backend/alembic/
- [X] T013 Create base model class with common fields in backend/src/models/base.py

### Core Entity Models (Shared Across Stories)

- [X] T014 [P] Create User model in backend/src/models/user/user.py
- [X] T015 [P] Create Team model in backend/src/models/user/team.py
- [X] T016 [P] Create Project model in backend/src/models/user/project.py
- [X] T017 Create database migration for User, Team, Project in backend/alembic/versions/001_users_teams_projects.py

### Authentication & Authorization Framework

- [X] T018 Implement JWT authentication middleware in backend/src/api/middleware/auth.py
- [X] T019 Implement RBAC authorization framework in backend/src/services/auth/rbac.py
- [X] T020 Create login/logout API endpoints in backend/src/api/rest/auth.py

### Tests for Authentication (MANDATORY per Constitution) ✅

- [X] T020A [P] Unit tests for JWT middleware in backend/tests/unit/middleware/test_auth.py
- [X] T020B [P] Unit tests for RBAC framework in backend/tests/unit/services/test_rbac.py
- [X] T020C Integration tests for auth API endpoints in backend/tests/integration/api/test_auth_api.py

### API Infrastructure

- [X] T021 Create FastAPI application factory with HTTPS support in backend/src/main.py
- [X] T022 Create API router configuration in backend/src/api/router.py
- [X] T023 Implement global exception handler in backend/src/api/middleware/exception_handler.py
- [X] T024 Implement request/response logging middleware in backend/src/api/middleware/logging.py
- [X] T025 Create common response models in backend/src/api/schemas/common.py
- [X] T026 Configure TLS 1.2+ enforcement and cipher suites in backend/src/config/tls.py
- [X] T027 Create pagination utilities in backend/src/api/utils/pagination.py

### Frontend Infrastructure

- [X] T028 Setup React Router configuration in frontend/src/router/index.tsx
- [X] T029 Create authentication context and hook in frontend/src/services/auth/AuthContext.tsx
- [X] T030 Create API client service in frontend/src/services/api/client.ts
- [X] T031 Setup global state management (Zustand) in frontend/src/services/store/index.ts
- [X] T032 Create shared UI components (Button, Input, Card, Modal) in frontend/src/components/shared/

**关卡**: 基础层就绪 - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - 算法工程师提交和监控分布式训练任务 (Priority: P1) 🎯 MVP

**Goal**: Enable algorithm engineers to submit PyTorch distributed training jobs and monitor progress in real-time

**Independent Test**: Submit a distributed training job, monitor its status, view metrics and logs, verify auto-recovery from checkpoint

### Backend Models for US1

- [X] T032 [P] [US1] Create TrainingJob model in backend/src/models/training/training_job.py
- [X] T033 [P] [US1] Create Checkpoint model in backend/src/models/training/checkpoint.py
- [X] T034 [P] [US1] Create MetricsLog model in backend/src/models/monitoring/metrics_log.py
- [X] T035 [US1] Create database migration for training entities in backend/alembic/versions/002_training_jobs.py

### Backend Services for US1

- [X] T036 [US1] Implement TrainingJobService in backend/src/services/training/job_service.py
- [X] T037 [US1] Implement HyperPod Training Operator integration (使用最新stable版本,参考AWS官方文档) in backend/src/services/training/operators/hyperpod_operator.py
- [X] T038 [US1] Implement distributed training templates (DDP, FSDP, DeepSpeed) in backend/src/services/training/templates/
- [X] T039 [US1] Implement Gang Scheduling via Kueue in backend/src/services/training/scheduler/gang_scheduler.py
- [X] T040 [US1] Implement CheckpointService with tiered storage in backend/src/services/checkpoint/checkpoint_service.py
- [X] T041 [US1] Implement tiered checkpoint storage (NVMe→FSx→S3) in backend/src/services/checkpoint/tiered_storage.py
- [X] T042 [US1] Implement auto-recovery service in backend/src/services/checkpoint/recovery/auto_recovery.py
- [X] T043 [US1] Implement MetricsCollectionService in backend/src/services/monitoring/metrics/metrics_service.py
- [X] T043A [US1] Implement network performance monitoring in backend/src/services/monitoring/metrics/network_metrics.py
- [X] T043B [US1] Implement training job timeout and stall detection in backend/src/services/training/monitoring/stall_detector.py

### Backend API for US1

- [X] T044 [US1] Create TrainingJob request/response schemas in backend/src/api/schemas/training.py
- [X] T045 [US1] Implement POST /training-jobs endpoint in backend/src/api/rest/training/jobs.py
- [X] T046 [US1] Implement GET /training-jobs list endpoint in backend/src/api/rest/training/jobs.py
- [X] T047 [US1] Implement GET /training-jobs/{id} detail endpoint in backend/src/api/rest/training/jobs.py
- [X] T048 [US1] Implement PUT /training-jobs/{id} update endpoint in backend/src/api/rest/training/jobs.py
- [X] T049 [US1] Implement DELETE /training-jobs/{id} endpoint in backend/src/api/rest/training/jobs.py
- [X] T050 [US1] Implement POST /training-jobs/{id}/actions/start endpoint in backend/src/api/rest/training/jobs.py
- [X] T051 [US1] Implement POST /training-jobs/{id}/actions/stop endpoint in backend/src/api/rest/training/jobs.py
- [X] T052 [US1] Implement POST /training-jobs/{id}/actions/resume endpoint in backend/src/api/rest/training/jobs.py
- [X] T053 [US1] Implement GET /training-jobs/{id}/metrics endpoint in backend/src/api/rest/training/jobs.py
- [X] T054 [US1] Implement GET /training-jobs/{id}/logs endpoint in backend/src/api/rest/training/jobs.py
- [X] T055 [US1] Implement GET /training-jobs/{id}/checkpoints endpoint in backend/src/api/rest/training/jobs.py

### Kubernetes Resources for US1

- [X] T056 [P] [US1] Create TrainingJob CRD definition in backend/k8s/crds/training-job-crd.yaml
- [X] T057 [P] [US1] Create PyTorchJob deployment template in backend/k8s/deployments/pytorch-job-template.yaml
- [X] T058 [P] [US1] Create RBAC configuration for training operator in backend/k8s/rbac/training-operator-rbac.yaml
- [X] T058A [P] [US1] Create NetworkPolicy templates for training job isolation in backend/k8s/deployments/network-policy-template.yaml

### Tests for US1 (MANDATORY) ✅

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation (TDD approach per Constitution Principle X)**

- [X] T055A [P] [US1] Unit tests for TrainingJobService in backend/tests/unit/services/training/test_job_service.py
- [X] T055B [P] [US1] Unit tests for CheckpointService in backend/tests/unit/services/checkpoint/test_checkpoint_service.py
- [X] T055C [P] [US1] Integration tests for training API endpoints in backend/tests/integration/api/test_training_api.py
- [ ] T055D [US1] E2E test for complete training job submission and monitoring in backend/tests/e2e/test_training_workflow.py

### Frontend for US1

- [X] T059 [P] [US1] Create TrainingJob TypeScript types in frontend/src/types/training.ts
- [X] T060 [US1] Create TrainingJob API client in frontend/src/services/api/training.ts
- [X] T061 [US1] Create TrainingJobList page in frontend/src/pages/training/TrainingJobList.tsx
- [X] T062 [US1] Create TrainingJobDetail page in frontend/src/pages/training/TrainingJobDetail.tsx
- [X] T063 [US1] Create TrainingJobCreate form in frontend/src/components/training/TrainingJobForm.tsx
- [X] T064 [US1] Create real-time metrics chart component in frontend/src/components/training/MetricsChart.tsx
- [X] T065 [US1] Create training logs viewer component in frontend/src/components/training/LogViewer.tsx
- [X] T066 [US1] Create checkpoints list component in frontend/src/components/training/CheckpointList.tsx
- [X] T067 [US1] Create job status indicator component in frontend/src/components/training/JobStatusBadge.tsx
- [X] T068 [US1] Integrate training pages into router in frontend/src/router/training.tsx

**关卡**: 用户故事1完成 - Algorithm engineers can submit and monitor distributed training jobs

---

## Phase 4: User Story 2 - 数据工程师管理和版本控制训练数据集 (Priority: P1)

**Goal**: Enable data engineers to upload, manage, and version control large-scale training datasets

**Independent Test**: Upload a 10GB+ dataset with resumable upload, create versions, compare versions, link dataset to training job

### Backend Models for US2

- [ ] T069 [P] [US2] Create Dataset model in backend/src/models/dataset/dataset.py
- [ ] T070 [P] [US2] Create DatasetVersion model in backend/src/models/dataset/dataset_version.py
- [ ] T071 [US2] Create database migration for dataset entities in backend/alembic/versions/003_datasets.py

### Backend Services for US2

- [ ] T072 [US2] Implement DatasetService in backend/src/services/dataset/dataset_service.py
- [ ] T073 [US2] Implement DatasetVersionService in backend/src/services/dataset/version/version_service.py
- [ ] T074 [US2] Implement S3 multipart upload for large files in backend/src/services/dataset/storage/s3_storage.py
- [ ] T075 [US2] Implement FSx integration for high-performance access in backend/src/services/dataset/storage/fsx_storage.py
- [ ] T076 [US2] Implement version comparison service in backend/src/services/dataset/version/version_compare.py
- [ ] T077 [US2] Implement data integrity verification in backend/src/services/dataset/validation/integrity_checker.py
- [ ] T077A [US2] Implement storage capacity monitoring and alerting in backend/src/services/dataset/storage/capacity_monitor.py
- [ ] T077A1 [US2] Integrate storage capacity alerts with notification system in backend/src/services/dataset/storage/alert_integration.py
- [ ] T077B [US2] Implement auto-scaling and data tiering configuration in backend/src/services/dataset/storage/scaling_manager.py

### Backend API for US2

- [ ] T078 [US2] Create Dataset request/response schemas in backend/src/api/schemas/dataset.py
- [ ] T079 [US2] Implement POST /datasets endpoint in backend/src/api/rest/dataset/datasets.py
- [ ] T080 [US2] Implement GET /datasets list endpoint in backend/src/api/rest/dataset/datasets.py
- [ ] T081 [US2] Implement GET /datasets/{id} detail endpoint in backend/src/api/rest/dataset/datasets.py
- [ ] T082 [US2] Implement PUT /datasets/{id} update endpoint in backend/src/api/rest/dataset/datasets.py
- [ ] T083 [US2] Implement DELETE /datasets/{id} endpoint in backend/src/api/rest/dataset/datasets.py
- [ ] T084 [US2] Implement POST /datasets/{id}/versions endpoint in backend/src/api/rest/dataset/versions.py
- [ ] T085 [US2] Implement GET /datasets/{id}/versions list endpoint in backend/src/api/rest/dataset/versions.py
- [ ] T086 [US2] Implement GET /datasets/{id}/versions/{version_id} endpoint in backend/src/api/rest/dataset/versions.py
- [ ] T087 [US2] Implement POST /datasets/{id}/versions/{version_id}/files upload endpoint in backend/src/api/rest/dataset/files.py
- [ ] T088 [US2] Implement GET /datasets/{id}/versions/{version_id}/files list endpoint in backend/src/api/rest/dataset/files.py
- [ ] T089 [US2] Implement POST /datasets/{id}/versions/{version_id}/actions/finalize endpoint in backend/src/api/rest/dataset/versions.py
- [ ] T090 [US2] Implement POST /datasets/{id}/versions/{version_id}/actions/compare endpoint in backend/src/api/rest/dataset/versions.py

### Tests for US2 (MANDATORY) ✅

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation (TDD approach per Constitution Principle X)**

- [ ] T090A [P] [US2] Unit tests for DatasetService in backend/tests/unit/services/dataset/test_dataset_service.py
- [ ] T090B [P] [US2] Unit tests for S3 multipart upload in backend/tests/unit/services/dataset/test_s3_storage.py
- [ ] T090C [P] [US2] Integration tests for dataset API endpoints in backend/tests/integration/api/test_dataset_api.py
- [ ] T090D [US2] E2E test for large file upload with resume in backend/tests/e2e/test_dataset_upload.py
- [ ] T090E [P] [US2] Integration test for storage capacity alerting (verify <10% threshold triggers alert) in backend/tests/integration/services/test_capacity_alerting.py

### Frontend for US2

- [ ] T091 [P] [US2] Create Dataset TypeScript types in frontend/src/types/dataset.ts
- [ ] T092 [US2] Create Dataset API client in frontend/src/services/api/dataset.ts
- [ ] T093 [US2] Create DatasetList page in frontend/src/pages/dataset/DatasetList.tsx
- [ ] T094 [US2] Create DatasetDetail page in frontend/src/pages/dataset/DatasetDetail.tsx
- [ ] T095 [US2] Create DatasetCreate form in frontend/src/components/dataset/DatasetForm.tsx
- [ ] T096 [US2] Create chunked file uploader component with resume in frontend/src/components/dataset/ChunkedUploader.tsx
- [ ] T097 [US2] Create version list component in frontend/src/components/dataset/VersionList.tsx
- [ ] T098 [US2] Create version comparison view in frontend/src/components/dataset/VersionCompare.tsx
- [ ] T099 [US2] Create file browser component in frontend/src/components/dataset/FileBrowser.tsx
- [ ] T100 [US2] Integrate dataset pages into router in frontend/src/router/dataset.tsx

**关卡**: 用户故事2完成 - Data engineers can upload and version control datasets

---

## Phase 5: User Story 3 - 平台管理员配置资源配额和监控集群 (Priority: P1)

**Goal**: Enable platform admins to configure resource quotas, set priority policies, and monitor cluster status

**Independent Test**: Create team quota, configure resource limits by role, verify quota enforcement, view cluster monitoring dashboard

### Backend Models for US3

- [ ] T101 [P] [US3] Create ResourceQuota model in backend/src/models/resource/resource_quota.py
- [ ] T102 [P] [US3] Create ResourceLimitConfig model in backend/src/models/resource/resource_limit_config.py
- [ ] T103 [US3] Create database migration for resource entities in backend/alembic/versions/004_resource_quotas.py

### Backend Services for US3

- [ ] T104 [US3] Implement ResourceQuotaService in backend/src/services/resource/quota/quota_service.py
- [ ] T105 [US3] Implement ResourceLimitConfigService in backend/src/services/resource/quota/limit_config_service.py
- [ ] T106 [US3] Implement HyperPod Task Governance integration in backend/src/services/resource/governance/task_governance.py
- [ ] T107 [US3] Implement quota enforcement middleware in backend/src/services/resource/governance/quota_enforcer.py
- [ ] T108 [US3] Implement preemption with checkpoint creation in backend/src/services/resource/governance/preemption_handler.py
- [ ] T109 [US3] Implement resource usage tracking in backend/src/services/resource/quota/usage_tracker.py
- [ ] T110 [US3] Implement cluster metrics service in backend/src/services/monitoring/metrics/cluster_metrics.py

### Backend API for US3

- [ ] T111 [US3] Create ResourceQuota request/response schemas in backend/src/api/schemas/resource.py
- [ ] T112 [US3] Implement POST /resources/quotas endpoint in backend/src/api/rest/resource/quotas.py
- [ ] T113 [US3] Implement GET /resources/quotas list endpoint in backend/src/api/rest/resource/quotas.py
- [ ] T114 [US3] Implement GET /resources/quotas/{id} detail endpoint in backend/src/api/rest/resource/quotas.py
- [ ] T115 [US3] Implement PUT /resources/quotas/{id} update endpoint in backend/src/api/rest/resource/quotas.py
- [ ] T116 [US3] Implement DELETE /resources/quotas/{id} endpoint in backend/src/api/rest/resource/quotas.py
- [ ] T117 [US3] Implement GET /resources/quotas/usage endpoint in backend/src/api/rest/resource/quotas.py
- [ ] T118 [US3] Implement PUT /resources/quotas/{id}/actions/override endpoint in backend/src/api/rest/resource/quotas.py
- [ ] T119 [US3] Implement CRUD for /resources/limit-configs endpoints in backend/src/api/rest/resource/limit_configs.py
- [ ] T120 [US3] Implement GET /resources/clusters list endpoint in backend/src/api/rest/resource/clusters.py
- [ ] T121 [US3] Implement GET /resources/clusters/{id} detail endpoint in backend/src/api/rest/resource/clusters.py
- [ ] T122 [US3] Implement GET /resources/clusters/{id}/nodes endpoint in backend/src/api/rest/resource/clusters.py
- [ ] T123 [US3] Implement GET /resources/clusters/{id}/metrics endpoint in backend/src/api/rest/resource/clusters.py

### Kubernetes Resources for US3

- [ ] T124 [P] [US3] Create Kueue ClusterQueue configuration in backend/k8s/deployments/kueue-cluster-queue.yaml
- [ ] T125 [P] [US3] Create Kueue LocalQueue templates in backend/k8s/deployments/kueue-local-queue-template.yaml
- [ ] T126 [P] [US3] Create ResourceQuota namespace template in backend/k8s/rbac/namespace-quota-template.yaml

### Tests for US3 (MANDATORY) ✅

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation (TDD approach per Constitution Principle X)**

- [ ] T126A [P] [US3] Unit tests for ResourceQuotaService in backend/tests/unit/services/resource/test_quota_service.py
- [ ] T126B [P] [US3] Unit tests for quota enforcement in backend/tests/unit/services/resource/test_quota_enforcer.py
- [ ] T126C [P] [US3] Integration tests for resource API endpoints in backend/tests/integration/api/test_resource_api.py
- [ ] T126D [US3] E2E test for quota configuration and enforcement in backend/tests/e2e/test_quota_workflow.py

### Frontend for US3

- [ ] T127 [P] [US3] Create Resource TypeScript types in frontend/src/types/resource.ts
- [ ] T128 [US3] Create Resource API client in frontend/src/services/api/resource.ts
- [ ] T129 [US3] Create QuotaManagement page in frontend/src/pages/resource/QuotaManagement.tsx
- [ ] T130 [US3] Create QuotaForm component in frontend/src/components/resource/QuotaForm.tsx
- [ ] T131 [US3] Create QuotaUsageChart component in frontend/src/components/resource/QuotaUsageChart.tsx
- [ ] T132 [US3] Create LimitConfigForm component in frontend/src/components/resource/LimitConfigForm.tsx
- [ ] T133 [US3] Create ClusterOverview page in frontend/src/pages/resource/ClusterOverview.tsx
- [ ] T134 [US3] Create ClusterMetricsChart component in frontend/src/components/resource/ClusterMetricsChart.tsx
- [ ] T135 [US3] Create NodeList component in frontend/src/components/resource/NodeList.tsx
- [ ] T136 [US3] Integrate resource pages into router in frontend/src/router/resource.tsx

**关卡**: 用户故事3完成 - Admins can configure quotas and monitor clusters

---

## Phase 6: User Story 4 - 项目经理查看资源使用报表和成本分析 (Priority: P2)

**Goal**: Enable project managers to view resource usage reports, analyze costs, and receive budget alerts

**Independent Test**: View monthly usage report, compare project costs, receive budget warning notification

### Backend Services for US4

- [ ] T137 [US4] Implement ResourceUsageService in backend/src/services/resource/cost/usage_service.py
- [ ] T138 [US4] Implement CostAnalysisService in backend/src/services/resource/cost/cost_analysis.py
- [ ] T139 [US4] Implement CostForecastService in backend/src/services/resource/cost/cost_forecast.py
- [ ] T140 [US4] Implement BudgetAlertService in backend/src/services/resource/cost/budget_alert.py

### Backend API for US4

- [ ] T141 [US4] Create cost analysis request/response schemas in backend/src/api/schemas/cost.py
- [ ] T142 [US4] Implement GET /resources/usage endpoint in backend/src/api/rest/resource/usage.py
- [ ] T143 [US4] Implement GET /resources/usage/history endpoint in backend/src/api/rest/resource/usage.py
- [ ] T144 [US4] Implement GET /resources/usage/{owner_type}/{owner_id} endpoint in backend/src/api/rest/resource/usage.py
- [ ] T145 [US4] Implement GET /resources/costs endpoint in backend/src/api/rest/resource/costs.py
- [ ] T146 [US4] Implement GET /resources/costs/forecast endpoint in backend/src/api/rest/resource/costs.py
- [ ] T147 [US4] Implement GET /resources/costs/{owner_type}/{owner_id} endpoint in backend/src/api/rest/resource/costs.py

### Tests for US4 (MANDATORY) ✅

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation (TDD approach per Constitution Principle X)**

- [ ] T147A [P] [US4] Unit tests for CostAnalysisService in backend/tests/unit/services/resource/test_cost_analysis.py
- [ ] T147B [P] [US4] Integration tests for cost API endpoints in backend/tests/integration/api/test_cost_api.py
- [ ] T147C [US4] E2E test for cost analysis report generation in backend/tests/e2e/test_cost_report.py

### Frontend for US4

- [ ] T148 [P] [US4] Create Cost TypeScript types in frontend/src/types/cost.ts
- [ ] T149 [US4] Create Cost API client in frontend/src/services/api/cost.ts
- [ ] T150 [US4] Create UsageReport page in frontend/src/pages/resource/UsageReport.tsx
- [ ] T151 [US4] Create CostAnalysis page in frontend/src/pages/resource/CostAnalysis.tsx
- [ ] T152 [US4] Create UsageTrendChart component in frontend/src/components/resource/UsageTrendChart.tsx
- [ ] T153 [US4] Create CostBreakdownChart component in frontend/src/components/resource/CostBreakdownChart.tsx
- [ ] T154 [US4] Create CostForecastChart component in frontend/src/components/resource/CostForecastChart.tsx
- [ ] T155 [US4] Create ProjectComparison component in frontend/src/components/resource/ProjectComparison.tsx
- [ ] T156 [US4] Integrate cost pages into router in frontend/src/router/cost.tsx

**关卡**: 用户故事4完成 - Project managers can analyze costs and usage

---

## Phase 7: User Story 5 - 算法工程师使用在线开发环境 (Priority: P2)

**Goal**: Enable algorithm engineers to use online JupyterLab/VS Code development environments with GPU access

**Independent Test**: Launch JupyterLab environment, run GPU-accelerated code, submit experiment as training job

### Backend Services for US5

- [ ] T157 [US5] Implement DevEnvironmentService in backend/src/services/development/env_service.py
- [ ] T158 [US5] Implement SageMaker Spaces Add-on integration in backend/src/services/development/spaces/spaces_integration.py
- [ ] T159 [US5] Implement environment resource allocation in backend/src/services/development/spaces/resource_allocator.py
- [ ] T160 [US5] Implement experiment-to-job conversion in backend/src/services/development/experiment/job_converter.py

### Backend API for US5

- [ ] T161 [US5] Create development environment request/response schemas in backend/src/api/schemas/development.py
- [ ] T162 [US5] Implement POST /environments endpoint in backend/src/api/rest/development/environments.py
- [ ] T163 [US5] Implement GET /environments list endpoint in backend/src/api/rest/development/environments.py
- [ ] T164 [US5] Implement GET /environments/{id} detail endpoint in backend/src/api/rest/development/environments.py
- [ ] T165 [US5] Implement POST /environments/{id}/actions/start endpoint in backend/src/api/rest/development/environments.py
- [ ] T166 [US5] Implement POST /environments/{id}/actions/stop endpoint in backend/src/api/rest/development/environments.py
- [ ] T167 [US5] Implement POST /environments/{id}/actions/submit-job endpoint in backend/src/api/rest/development/environments.py

### Tests for US5 (MANDATORY) ✅

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation (TDD approach per Constitution Principle X)**

- [ ] T167A [P] [US5] Unit tests for DevEnvironmentService in backend/tests/unit/services/development/test_env_service.py
- [ ] T167B [P] [US5] Integration tests for development API endpoints in backend/tests/integration/api/test_development_api.py
- [ ] T167C [US5] E2E test for environment launch and job submission in backend/tests/e2e/test_dev_environment.py

### Frontend for US5

- [ ] T168 [P] [US5] Create Development TypeScript types in frontend/src/types/development.ts
- [ ] T169 [US5] Create Development API client in frontend/src/services/api/development.ts
- [ ] T170 [US5] Create EnvironmentList page in frontend/src/pages/development/EnvironmentList.tsx
- [ ] T171 [US5] Create EnvironmentLauncher component in frontend/src/components/development/EnvironmentLauncher.tsx
- [ ] T172 [US5] Create EnvironmentCard component in frontend/src/components/development/EnvironmentCard.tsx
- [ ] T173 [US5] Create SubmitJobDialog component in frontend/src/components/development/SubmitJobDialog.tsx
- [ ] T174 [US5] Integrate development pages into router in frontend/src/router/development.tsx

**关卡**: 用户故事5完成 - Engineers can use online development environments

---

## Phase 8: Monitoring & Observability (Cross-Cutting)

**Purpose**: Comprehensive monitoring, alerting, and observability for the platform

### Backend Services for Monitoring

- [ ] T175 [P] Implement MonitoringService in backend/src/services/monitoring/monitoring_service.py
- [ ] T176 [P] Implement AlertService in backend/src/services/monitoring/alerts/alert_service.py
- [ ] T177 [P] Implement AlertRuleService in backend/src/services/monitoring/alerts/alert_rule_service.py
- [ ] T178 Implement HyperPod Observability Add-on integration in backend/src/services/monitoring/integration/observability_addon.py
- [ ] T179 Implement PromQL query executor in backend/src/services/monitoring/metrics/promql_executor.py
- [ ] T180 Implement log aggregation service in backend/src/services/monitoring/logs/log_aggregator.py
- [ ] T180A Implement log query performance optimization (indexing, caching, pagination) in backend/src/services/monitoring/logs/query_optimizer.py
- [ ] T181 Implement notification channel service in backend/src/services/monitoring/notifications/channel_service.py
- [ ] T182 Implement notification subscription service in backend/src/services/monitoring/notifications/subscription_service.py
- [ ] T183 Implement health check service in backend/src/services/monitoring/health/health_service.py
- [ ] T183A [P] Define platform SLI/SLO for 99% availability target in backend/src/services/monitoring/slo/sli_definition.py
- [ ] T183B Implement availability monitoring dashboard in backend/src/services/monitoring/dashboards/availability_dashboard.py
- [ ] T183C Configure availability alerting for SLO violations in backend/src/services/monitoring/alerts/slo_alerts.py
- [ ] T183D [P] Implement storage capacity monitoring and alerting (threshold: 90%) in backend/src/services/monitoring/storage/capacity_monitor.py

### Backend API for Monitoring

- [ ] T184 Create monitoring request/response schemas in backend/src/api/schemas/monitoring.py
- [ ] T185 Implement GET /monitoring/metrics endpoint in backend/src/api/rest/monitoring/metrics.py
- [ ] T186 Implement POST /monitoring/metrics/query endpoint in backend/src/api/rest/monitoring/metrics.py
- [ ] T187 Implement GET /monitoring/metrics/training-jobs/{job_id} endpoint in backend/src/api/rest/monitoring/metrics.py
- [ ] T188 Implement GET /monitoring/metrics/nodes/{node_id} endpoint in backend/src/api/rest/monitoring/metrics.py
- [ ] T189 Implement monitoring dashboards CRUD endpoints in backend/src/api/rest/monitoring/dashboards.py
- [ ] T190 Implement GET /monitoring/logs endpoint in backend/src/api/rest/monitoring/logs.py
- [ ] T191 Implement POST /monitoring/logs/search endpoint in backend/src/api/rest/monitoring/logs.py
- [ ] T192 Implement alerts CRUD endpoints in backend/src/api/rest/monitoring/alerts.py
- [ ] T193 Implement alert-rules CRUD endpoints in backend/src/api/rest/monitoring/alert_rules.py
- [ ] T194 Implement GET /monitoring/health endpoint in backend/src/api/rest/monitoring/health.py
- [ ] T195 Implement notification channels CRUD endpoints in backend/src/api/rest/monitoring/notifications.py
- [ ] T196 Implement notification subscriptions CRUD endpoints in backend/src/api/rest/monitoring/subscriptions.py

### Frontend for Monitoring

- [ ] T197 [P] Create Monitoring TypeScript types in frontend/src/types/monitoring.ts
- [ ] T198 Create Monitoring API client in frontend/src/services/api/monitoring.ts
- [ ] T199 Create Dashboard page with customizable panels in frontend/src/pages/dashboard/Dashboard.tsx
- [ ] T200 Create AlertList page in frontend/src/pages/monitoring/AlertList.tsx
- [ ] T201 Create AlertRuleManagement page in frontend/src/pages/monitoring/AlertRuleManagement.tsx
- [ ] T202 Create SystemHealth page in frontend/src/pages/monitoring/SystemHealth.tsx
- [ ] T203 Create MetricsPanel component in frontend/src/components/monitoring/MetricsPanel.tsx
- [ ] T204 Create AlertBadge component in frontend/src/components/monitoring/AlertBadge.tsx
- [ ] T205 Create HealthStatusIndicator component in frontend/src/components/monitoring/HealthStatusIndicator.tsx
- [ ] T206 Integrate monitoring pages into router in frontend/src/router/monitoring.tsx

### Tests for Monitoring (MANDATORY) ✅

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation (TDD approach per Constitution Principle X)**

- [ ] T206A [P] Unit tests for log query optimization in backend/tests/unit/services/monitoring/test_query_optimizer.py
- [ ] T206B [P] Integration tests for monitoring API endpoints in backend/tests/integration/api/test_monitoring_api.py
- [ ] T206C Performance test for log query P99<3s requirement in backend/tests/performance/test_log_query_performance.py
- [ ] T206D E2E test for monitoring dashboard and alerting workflow in backend/tests/e2e/test_monitoring_workflow.py

---

## Phase 9: Model Management (Cross-Cutting)

**Purpose**: Model versioning, registration, and lifecycle management

### Backend Models for Model Management

- [ ] T207 [P] Create Model model in backend/src/models/model/model.py
- [ ] T208 [P] Create ModelVersion model in backend/src/models/model/model_version.py
- [ ] T209 Create database migration for model entities in backend/alembic/versions/005_models.py

### Backend Services for Model Management

- [ ] T210 Implement ModelService in backend/src/services/model/model_service.py
- [ ] T211 Implement ModelVersionService in backend/src/services/model/version_service.py
- [ ] T212 Implement SageMaker Model Registry integration in backend/src/services/model/registry/sagemaker_registry.py
- [ ] T213 [P] Deploy SageMaker Managed MLflow instance with CDK in infra/cdk/mlflow/mlflow_stack.py
- [ ] T213A Configure MLflow tracking server integration in backend/src/config/mlflow.py
- [ ] T213B Implement training job MLflow logging in backend/src/services/training/mlflow_logger.py
- [ ] T213C Add MLflow experiment UI integration in frontend/src/pages/experiments/ExperimentList.tsx

### Backend API for Model Management

- [ ] T214 Create model request/response schemas in backend/src/api/schemas/model.py
- [ ] T215 Implement models CRUD endpoints in backend/src/api/rest/model/models.py
- [ ] T216 Implement model versions CRUD endpoints in backend/src/api/rest/model/versions.py

### Frontend for Model Management

- [ ] T217 [P] Create Model TypeScript types in frontend/src/types/model.ts
- [ ] T218 Create Model API client in frontend/src/services/api/model.ts
- [ ] T219 Create ModelList page in frontend/src/pages/model/ModelList.tsx
- [ ] T220 Create ModelDetail page in frontend/src/pages/model/ModelDetail.tsx
- [ ] T221 Create ModelVersionList component in frontend/src/components/model/ModelVersionList.tsx
- [ ] T222 Integrate model pages into router in frontend/src/router/model.tsx

### Tests for Model Management (MANDATORY) ✅

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation (TDD approach per Constitution Principle X)**

- [ ] T222A [P] Unit tests for ModelService in backend/tests/unit/services/model/test_model_service.py
- [ ] T222B [P] Unit tests for ModelVersionService in backend/tests/unit/services/model/test_model_version_service.py
- [ ] T222C [P] Integration tests for model API endpoints in backend/tests/integration/api/test_model_api.py
- [ ] T222D E2E test for model registration and versioning workflow in backend/tests/e2e/test_model_workflow.py

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

### Security Hardening

- [ ] T223 [P] Implement rate limiting middleware in backend/src/api/middleware/rate_limiter.py
- [ ] T224 [P] Implement request validation middleware in backend/src/api/middleware/validator.py
- [ ] T225 [P] Implement audit logging service in backend/src/services/audit/audit_service.py
- [ ] T226 Configure ingress controller TLS termination with cert-manager in infra/helm/ai-platform/values.yaml

### Data Encryption (FR-018)

- [ ] T241 [P] Configure S3 bucket default encryption with KMS in infra/cdk/storage/s3_encryption.py
- [ ] T242 [P] Configure FSx for Lustre data-at-rest encryption in infra/cdk/storage/fsx_encryption.py
- [ ] T243 [P] Configure EFS filesystem encryption in infra/cdk/storage/efs_encryption.py
- [ ] T244 Implement KMS key management service in backend/src/services/security/kms_service.py
- [ ] T245 Implement encryption status validation in backend/src/services/security/encryption_validator.py

### Performance Optimization

- [ ] T227 [P] Implement Redis caching layer in backend/src/services/cache/redis_cache.py
- [ ] T228 [P] Add database query optimization and indexing in backend/alembic/versions/006_indexes.py
- [ ] T229 [P] Implement API response compression in backend/src/api/middleware/compression.py

### Documentation

- [ ] T230 [P] Generate OpenAPI documentation in backend/docs/openapi.yaml
- [ ] T231 [P] Create API usage examples in backend/docs/api-examples.md

### User Onboarding & Quick Start

- [ ] T230A [P] Create quickstart guide in docs/quickstart.md
- [ ] T230B [P] Create example PyTorch training scripts in examples/pytorch/
- [ ] T230C [P] Create step-by-step user tutorial in docs/tutorials/getting-started.md
- [ ] T230D [P] Create troubleshooting FAQ in docs/troubleshooting.md

### Infrastructure as Code

- [ ] T232 [P] Create AWS CDK HyperPod cluster definition in infra/cdk/hyperpod/cluster.py
- [ ] T233 [P] Create AWS CDK storage resources (FSx, S3, EFS) in infra/cdk/storage/storage.py
- [ ] T234 [P] Create AWS CDK networking configuration in infra/cdk/networking/vpc.py
- [ ] T235 [P] Create Helm chart for platform deployment in infra/helm/ai-platform/
- [ ] T236 [P] Create ArgoCD application definitions in infra/argocd/applications/
- [ ] T236A [P] Create ArgoCD project definitions in infra/argocd/projects/
- [ ] T236B Configure ArgoCD auto-sync policies and health checks in infra/argocd/applications/
- [ ] T236C Configure ArgoCD integration with Helm charts in infra/argocd/applications/

### Tests for Security Hardening (MANDATORY) ✅

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation (TDD approach per Constitution Principle X)**

- [ ] T246 [P] Unit tests for rate limiting middleware in backend/tests/unit/middleware/test_rate_limiter.py
- [ ] T247 [P] Unit tests for request validation in backend/tests/unit/middleware/test_validator.py
- [ ] T248 [P] Integration tests for audit logging in backend/tests/integration/services/test_audit_logging.py
- [ ] T249 Security penetration tests for authentication in backend/tests/security/test_auth_security.py

### Tests for Data Encryption (MANDATORY) ✅

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation (TDD approach per Constitution Principle X)**

- [ ] T250 [P] Unit tests for KMS key management in backend/tests/unit/services/security/test_kms_service.py
- [ ] T251 Integration test for encryption status validation in backend/tests/integration/services/test_encryption_validation.py
- [ ] T252 Verify S3/FSx/EFS encryption configuration in backend/tests/integration/infra/test_storage_encryption.py

### Tests for Performance Optimization (MANDATORY) ✅

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation (TDD approach per Constitution Principle X)**

- [ ] T253 [P] Unit tests for Redis caching layer in backend/tests/unit/services/cache/test_redis_cache.py
- [ ] T254 Performance benchmark tests for API response times in backend/tests/performance/test_api_performance.py
- [ ] T255 Load testing for 1000+ registered users in backend/tests/performance/test_load_1000_users.py

### Validation

- [ ] T237 Run quickstart.md validation scenarios
- [ ] T238 Verify all API contracts match implementation
- [ ] T239 Perform end-to-end integration testing

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-7)**: All depend on Foundational phase completion
  - US1, US2, US3 can proceed in parallel (all P1 priority)
  - US4, US5 can start after Foundational (P2, can proceed in parallel with each other)
- **Monitoring (Phase 8)**: Can start after Foundational, integrates with all user stories
- **Model Management (Phase 9)**: Can start after US1 completion (depends on training jobs)
- **Polish (Phase 10)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational - No dependencies on other stories
- **User Story 2 (P1)**: Can start after Foundational - Independent, but datasets can be linked to US1 jobs
- **User Story 3 (P1)**: Can start after Foundational - Quota enforcement applies to US1 jobs
- **User Story 4 (P2)**: Can start after Foundational - Uses data from US1-US3
- **User Story 5 (P2)**: Can start after Foundational - Can submit jobs from US1

### Within Each User Story

- Models before services
- Services before endpoints
- Backend API before frontend
- Core implementation before integration

### Parallel Opportunities

**Phase 1 (All [P]):**
```
Task: T002 Initialize Python backend
Task: T003 Initialize TypeScript frontend
Task: T004 Configure Python linting
Task: T005 Configure TypeScript linting
Task: T006 Create backend dependencies
Task: T007 Create frontend package.json
```

**Phase 2 (Foundational [P]):**
```
Task: T014 Create User model
Task: T015 Create Team model
Task: T016 Create Project model
```

**Phase 3 (US1 Models [P]):**
```
Task: T032 Create TrainingJob model
Task: T033 Create Checkpoint model
Task: T034 Create MetricsLog model
```

**Phase 4 (US2 Models [P]):**
```
Task: T069 Create Dataset model
Task: T070 Create DatasetVersion model
```

**Multi-Story Parallel (After Phase 2):**
```
Developer A: User Story 1 (Training Jobs)
Developer B: User Story 2 (Datasets)
Developer C: User Story 3 (Resource Management)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test training job submission and monitoring
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Add User Story 4 & 5 → Test independently → Deploy/Demo
6. Add Monitoring & Model Management → Final release

### Parallel Team Strategy

With 3+ developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (Training Jobs)
   - Developer B: User Story 2 (Datasets)
   - Developer C: User Story 3 (Resource Management)
3. After P1 stories complete:
   - Developer A: User Story 4 (Cost Analysis)
   - Developer B: User Story 5 (Dev Environments)
   - Developer C: Monitoring & Model Management
4. Final phase: All developers on Polish & Integration

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any 关卡 to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
