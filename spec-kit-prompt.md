## Phase 3: US1 (P1) - 训练任务管理 (33 tasks)

/speckit.implement ## Phase 3: US1 (P1) - 训练任务管理 (33 tasks) 中的后端 API 端点 (基于 contracts/training-jobs-api.yaml), 每个任务按照TDD（测试驱动开发的流程进行），完成后将相应的任务标记为完成状态
/speckit.implement ## Phase 3: US1 (P1) - 训练任务管理 (33 tasks) 中的HyperPod 集成服务(T037，T037d，T037c，T037e), 每个任务按照TDD（测试驱动开发的流程进行），完成后将tasks.md中已经明确完成的任务标记为完成状态


/speckit.implement ## Phase 3: US1 (P1) - 训练任务管理 (33 tasks) 中的### 集成测试这个子阶段, 每个任务按照TDD（测试驱动开发的流程进行），完成后将tasks.md中已经明确完成的任务标记为完成状态

/speckit.implement ## Phase 4: US2 (P1) - 数据集管理 (14 tasks) 中的### QLAlchemy 模型这个子阶段, 每个任务按照TDD（测试驱动开发的流程进行），完成后将tasks.md中已经明确完成的任务标记为完成状态



/speckit.implement ## Phase 5: US3 (P1) - 资源配额和集群监控 (21 tasks) 的数据表迁移 和 SQLAlchemy 模型这个子阶段, 每个任务按照TDD（测试驱动开发的流程进行），完成后将tasks.md中已经明确完成的任务标记为完成状态

/speckit.implement ## Phase 5: US3 (P1) - 资源配额和集群监控 (21 tasks) 的后端 API 端点 (基于 contracts/users-api.yaml, resource-quotas-api.yaml, monitoring-api.yaml)这个子阶段, 每个任务按照TDD（测试驱动开发的流程进行），完成后将tasks.md中已经明确完成的任务标记为完成状态




/speckit.implement ## Phase 3: US1 (P1) - 训练任务管理 (33 tasks) 中的集成测试这个子阶段, 中的
- SC-001: 支持 PyTorch DDP/FSDP/DeepSpeed ZeRO
- SC-002: 检查点保存成功率 >99%
这两个集成测试是否完成
每个任务按照TDD（测试驱动开发的流程进行），完成后将tasks.md中已经明确完成的任务标记为完成状态



/everything-claude-code:eval 对这个文件中的 'US1 (P1) - 训练任务管理 (37 tasks)'下的 ‘### 后端 API 端点 (基于 contracts/training-jobs-api.yaml)
’ 制定评估/Users/jinhuasu/Project_Workspace/Anker-Projects/ml-platform-research/llm-platform-solution/ai-studio-project/specs/001-ai-training-platform/tasks.md  


/everything-claude-code:eval 对这个文件中的 'US1 (P1) - 训练任务管理 (37 tasks)'下的 
‘
### 集成测试
- [] [T038c] [US1] 抢占时序SLA集成测试 - `backend/tests/integration/training/test_preemption_timing.py`,验证 FR-004 抢占时序保证:
  - **测试场景 1**: 触发低优先级任务被高优先级任务抢占 (使用 Kueue Priority 配置)
  - **测试场景 2**: 验证 checkpoint 在抢占触发后 5 分钟内保存完成 (监控 T038 的场景 4 触发时间戳)
  - **测试场景 3**: 验证被抢占任务的 Pod 在 30 秒内被释放 (调用 Kubernetes API 查询 Pod 状态)
  - **测试场景 4**: 验证任务状态正确转换为 Preempted (调用 T029 状态同步逻辑验证)
  - **测试场景 5**: 验证抢占后自动恢复成功 (checkpoint 恢复 + 训练继续)
  - **测试工具**: 使用 pytest + HyperPod SDK + Kubernetes Python Client
  - **估算**: 6h (SHOULD, Integration Test)
  - **依赖**: T022 (checkpoints 表), T024 (Checkpoint 模型), T029 (状态同步), T038 (checkpoint 自动保存逻辑)
  - **参考**: spec.md FR-004 抢占式调度时序要求
‘制定评估
参考文件：/Users/jinhuasu/Project_Workspace/Anker-Projects/ml-platform-research/llm-platform-solution/ai-studio-project/specs/001-ai-training-platform/tasks.md  


/speckit.implement Phase 4: US2 (P1) - 数据集管理 (14 tasks)的数据表迁移、SQLAlchemy 模型、后端 API 端点 (基于 contracts/datasets-api.yaml)这些子阶段, 

每个任务按照TDD（测试驱动开发的流程进行），完成后将tasks.md中已经明确完成的任务标记为完成状态
