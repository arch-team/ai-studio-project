## EVAL: us1-checkpoints
Created: 2026-02-20
Last Check: 2026-02-20 (post-fix)
Module: backend/src/modules/training/application/services/checkpoint_*.py
Phase: 3 (P1 Must-Have)
Tasks: T038, T038b-1, T038b-2

### Capability Evals

#### 检查点创建 (T038)
- [x] 定期自动创建: 每 10-15 分钟为 Running 状态任务自动创建检查点
- [x] 训练中断触发: Pods 异常终止时立即触发检查点创建
- [x] 节点故障触发: PodsReady=False 持续 >30 秒时触发检查点创建
- [x] 资源抢占触发: Kueue Evicted condition 时在 5 分钟内完成检查点保存
- [x] 用户手动触发: API 调用 create_checkpoint(job_id, trigger_type) 成功创建
- [x] 检查点元数据正确记录 (创建时间、序号、存储路径、SHA-256 校验和)
- [x] 检查点优先保存到 NVMe 本地存储，不可用时保存到 FSx

#### 分层迁移 (T038b-1)
- [x] 热检查点: 最近 3 个检查点保留在 NVMe 本地存储
- [x] 温检查点: 第 4-10 个检查点自动迁移到 FSx for Lustre
- [x] 冷检查点: 序号 >10 或 >72 小时的检查点归档到 S3
- [x] 异步迁移在检查点间隔期执行，不影响训练性能
- [x] NVMe/FSx 使用率 >90% 时触发紧急迁移至下一层
- [x] 所有层均满载时告警并暂停新检查点创建 (保留最近 1 个)
- [x] 迁移失败时保留原位置检查点，最多重试 3 次 (指数退避 1s→2s→4s)
- [x] SHA-256 校验和验证: 恢复前验证完整性，损坏时自动尝试上一个有效检查点

#### S3 生命周期 (T038b-2)
- [x] S3 Lifecycle Rule: 30 天后自动转换为 Standard-IA
- [x] S3 Lifecycle Rule: 90 天后自动删除冷检查点 (仅 checkpoint_type=cold 标签)
- [x] CDK 参数 checkpoint_retention_days 和 checkpoint_ia_transition_days 可配置

#### 抢占时序 SLA (T038c)
- [x] 低优先级任务被高优先级任务抢占时 checkpoint 在 5 分钟内保存完成
- [x] 被抢占任务的 Pod 在 30 秒内被释放
- [x] 任务状态正确转换为 Preempted
- [x] 抢占超时控制: asyncio.wait_for(timeout=300s)

### Regression Evals
- [x] 检查点创建不影响训练任务性能 (GPU 利用率下降 <5%)
- [x] 分层迁移服务不影响正在运行的训练任务
- [x] S3 生命周期规则不误删热/温检查点
- [x] 迁移失败告警 recipient_ids 从配置读取 (空时记录 warning)

### Success Criteria
- pass@3 > 90% for capability evals
- pass^3 = 100% for regression evals
- SC-002: 检查点保存成功率 >99%
