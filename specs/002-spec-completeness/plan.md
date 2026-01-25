# Implementation Plan: [FEATURE]

**Branch**: `[###-feature-name]` | **Date**: [DATE] | **Spec**: [link]
**Input**: Feature specification from `/specs/[###-feature-name]/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

[Extract from feature spec: primary requirement + technical approach from research]

## Technical Context

<!--
  ACTION REQUIRED: Replace the content in this section with the technical details
  for the project. The structure here is presented in advisory capacity to guide
  the iteration process.
-->

**Language/Version**: [e.g., Python 3.11, Swift 5.9, Rust 1.75 or NEEDS CLARIFICATION]  
**Primary Dependencies**: [e.g., FastAPI, UIKit, LLVM or NEEDS CLARIFICATION]  
**Storage**: [if applicable, e.g., PostgreSQL, CoreData, files or N/A]  
**Testing**: [e.g., pytest, XCTest, cargo test or NEEDS CLARIFICATION]  
**Target Platform**: [e.g., Linux server, iOS 15+, WASM or NEEDS CLARIFICATION]
**Project Type**: [single/web/mobile - determines source structure]  
**Performance Goals**: [domain-specific, e.g., 1000 req/s, 10k lines/sec, 60 fps or NEEDS CLARIFICATION]  
**Constraints**: [domain-specific, e.g., <200ms p95, <100MB memory, offline-capable or NEEDS CLARIFICATION]  
**Scale/Scope**: [domain-specific, e.g., 10k users, 1M LOC, 50 screens or NEEDS CLARIFICATION]

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### HyperPod Native-First (Principle I)
- [ ] All HyperPod interactions use `sagemaker-hyperpod` Python SDK
- [ ] Training tasks submitted via SDK training API, not raw K8S
- [ ] Inference deployment via SDK inference API, not custom operators
- [ ] Development spaces managed via SDK Spaces API
- [ ] Cluster management via SDK cluster API

**If using raw K8S API directly**: Document justification and get governance approval

### SDK-First Development (Principle I.B)
- [ ] Verified `sagemaker-hyperpod` SDK supports required functionality
- [ ] SDK documentation reviewed for target features
- [ ] Any SDK bypasses documented with clear technical rationale
- [ ] Platform API design aligns with SDK abstraction levels

**If SDK does not support needed functionality**: Document specific gaps and alternative approach

### HyperPod-Enhanced Capabilities First (Principle II)
- [ ] Component selection prioritizes HyperPod扩展能力:
  - **首选**: HyperPod托管组件和扩展能力 (Training/Inference Operators, Task Governance, Observability, Spaces)
  - **次选**: 开源 K8S 组件 (仅在 HyperPod 不提供对应功能时)
  - **避免**: 自行实现 HyperPod 已提供的功能
- [ ] 充分利用 HyperPod 特有扩展 (Checkpointless Training, Elastic Agent, Deep Health Checks)
- [ ] 不要求工作负载可在标准 K8S 集群运行 (HyperPod 锁定策略)
- [ ] MAY 使用 kubectl/Helm 工具 (但主要通过 HyperPod SDK 和控制台管理)

**If not using HyperPod components**: Justify why HyperPod扩展能力不足以满足需求

### Code Design and Implementation Quality (Principle X)
- [ ] Architecture follows SOLID principles (SRP, OCP, LSP, ISP, DIP)
- [ ] Design adheres to DRY, KISS, YAGNI principles
- [ ] Component selection prioritizes mature SDKs and libraries:
  - **Python**: FastAPI, SQLAlchemy, Pydantic, pytest over custom implementations
  - **Frontend**: React, TypeScript, Zustand, TanStack Query over custom frameworks
  - **HyperPod**: `sagemaker-hyperpod` SDK over raw K8S API (per Principle I.B)
- [ ] Clean Code practices planned:
  - Clear naming conventions
  - Functions <50 lines, parameters ≤3
  - Self-documenting code with minimal comments
  - Exception-based error handling
- [ ] Code review standards defined (SOLID compliance, test coverage per Principle IX)
- [ ] Technical debt management strategy established

**If implementing custom solutions**: Document why existing mature libraries are insufficient

### UI/UX Consistency (Principle XI)
- [ ] UI design aligns with AWS Console design language and patterns
- [ ] MUST use AWS Cloudscape Design System (`@cloudscape-design/components`)
- [ ] Visual consistency verified:
  - Cloudscape color system, Amazon Ember font
  - Official Cloudscape icons only
  - Cloudscape spacing and grid system
- [ ] Interaction consistency planned:
  - AWS Console standard operation patterns
  - Cloudscape feedback components (Flash, StatusIndicator)
  - AWS Console navigation patterns (AppLayout, BreadcrumbGroup)
- [ ] Terminology consistency:
  - Use AWS official terms (e.g., "Training Job" not "Job/Task")
  - Follow AWS naming conventions
  - Create terminology dictionary mapping to AWS terms
- [ ] Accessibility requirements:
  - WCAG 2.1 AA compliance
  - Keyboard navigation support
  - Proper ARIA labels
- [ ] Reference AWS SageMaker Console and AWS EKS Console for design patterns

**If not using Cloudscape**: NOT ALLOWED - UI component library has no exceptions

### Clean Architecture (Principle XII)

**适用范围**: 本检查项 **仅适用于后端项目 (backend/)**。前端和基础设施项目不适用此检查。

- [ ] **适用范围确认**: 此功能涉及后端代码 (backend/) → 需遵循 Clean Architecture
- [ ] Backend code follows four-layer architecture:
  - **domain**: Entities, Value Objects, Repository interfaces, Exceptions
  - **application**: Services, DTOs, Port interfaces
  - **infrastructure**: Persistence (SQLAlchemy), External adapters (HyperPod SDK, S3, MLflow)
  - **api**: FastAPI endpoints, Pydantic schemas, Dependencies, Middleware
- [ ] Dependency rules verified:
  - domain layer has NO imports from application/infrastructure/api
  - application layer has NO imports from infrastructure/api
  - infrastructure implements domain/application interfaces
  - api depends only on application layer
- [ ] Repository pattern implemented:
  - Interfaces defined in domain/repositories/
  - Implementations in infrastructure/persistence/repositories/
- [ ] Dependency injection configured:
  - Services receive dependencies via constructor
  - FastAPI dependencies or DI container used
  - No direct instantiation of infrastructure in application/domain
- [ ] Test isolation planned:
  - Domain layer testable without external dependencies
  - Application layer tests use mock repositories
  - Integration tests use real infrastructure

**不适用范围**:
- **前端项目 (frontend/)**: 采用 React 组件化架构,遵循 Cloudscape Design System
- **基础设施项目 (infrastructure/cdk/)**: 采用 AWS CDK Construct/Stack 模式

**If violating dependency rules**: Document justification and get governance approval

[Additional gates determined based on constitution file]

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)
<!--
  ACTION REQUIRED: Replace the placeholder tree below with the concrete layout
  for this feature. Delete unused options and expand the chosen structure with
  real paths (e.g., apps/admin, packages/something). The delivered plan must
  not include Option labels.
-->

```text
# [REMOVE IF UNUSED] Option 1: Single project (DEFAULT)
src/
├── models/
├── services/
├── cli/
└── lib/

tests/
├── contract/
├── integration/
└── unit/

# [REMOVE IF UNUSED] Option 2: Web application (when "frontend" + "backend" detected)
backend/
├── src/
│   ├── models/
│   ├── services/
│   └── api/
└── tests/

frontend/
├── src/
│   ├── components/
│   ├── pages/
│   └── services/
└── tests/

# [REMOVE IF UNUSED] Option 3: Mobile + API (when "iOS/Android" detected)
api/
└── [same as backend above]

ios/ or android/
└── [platform-specific structure: feature modules, UI flows, platform tests]
```

**Structure Decision**: [Document the selected structure and reference the real
directories captured above]

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
