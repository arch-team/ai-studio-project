---

description: "Task list template for feature implementation"
---

# Tasks: [FEATURE NAME]

**Input**: Design documents from `/specs/[###-feature-name]/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are MANDATORY for production features (per Constitution Principle IX: Test Strategy and Quality Assurance). Only skip tests for proof-of-concept or experimental features explicitly marked as non-production.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

<!-- 
  ============================================================================
  IMPORTANT: The tasks below are SAMPLE TASKS for illustration purposes only.
  
  The /speckit.tasks command MUST replace these with actual tasks based on:
  - User stories from spec.md (with their priorities P1, P2, P3...)
  - Feature requirements from plan.md
  - Entities from data-model.md
  - Endpoints from contracts/
  
  Tasks MUST be organized by user story so each story can be:
  - Implemented independently
  - Tested independently
  - Delivered as an MVP increment
  
  DO NOT keep these sample tasks in the generated tasks.md file.
  ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per implementation plan
- [ ] T002 Initialize [language] project with [framework] dependencies
- [ ] T003 [P] Configure linting and formatting tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### SDK Integration Tasks (per Constitution Principle I.B)

- [ ] T004 Install and configure `sagemaker-hyperpod` Python SDK
- [ ] T005 Establish cluster connection via SDK cluster API
- [ ] T006 Verify SDK training API supports required training workflows
- [ ] T007 Verify SDK inference API supports required deployment patterns
- [ ] T008 Setup SDK authentication (IAM roles, service accounts)

**SDK Verification Checkpoint**: Confirm SDK supports all required HyperPod interactions

### Clean Architecture Setup (per Constitution Principle XII)

**适用范围**: 以下任务 **仅适用于后端项目 (backend/)**。前端和基础设施项目不适用。

- [ ] T009 Create four-layer directory structure (backend/ only):
  - `backend/src/domain/` (entities, value_objects, exceptions, repositories)
  - `backend/src/application/` (services, dto, interfaces)
  - `backend/src/infrastructure/` (persistence, external, config)
  - `backend/src/api/` (v1/endpoints, v1/schemas, v1/dependencies, middleware)
- [ ] T010 [P] Setup dependency injection framework (FastAPI dependencies or dependency-injector)
- [ ] T011 [P] Create base domain exceptions in `backend/src/domain/exceptions/`
- [ ] T012 [P] Setup infrastructure config management in `backend/src/infrastructure/config/`
- [ ] T013 Create repository interface base class in `backend/src/domain/repositories/base.py`
- [ ] T014 Setup SQLAlchemy async session factory in `backend/src/infrastructure/persistence/`
- [ ] T015 [P] Configure Alembic migrations in `backend/src/infrastructure/persistence/migrations/`

**不适用范围**:
- **前端项目 (frontend/)**: 采用 React 组件化架构 (pages/, components/, hooks/, store/)
- **基础设施项目 (infrastructure/cdk/)**: 采用 AWS CDK Construct/Stack 模式

### Core Infrastructure Tasks

- [ ] T016 [P] Implement authentication/authorization in `src/api/middleware/`
- [ ] T017 [P] Setup API routing in `src/api/v1/router.py`
- [ ] T018 Configure error handling and logging in `src/core/`
- [ ] T019 Setup environment configuration in `src/infrastructure/config/settings.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - [Title] (Priority: P1) 🎯 MVP

**Goal**: [Brief description of what this story delivers]

**Independent Test**: [How to verify this story works on its own]

### Tests for User Story 1 (MANDATORY for production features) ✅

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation (TDD approach per Constitution Principle IX)**

- [ ] T020 [P] [US1] Unit test for domain entity in tests/unit/domain/test_[entity].py
- [ ] T021 [P] [US1] Unit test for application service in tests/unit/application/test_[service].py
- [ ] T022 [P] [US1] Contract test for [endpoint] in tests/contract/test_[name].py
- [ ] T023 [P] [US1] Integration test for [user journey] in tests/integration/test_[name].py

### Domain Layer Tasks (per Constitution Principle XII)

- [ ] T024 [P] [US1] Create [Entity] in src/domain/entities/[entity].py
- [ ] T025 [P] [US1] Create [ValueObject] in src/domain/value_objects/[vo].py
- [ ] T026 [P] [US1] Create repository interface in src/domain/repositories/[entity]_repository.py
- [ ] T027 [P] [US1] Create domain exception in src/domain/exceptions/[entity]_exceptions.py

### Application Layer Tasks

- [ ] T028 [US1] Create DTO in src/application/dto/[entity]_dto.py (depends on T024, T025)
- [ ] T029 [US1] Implement [Service] in src/application/services/[entity]_service.py

### Infrastructure Layer Tasks

- [ ] T030 [P] [US1] Create SQLAlchemy model in src/infrastructure/persistence/models/[entity].py
- [ ] T031 [US1] Implement repository in src/infrastructure/persistence/repositories/[entity]_repository.py (depends on T026, T030)

### API Layer Tasks

- [ ] T032 [P] [US1] Create Pydantic schemas in src/api/v1/schemas/[entity].py
- [ ] T033 [US1] Implement endpoint in src/api/v1/endpoints/[entity].py (depends on T029, T032)
- [ ] T034 [US1] Register endpoint router in src/api/v1/router.py
- [ ] T035 [US1] Setup dependency injection for [Service] in src/api/v1/dependencies/

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - [Title] (Priority: P2)

**Goal**: [Brief description of what this story delivers]

**Independent Test**: [How to verify this story works on its own]

### Tests for User Story 2 (MANDATORY for production features) ✅

- [ ] T018 [P] [US2] Contract test for [endpoint] in tests/contract/test_[name].py
- [ ] T019 [P] [US2] Integration test for [user journey] in tests/integration/test_[name].py

### Implementation for User Story 2

- [ ] T020 [P] [US2] Create [Entity] model in src/models/[entity].py
- [ ] T021 [US2] Implement [Service] in src/services/[service].py
- [ ] T022 [US2] Implement [endpoint/feature] in src/[location]/[file].py
- [ ] T023 [US2] Integrate with User Story 1 components (if needed)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - [Title] (Priority: P3)

**Goal**: [Brief description of what this story delivers]

**Independent Test**: [How to verify this story works on its own]

### Tests for User Story 3 (MANDATORY for production features) ✅

- [ ] T024 [P] [US3] Contract test for [endpoint] in tests/contract/test_[name].py
- [ ] T025 [P] [US3] Integration test for [user journey] in tests/integration/test_[name].py

### Implementation for User Story 3

- [ ] T026 [P] [US3] Create [Entity] model in src/models/[entity].py
- [ ] T027 [US3] Implement [Service] in src/services/[service].py
- [ ] T028 [US3] Implement [endpoint/feature] in src/[location]/[file].py

**Checkpoint**: All user stories should now be independently functional

---

[Add more user story phases as needed, following the same pattern]

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] TXXX [P] Documentation updates in docs/
- [ ] TXXX Code cleanup and refactoring
- [ ] TXXX Performance optimization across all stories
- [ ] TXXX [P] Additional unit tests (if requested) in tests/unit/
- [ ] TXXX Security hardening
- [ ] TXXX Run quickstart.md validation

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for [endpoint] in tests/contract/test_[name].py"
Task: "Integration test for [user journey] in tests/integration/test_[name].py"

# Launch all models for User Story 1 together:
Task: "Create [Entity1] model in src/models/[entity1].py"
Task: "Create [Entity2] model in src/models/[entity2].py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1
   - Developer B: User Story 2
   - Developer C: User Story 3
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
