# 训练管理模块 E2E 全面回归验证实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 对 dev 环境训练管理模块执行 57 用例分层回归（50 Mock + 7 真实集群），修复失败项、加固已知抖动用例，最终全量通过且集群环境恢复干净。

**Architecture:** 分层串行回归——预检环境基线 → Mock 层（前端/契约问题）→ 真实层（链路/集群问题）→ 条件性修复 → 抖动加固 → 终验。所有测试通过 `E2E_BASE_URL` 指向已部署的 dev ALB 运行（Mock 测试登录走真实 API，业务接口由 Playwright `page.route` 拦截；真实冒烟测试无任何 Mock）。

**Tech Stack:** Playwright（frontend/e2e/）、kubectl（EKS dev 集群）、curl + Python（API 预检）。

**Spec:** `docs/superpowers/specs/2026-06-12-training-management-e2e-regression-design.md`

---

## 关键环境信息（执行者必读）

| 项 | 值 |
|----|----|
| 平台入口 | `http://ai-platform-dev-alb-1343863355.us-east-1.elb.amazonaws.com` |
| 前端项目目录 | `frontend/`（所有 npx/npm 命令在此目录执行） |
| kubectl 上下文 | `arn:aws:eks:us-east-1:897473508751:cluster/ai-platform-dev-eks` |
| 测试登录凭据 | `admin` / `Admin123!`（e2e/utils/auth.ts 默认值） |
| 当前部署版本 | backend v1.2.20 / frontend v1.0.15 |
| K8s 清单目录 | `infrastructure/k8s/base/application/` |
| 历史遗留 CR | `default/test-training-job-001`（138 天前，非本轮产物，**不要动它**） |

**种子任务基线**（预检与终验一致性标准）：

| ID | job_name | 期望状态 |
|----|----------|---------|
| 1 | llama2-finetune-001 | completed |
| 2 | sd-finetune-001 | completed |
| 3 | bert-pretrain-001 | running |

**测试诚信红线**：禁止跳过/注释失败测试，禁止伪造结果。测试失败 = 必须根因分析。

---

### Task 1: 预检——平台健康与环境基线

**Files:** 无文件改动（只读检查）

- [ ] **Step 1: 平台健康检查**

```bash
curl -s -o /dev/null -w "%{http_code}\n" --max-time 10 http://ai-platform-dev-alb-1343863355.us-east-1.elb.amazonaws.com/
```

预期输出：`200`

- [ ] **Step 2: 登录并核对种子任务基线**

```bash
TOKEN=$(curl -s -X POST http://ai-platform-dev-alb-1343863355.us-east-1.elb.amazonaws.com/api/v1/auth/login \
  -H "Content-Type: application/json" -d '{"username":"admin","password":"Admin123!"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['tokens']['access_token'])")
curl -s "http://ai-platform-dev-alb-1343863355.us-east-1.elb.amazonaws.com/api/v1/training-jobs?page=1&page_size=20" \
  -H "Authorization: Bearer $TOKEN" | python3 -c "
import sys, json
d = json.load(sys.stdin)
for j in sorted(d['items'], key=lambda x: x['id']):
    print(j['id'], j['job_name'], j['status'])
print('total:', d['total'])"
```

预期输出（必须逐行匹配）：

```
1 llama2-finetune-001 completed
2 sd-finetune-001 completed
3 bert-pretrain-001 running
total: 3
```

若 `bert-pretrain-001` 不是 `running`（例如上轮遗留 `paused`）：调用 `POST /api/v1/training-jobs/3/resume`（带同样的 Authorization 头）恢复后重查。若出现多余任务（total > 3）：先确认是 `e2e-smoke-*` 命名的测试遗留，是则调用 `DELETE /api/v1/training-jobs/{id}` 清理；否则停下来向用户报告。

- [ ] **Step 3: 记录集群 CR 基线**

```bash
kubectl --context arn:aws:eks:us-east-1:897473508751:cluster/ai-platform-dev-eks \
  get hyperpodpytorchjobs -A
```

预期输出：仅 `default/test-training-job-001`（历史遗留）。如出现其他 CR（如 `bert-pretrain-001`），说明上轮清理不彻底——记录下来，在 Task 6 终验时以"恢复到本步骤记录的集合"为准；若存在 `bert-pretrain-001` 之类明显与种子任务同名的 CR 且其 DB 状态为 running，这是正常的运行中任务载体，保留。

- [ ] **Step 4: 确认前端依赖就绪**

```bash
cd frontend && npx playwright --version
```

预期输出：`Version 1.x`。若报错则 `npm install` 后重试。

---

### Task 2: Mock 层回归（50 用例）

**Files:** 无文件改动（运行测试）

- [ ] **Step 1: 串行运行 3 个 Mock 套件**

```bash
cd frontend && E2E_BASE_URL=http://ai-platform-dev-alb-1343863355.us-east-1.elb.amazonaws.com \
  npx playwright test e2e/tests/training-jobs.spec.ts e2e/tests/training-jobs-crud.spec.ts \
  e2e/tests/training-jobs-operations.spec.ts --workers=1 --reporter=list
```

预期：`50 passed`（约 5-10 分钟）。

- [ ] **Step 2: 记录失败清单（如有）**

若有失败：保存完整失败输出（用例名、错误消息、失败断言位置），逐个归类——前端 Bug / 契约不匹配 / 测试自身问题 / 环境抖动。失败项进入 Task 4 处理；**Mock 层失败先不修，先跑完 Task 3 收集全量失败清单**（避免修复打断回归基线）。已知抖动用例（`状态 "failed" - 暂停:false, 恢复:false, 删除禁用:false`）失败时先单独重跑一次：

```bash
cd frontend && E2E_BASE_URL=http://ai-platform-dev-alb-1343863355.us-east-1.elb.amazonaws.com \
  npx playwright test e2e/tests/training-jobs-operations.spec.ts -g '状态 "failed"' --workers=1 --reporter=list
```

重跑通过 → 标记为"抖动复现，Task 5 加固解决"；重跑仍失败 → 按真实 Bug 进 Task 4。

---

### Task 3: 真实层回归（7 用例）

**Files:** 无文件改动（运行测试）

> 此套件在真实集群创建/删除 HyperPod CR（暂停→恢复闭环、创建→删除闭环），测试自带清理逻辑。

- [ ] **Step 1: 运行真实冒烟套件**

```bash
cd frontend && E2E_BASE_URL=http://ai-platform-dev-alb-1343863355.us-east-1.elb.amazonaws.com \
  npx playwright test e2e/tests/training-real-smoke.spec.ts --workers=1 --reporter=list
```

预期：`7 passed`（约 3-5 分钟）。

- [ ] **Step 2: 测试后立即核对环境**

重复 Task 1 Step 2 和 Step 3 的命令。预期：种子基线复原（bert-pretrain-001 回到 running）、无新增 CR、无 `e2e-smoke-*` 任务残留。若真实层测试中途失败导致状态未复原（如暂停后未恢复），手工修复：

```bash
# bert 停在 paused 时恢复（TOKEN 获取方式同 Task 1）
curl -s -X POST "http://ai-platform-dev-alb-1343863355.us-east-1.elb.amazonaws.com/api/v1/training-jobs/3/resume" \
  -H "Authorization: Bearer $TOKEN"
# e2e-smoke-* 残留任务删除
curl -s -X DELETE "http://ai-platform-dev-alb-1343863355.us-east-1.elb.amazonaws.com/api/v1/training-jobs/{残留ID}" \
  -H "Authorization: Bearer $TOKEN"
```

- [ ] **Step 3: 汇总全量失败清单**

合并 Task 2 与 Task 3 的失败项。若为空 → 跳过 Task 4，直接进 Task 5。

---

### Task 4: 条件性修复循环（仅当 Task 2/3 有失败）

**Files:** 视失败根因而定；以下为流程模板

> 对每个失败项独立执行此循环。修复遵循 TDD：先写失败测试复现根因，再修代码。

- [ ] **Step 1: 根因分析**

用失败输出 + 浏览器截图（`frontend/test-results/` 下自动保存）+ 后端日志定位：

```bash
# 后端日志（如怀疑 API 问题）
kubectl --context arn:aws:eks:us-east-1:897473508751:cluster/ai-platform-dev-eks \
  logs -n ai-platform deploy/backend --tail=100 | grep -i "error\|exception"
# 直接 curl 复现 API 行为（TOKEN 同 Task 1）
curl -s -i "http://ai-platform-dev-alb-1343863355.us-east-1.elb.amazonaws.com/api/v1/training-jobs/3/pause" \
  -X POST -H "Authorization: Bearer $TOKEN"
```

- [ ] **Step 2: 写失败的单元测试复现根因**

后端测试放 `backend/tests/unit/{module}/`，前端放 `frontend/tests/unit/`。运行确认失败：

```bash
# 后端
cd backend && pytest tests/unit/training/ -k "新测试名" -v
# 前端
cd frontend && npm test -- tests/unit/features/training --run
```

- [ ] **Step 3: 最小实现使测试通过，跑质量门禁**

```bash
# 后端门禁
cd backend && black src/ tests/ && ruff check src/ tests/ && pytest tests/unit -q
# 前端门禁
cd frontend && npm run lint && npm test -- --run
```

预期：全绿。

- [ ] **Step 4: 部署（仅当改了后端/前端运行代码）**

ECR tag 不可变，版本号必须递增（下一可用：backend v1.2.21 / frontend v1.0.16）：

```bash
# 查当前镜像仓库地址
grep -rn "image:" infrastructure/k8s/base/application/ | grep -i "backend\|frontend"
# 构建推送（以后端为例，仓库地址以上一命令输出为准）
cd backend && docker build --platform linux/amd64 -t {ECR_REPO}:v1.2.21 .
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin {ECR_REGISTRY}
docker push {ECR_REPO}:v1.2.21
# 更新清单并滚动部署
# （编辑 infrastructure/k8s/base/application/ 中对应 deployment 的 image tag）
kubectl --context arn:aws:eks:us-east-1:897473508751:cluster/ai-platform-dev-eks \
  apply -k infrastructure/k8s/base/application/
kubectl --context arn:aws:eks:us-east-1:897473508751:cluster/ai-platform-dev-eks \
  rollout status -n ai-platform deploy/backend --timeout=300s
```

- [ ] **Step 5: 真实环境复验**

重跑失败的那个 E2E 用例（`-g "用例名"`），预期通过。

- [ ] **Step 6: 提交**

```bash
git add {改动文件} && git commit -m "fix({scope}): {根因简述}"
```

---

### Task 5: 抖动用例加固

**Files:**
- Modify: `frontend/e2e/tests/training-jobs-operations.spec.ts:314-326`（状态按钮可见性矩阵）

> 已知抖动：`状态 "failed"` 用例在全量串行跑时偶发失败，单独重跑稳定。根因：共享环境慢响应时，`waitForContentLoad()` 只等 `h1` 可见，详情数据可能尚未渲染完成，按钮断言与数据加载存在竞态。加固方式：按钮断言前先等待状态标签文本渲染（证明详情查询已完成）。

- [ ] **Step 1: 修改测试增加状态标签等待**

在 `for` 循环内 `await detailPage.waitForContentLoad();` 之后、`// 检查暂停按钮` 之前插入：

```typescript
        // 加固：等待状态标签渲染，确保详情数据已加载完成再断言按钮
        // （共享环境慢响应时 h1 可见不代表详情查询已完成，曾导致 failed 用例偶发抖动）
        const STATUS_LABELS: Record<string, string> = {
          submitted: '已提交',
          running: '运行中',
          paused: '已暂停',
          preempted: '被抢占',
          completed: '已完成',
          failed: '已失败',
        };
        await expect(page.getByText(STATUS_LABELS[status]).first()).toBeVisible({
          timeout: 10000,
        });
```

- [ ] **Step 2: 运行该文件全量验证**

```bash
cd frontend && E2E_BASE_URL=http://ai-platform-dev-alb-1343863355.us-east-1.elb.amazonaws.com \
  npx playwright test e2e/tests/training-jobs-operations.spec.ts --workers=1 --reporter=list
```

预期：`21 passed`。

- [ ] **Step 3: Lint 检查**

```bash
cd frontend && npm run lint
```

预期：0 错误 0 警告。

- [ ] **Step 4: 提交**

```bash
git add frontend/e2e/tests/training-jobs-operations.spec.ts
git commit -m "test(frontend): 加固状态按钮矩阵用例——按钮断言前等待状态标签渲染"
```

---

### Task 6: 终验——全量 57 用例 + 环境恢复

**Files:** 无文件改动（运行测试 + 环境核对）

- [ ] **Step 1: 全量串行运行 4 个套件**

```bash
cd frontend && E2E_BASE_URL=http://ai-platform-dev-alb-1343863355.us-east-1.elb.amazonaws.com \
  npx playwright test e2e/tests/training-jobs.spec.ts e2e/tests/training-jobs-crud.spec.ts \
  e2e/tests/training-jobs-operations.spec.ts e2e/tests/training-real-smoke.spec.ts \
  --workers=1 --reporter=list
```

预期：`57 passed`。

判定规则（与 spec 验收标准一致）：
- 非抖动用例失败 → 回 Task 4 修复后重新终验
- 仅"状态按钮矩阵"类已加固抖动用例失败 → 单独重跑该用例（`-g`），连续 2 次稳定通过即达标，并在最终报告中如实记录

- [ ] **Step 2: 环境恢复核对**

重复 Task 1 Step 2（种子基线三行 + total: 3）与 Step 3（CR 集合与预检基线一致）。预期完全一致；不一致则按 Task 3 Step 2 的手工修复命令处理后复查。

- [ ] **Step 3: 最终提交与报告**

```bash
git status --short   # 确认无本轮遗漏的未提交改动（backend/tests 下既有脏文件与本轮无关，不要动）
git log --oneline -5
```

向用户输出最终报告：57 用例结果、失败修复明细（如有）、抖动处理记录、环境恢复核对结果。

---

## 任务依赖

```
Task 1（预检）→ Task 2（Mock 层）→ Task 3（真实层）→ Task 4（条件修复）→ Task 5（加固）→ Task 6（终验）
```

Task 4 仅在 Task 2/3 有失败时执行；多个失败项按"后端→前端→测试自身"顺序逐个修复，每项独立 commit。
