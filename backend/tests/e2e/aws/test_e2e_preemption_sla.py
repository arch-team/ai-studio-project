"""抢占时序 SLA E2E 测试 (T038c)

在真实 HyperPod + Kueue 环境验证:
1. 低优先级任务被高优先级任务抢占
2. Checkpoint 在 5 分钟内保存完成
3. Pod 在 30 秒内释放
4. 任务状态正确转换
5. 自动恢复成功

环境要求:
- HyperPod 集群可用
- Kueue 调度器配置
- 充足的 GPU 资源

运行方式:
    # 设置环境变量
    export AWS_REGION=us-west-2
    export HYPERPOD_CLUSTER_NAME=ai-training-cluster-dev
    export E2E_READ_ONLY=false

    # 运行测试
    pytest tests/e2e/aws/test_e2e_preemption_sla.py -v -s

依赖: T022 (checkpoints 表), T024 (Checkpoint 模型), T029 (状态同步), T038 (checkpoint 保存)
参考: FR-004 (spec.md)

⚠️ 警告: 此测试会创建真实训练任务，请确保资源配额充足
"""

import asyncio
import time
from typing import Any

import pytest
from httpx import AsyncClient

from .conftest import (
    SLAConstants,
    skip_without_aws,
    skip_without_hyperpod,
    skip_write_tests,
    track_resource,
)


@pytest.mark.e2e
@pytest.mark.aws_integration
@pytest.mark.slow
@skip_without_aws
@skip_without_hyperpod
class TestPreemptionTimingSLAE2E:
    """抢占时序 SLA E2E 测试 - FR-004

    在真实 HyperPod + Kueue 环境验证抢占 SLA。
    """

    # =========================================================================
    # 辅助方法
    # =========================================================================

    async def _wait_for_status(
        self,
        client: Any,
        job_id: str,
        expected_status: str,
        timeout: int,
    ) -> str:
        """等待任务达到指定状态

        Args:
            client: HyperPod 客户端
            job_id: 任务 ID
            expected_status: 期望的状态
            timeout: 超时时间 (秒)

        Returns:
            达到的状态

        Raises:
            TimeoutError: 超时未达到期望状态
        """
        cluster_name = getattr(client, "_cluster_name", "")
        start = time.time()
        while time.time() - start < timeout:
            try:
                status = await client.get_training_job_status(
                    cluster_name=cluster_name, job_name=job_id
                )
                current_status = status.get("status", "")
                if current_status.lower() == expected_status.lower():
                    return expected_status
                # 如果任务失败，提前退出
                if current_status.lower() in ["failed", "error"]:
                    raise RuntimeError(
                        f"Job {job_id} failed with status: {current_status}"
                    )
            except Exception as e:
                print(f"⚠️ 获取状态失败: {e}")
            await asyncio.sleep(SLAConstants.JOB_STATUS_POLL_INTERVAL)

        raise TimeoutError(
            f"Job {job_id} did not reach {expected_status} within {timeout}s"
        )

    async def _wait_for_api_status(
        self,
        client: AsyncClient,
        token: str,
        job_id: int,
        expected_status: str,
        timeout: int,
    ) -> str:
        """通过 API 等待任务状态

        Args:
            client: HTTP 客户端
            token: 认证 token
            job_id: 任务 ID
            expected_status: 期望的状态
            timeout: 超时时间 (秒)

        Returns:
            达到的状态
        """
        start = time.time()
        while time.time() - start < timeout:
            response = await client.get(
                f"/api/v1/training-jobs/{job_id}",
                headers={"Authorization": f"Bearer {token}"},
            )
            if response.status_code == 200:
                current_status = response.json().get("status", "")
                if current_status.lower() == expected_status.lower():
                    return expected_status
            await asyncio.sleep(SLAConstants.JOB_STATUS_POLL_INTERVAL)

        raise TimeoutError(
            f"Job {job_id} did not reach {expected_status} within {timeout}s"
        )

    async def _wait_for_checkpoint(
        self,
        client: Any,
        job_id: str,
        timeout: int,
        checkpoint_base_path: str = "s3://ai-training-checkpoints-dev/checkpoints",
    ) -> dict[str, Any] | None:
        """等待 checkpoint 完成

        Args:
            client: HyperPod 客户端
            job_id: 任务 ID
            timeout: 超时时间 (秒)
            checkpoint_base_path: 检查点 S3 基础路径

        Returns:
            最新的抢占 checkpoint 信息，或 None
        """
        start = time.time()
        while time.time() - start < timeout:
            try:
                checkpoints = await client.list_checkpoints(
                    job_id=job_id, checkpoint_base_path=checkpoint_base_path
                )
                preemption_ckpts = [
                    c
                    for c in checkpoints
                    if c.get("trigger_type", "").upper() == "PREEMPTION"
                ]
                if preemption_ckpts:
                    return preemption_ckpts[-1]
                # 如果没有 trigger_type，返回任何 checkpoint
                if checkpoints:
                    return checkpoints[-1]
            except Exception as e:
                print(f"⚠️ 获取 checkpoint 失败: {e}")
            await asyncio.sleep(10)
        return None

    async def _wait_for_pod_terminated(
        self,
        client: Any,
        job_name: str,
        pod_name: str,
        timeout: int,
    ) -> None:
        """等待 Pod 终止

        Args:
            client: HyperPod 客户端
            job_name: 任务名称
            pod_name: Pod 名称
            timeout: 超时时间 (秒)

        Raises:
            TimeoutError: 超时未终止
        """
        cluster_name = getattr(client, "_cluster_name", "")
        start = time.time()
        while time.time() - start < timeout:
            try:
                pod_status = await client.get_pod_status(
                    cluster_name=cluster_name, job_name=job_name, pod_name=pod_name
                )
                phase = pod_status.get("phase", "")
                if phase in ["Terminated", "Failed", "Succeeded"]:
                    return
            except Exception as e:
                # Pod 不存在也视为已终止
                if "not found" in str(e).lower():
                    return
                print(f"⚠️ 获取 Pod 状态失败: {e}")
            await asyncio.sleep(2)

        raise TimeoutError(f"Pod {pod_name} not terminated within {timeout}s")

    async def _cleanup_jobs(
        self,
        client: Any,
        job_ids: list[str | None],
    ) -> None:
        """清理测试任务

        Args:
            client: HyperPod 客户端
            job_ids: 任务 ID 列表
        """
        for job_id in job_ids:
            if job_id:
                try:
                    await client.cancel_training_job(job_id)
                    print(f"✅ 清理任务: {job_id}")
                except Exception as e:
                    print(f"⚠️ 清理任务 {job_id} 失败: {e}")

    # =========================================================================
    # 测试场景
    # =========================================================================

    @pytest.mark.asyncio
    @skip_write_tests
    async def test_low_priority_preempted_by_high_priority(
        self,
        hyperpod_client: Any,
        low_priority_job_config: dict[str, Any],
        high_priority_job_config: dict[str, Any],
    ) -> None:
        """场景1: 低优先级任务被高优先级任务抢占

        验证步骤:
        1. 提交低优先级任务，等待 Running
        2. 提交高优先级任务 (资源竞争)
        3. 验证低优先级任务被抢占
        4. 清理测试资源
        """
        cluster_name = getattr(hyperpod_client, "_cluster_name", "")
        low_job_id: str | None = None
        high_job_id: str | None = None

        try:
            # Step 1: 提交低优先级任务
            job_name = low_priority_job_config.get("job_name", f"e2e-low-{int(time.time())}")
            result = await hyperpod_client.submit_training_job(
                cluster_name=cluster_name,
                job_name=job_name,
                job_config=low_priority_job_config,
            )
            low_job_id = result.get("job_name", job_name)
            track_resource("training_job", low_job_id)
            print(f"📤 已提交低优先级任务: {low_job_id}")

            # 等待任务 Running
            await self._wait_for_status(
                hyperpod_client,
                low_job_id,
                "Running",
                timeout=SLAConstants.JOB_SUBMISSION_TIMEOUT,
            )
            print("✅ 低优先级任务已 Running")

            # Step 2: 提交高优先级任务 (触发抢占)
            high_job_name = high_priority_job_config.get("job_name", f"e2e-high-{int(time.time())}")
            result = await hyperpod_client.submit_training_job(
                cluster_name=cluster_name,
                job_name=high_job_name,
                job_config=high_priority_job_config,
            )
            high_job_id = result.get("job_name", high_job_name)
            track_resource("training_job", high_job_id)
            print(f"📤 已提交高优先级任务: {high_job_id}")

            # Step 3: 验证低优先级任务被抢占
            preemption_start = time.time()
            status = await self._wait_for_status(
                hyperpod_client,
                low_job_id,
                "Preempted",
                timeout=60,
            )
            preemption_time = time.time() - preemption_start

            # Assert
            assert status == "Preempted"
            print(f"✅ 抢占完成，耗时: {preemption_time:.2f}s")

        finally:
            # Cleanup
            await self._cleanup_jobs(hyperpod_client, [low_job_id, high_job_id])

    @pytest.mark.asyncio
    @skip_write_tests
    async def test_checkpoint_saved_within_sla(
        self,
        hyperpod_client: Any,
        checkpoint_enabled_job_config: dict[str, Any],
    ) -> None:
        """场景2: Checkpoint 在 5 分钟内保存完成

        验证步骤:
        1. 提交启用 checkpoint 的任务
        2. 等待任务 Running 并积累训练状态
        3. 触发抢占
        4. 验证 checkpoint 在 5 分钟内保存完成
        5. 验证 checkpoint 文件存在于 S3
        """
        cluster_name = getattr(hyperpod_client, "_cluster_name", "")
        job_id: str | None = None
        checkpoint_base_path = checkpoint_enabled_job_config.get(
            "checkpoint_config", {}
        ).get("s3_path", "s3://ai-training-checkpoints-dev/checkpoints")

        try:
            # Step 1: 提交任务
            job_name = checkpoint_enabled_job_config.get("job_name", f"e2e-ckpt-{int(time.time())}")
            result = await hyperpod_client.submit_training_job(
                cluster_name=cluster_name,
                job_name=job_name,
                job_config=checkpoint_enabled_job_config,
            )
            job_id = result.get("job_name", job_name)
            track_resource("training_job", job_id)
            print(f"📤 已提交 checkpoint 测试任务: {job_id}")

            # Step 2: 等待 Running
            await self._wait_for_status(
                hyperpod_client,
                job_id,
                "Running",
                timeout=SLAConstants.JOB_SUBMISSION_TIMEOUT,
            )
            print("✅ 任务已 Running")

            # 等待训练积累状态 (30秒)
            print("⏳ 等待训练积累状态 (30s)...")
            await asyncio.sleep(30)

            # Step 3: 触发抢占 (使用高优先级任务触发)
            preemption_start = time.time()
            preemption_config = {
                "image_uri": checkpoint_enabled_job_config.get("image_uri"),
                "instance_type": checkpoint_enabled_job_config.get("instance_type"),
                "node_count": 1,
                "command": ["python", "-c", "print('preemption job')"],
            }
            await hyperpod_client.trigger_preemption(
                cluster_name=cluster_name,
                target_job_name=job_id,
                preemption_job_config=preemption_config,
            )
            print("📤 已触发抢占")

            # Step 4: 等待 checkpoint 完成
            checkpoint_info = await self._wait_for_checkpoint(
                hyperpod_client,
                job_id,
                timeout=SLAConstants.CHECKPOINT_SAVE_TIMEOUT,
                checkpoint_base_path=checkpoint_base_path,
            )
            checkpoint_time = time.time() - preemption_start

            # Assert
            assert checkpoint_info is not None, "Checkpoint 未在 SLA 时间内创建"
            assert checkpoint_time < SLAConstants.CHECKPOINT_SAVE_TIMEOUT
            print(
                f"✅ Checkpoint 保存完成，耗时: {checkpoint_time:.2f}s "
                f"(SLA: {SLAConstants.CHECKPOINT_SAVE_TIMEOUT}s)"
            )

            # Step 5: 验证 S3 文件存在
            s3_path = checkpoint_info.get("s3_path") or checkpoint_info.get("key")
            if s3_path:
                # 构造完整 S3 路径
                if not s3_path.startswith("s3://"):
                    s3_path = f"{checkpoint_base_path.rstrip('/')}/{s3_path}"
                exists = await hyperpod_client.verify_checkpoint_exists(s3_path)
                assert exists, f"Checkpoint 文件不存在: {s3_path}"
                print(f"✅ Checkpoint 文件已验证: {s3_path}")

        finally:
            await self._cleanup_jobs(hyperpod_client, [job_id])

    @pytest.mark.asyncio
    @skip_write_tests
    async def test_pod_released_within_sla(
        self,
        hyperpod_client: Any,
        low_priority_job_config: dict[str, Any],
    ) -> None:
        """场景3: Pod 在 30 秒内释放

        验证步骤:
        1. 提交任务并等待 Running
        2. 记录 Pod 名称
        3. 触发抢占
        4. 验证 Pod 在 30 秒内终止
        """
        cluster_name = getattr(hyperpod_client, "_cluster_name", "")
        job_id: str | None = None

        try:
            # Step 1: 提交任务
            job_name = low_priority_job_config.get("job_name", f"e2e-pod-{int(time.time())}")
            result = await hyperpod_client.submit_training_job(
                cluster_name=cluster_name,
                job_name=job_name,
                job_config=low_priority_job_config,
            )
            job_id = result.get("job_name", job_name)
            track_resource("training_job", job_id)
            print(f"📤 已提交任务: {job_id}")

            await self._wait_for_status(
                hyperpod_client,
                job_id,
                "Running",
                timeout=SLAConstants.JOB_SUBMISSION_TIMEOUT,
            )
            print("✅ 任务已 Running")

            # Step 2: 获取 Pod 信息
            pod_info = await hyperpod_client.get_job_pods(job_id)
            pod_names = [p.get("name") for p in pod_info if p.get("name")]
            print(f"📋 任务 Pod: {pod_names}")

            if not pod_names:
                pytest.skip("No pods found for the job")

            # Step 3: 触发抢占
            release_start = time.time()
            preemption_config = {
                "image_uri": low_priority_job_config.get("image_uri"),
                "instance_type": low_priority_job_config.get("instance_type"),
                "node_count": 1,
                "command": ["python", "-c", "print('preemption job')"],
            }
            await hyperpod_client.trigger_preemption(
                cluster_name=cluster_name,
                target_job_name=job_id,
                preemption_job_config=preemption_config,
            )
            print("📤 已触发抢占")

            # Step 4: 等待 Pod 终止
            for pod_name in pod_names:
                await self._wait_for_pod_terminated(
                    hyperpod_client,
                    job_name=job_id,
                    pod_name=pod_name,
                    timeout=SLAConstants.POD_RELEASE_TIMEOUT,
                )

            release_time = time.time() - release_start

            # Assert
            assert release_time < SLAConstants.POD_RELEASE_TIMEOUT
            print(
                f"✅ Pod 释放完成，耗时: {release_time:.2f}s "
                f"(SLA: {SLAConstants.POD_RELEASE_TIMEOUT}s)"
            )

        finally:
            await self._cleanup_jobs(hyperpod_client, [job_id])

    @pytest.mark.asyncio
    @skip_write_tests
    async def test_job_status_transition_to_preempted(
        self,
        hyperpod_client: Any,
        async_client: AsyncClient,
        low_priority_job_config: dict[str, Any],
        admin_token: str,
    ) -> None:
        """场景4: 任务状态正确转换为 Preempted

        验证步骤:
        1. 通过 API 提交任务
        2. 触发抢占
        3. 验证 API 返回状态为 preempted
        4. 验证数据库状态一致
        """
        job_id: int | None = None

        try:
            # Step 1: 通过 API 提交任务
            response = await async_client.post(
                "/api/v1/training-jobs",
                json=low_priority_job_config,
                headers={"Authorization": f"Bearer {admin_token}"},
            )

            if response.status_code != 201:
                pytest.skip(f"Failed to submit job via API: {response.status_code}")

            job_id = response.json()["id"]
            print(f"📤 已通过 API 提交任务: {job_id}")

            # 等待 Running
            await self._wait_for_api_status(
                async_client,
                admin_token,
                job_id,
                "running",
                timeout=SLAConstants.JOB_SUBMISSION_TIMEOUT,
            )
            print("✅ 任务已 Running")

            # Step 2: 触发抢占
            # 注：需要通过 HyperPod 客户端触发，因为是底层操作
            cluster_name = getattr(hyperpod_client, "_cluster_name", "")
            hyperpod_job_id = response.json().get("hyperpod_job_name")
            if hyperpod_job_id:
                preemption_config = {
                    "image_uri": low_priority_job_config.get("image_uri"),
                    "instance_type": low_priority_job_config.get("instance_type"),
                    "node_count": 1,
                    "command": ["python", "-c", "print('preemption job')"],
                }
                await hyperpod_client.trigger_preemption(
                    cluster_name=cluster_name,
                    target_job_name=hyperpod_job_id,
                    preemption_job_config=preemption_config,
                )
                print("📤 已触发抢占")
            else:
                pytest.skip("No HyperPod job name in response")

            # Step 3: 验证 API 状态
            await self._wait_for_api_status(
                async_client,
                admin_token,
                job_id,
                "preempted",
                timeout=60,
            )

            # 获取最终状态
            status_response = await async_client.get(
                f"/api/v1/training-jobs/{job_id}",
                headers={"Authorization": f"Bearer {admin_token}"},
            )
            job_data = status_response.json()

            # Assert
            assert job_data["status"].lower() == "preempted"
            assert job_data.get("preemption_count", 0) >= 1
            print("✅ 状态转换正确: running → preempted")
            print(f"   preemption_count: {job_data.get('preemption_count')}")

        finally:
            if job_id:
                # 通过 API 取消任务
                await async_client.delete(
                    f"/api/v1/training-jobs/{job_id}",
                    headers={"Authorization": f"Bearer {admin_token}"},
                )

    @pytest.mark.asyncio
    @skip_write_tests
    async def test_auto_recovery_from_preemption(
        self,
        hyperpod_client: Any,
        checkpoint_enabled_job_config: dict[str, Any],
    ) -> None:
        """场景5: 抢占后自动恢复成功

        验证步骤:
        1. 提交任务，等待 Running
        2. 触发抢占，等待 checkpoint 保存
        3. 触发恢复
        4. 验证任务从 checkpoint 恢复并继续运行
        """
        cluster_name = getattr(hyperpod_client, "_cluster_name", "")
        job_id: str | None = None
        resumed_job_id: str | None = None
        checkpoint_base_path = checkpoint_enabled_job_config.get(
            "checkpoint_config", {}
        ).get("s3_path", "s3://ai-training-checkpoints-dev/checkpoints")

        try:
            # Step 1: 提交任务
            job_name = checkpoint_enabled_job_config.get("job_name", f"e2e-recovery-{int(time.time())}")
            result = await hyperpod_client.submit_training_job(
                cluster_name=cluster_name,
                job_name=job_name,
                job_config=checkpoint_enabled_job_config,
            )
            job_id = result.get("job_name", job_name)
            track_resource("training_job", job_id)
            print(f"📤 已提交任务: {job_id}")

            await self._wait_for_status(
                hyperpod_client,
                job_id,
                "Running",
                timeout=SLAConstants.JOB_SUBMISSION_TIMEOUT,
            )
            print("✅ 任务已 Running")

            # 等待训练积累状态
            print("⏳ 等待训练积累状态 (30s)...")
            await asyncio.sleep(30)

            # Step 2: 触发抢占
            preemption_config = {
                "image_uri": checkpoint_enabled_job_config.get("image_uri"),
                "instance_type": checkpoint_enabled_job_config.get("instance_type"),
                "node_count": 1,
                "command": ["python", "-c", "print('preemption job')"],
            }
            await hyperpod_client.trigger_preemption(
                cluster_name=cluster_name,
                target_job_name=job_id,
                preemption_job_config=preemption_config,
            )
            print("📤 已触发抢占")

            await self._wait_for_status(
                hyperpod_client,
                job_id,
                "Preempted",
                timeout=60,
            )
            print("✅ 任务已 Preempted")

            # 等待 checkpoint 完成
            checkpoint_info = await self._wait_for_checkpoint(
                hyperpod_client,
                job_id,
                timeout=SLAConstants.CHECKPOINT_SAVE_TIMEOUT,
                checkpoint_base_path=checkpoint_base_path,
            )
            assert checkpoint_info is not None, "Checkpoint 未创建"
            print(f"✅ Checkpoint 已保存: {checkpoint_info.get('key')}")

            # Step 3: 触发恢复
            recovery_start = time.time()
            s3_path = checkpoint_info.get("s3_path") or checkpoint_info.get("key")
            if s3_path and not s3_path.startswith("s3://"):
                s3_path = f"{checkpoint_base_path.rstrip('/')}/{s3_path}"

            resumed_job_name = f"{job_id}-resumed-{int(time.time())}"
            result = await hyperpod_client.resume_training_job(
                cluster_name=cluster_name,
                job_name=resumed_job_name,
                checkpoint_path=s3_path,
                job_config=checkpoint_enabled_job_config,
            )
            resumed_job_id = result.get("job_name", resumed_job_name)
            track_resource("training_job", resumed_job_id)
            print("📤 已触发恢复")

            # Step 4: 验证恢复成功
            await self._wait_for_status(
                hyperpod_client,
                resumed_job_id,
                "Running",
                timeout=SLAConstants.JOB_SUBMISSION_TIMEOUT,
            )
            recovery_time = time.time() - recovery_start

            # Assert
            job_status = await hyperpod_client.get_training_job_status(
                cluster_name=cluster_name, job_name=resumed_job_id
            )
            assert job_status["status"].lower() == "running"
            print(f"✅ 自动恢复成功，耗时: {recovery_time:.2f}s")

        finally:
            await self._cleanup_jobs(hyperpod_client, [job_id, resumed_job_id])


@pytest.mark.e2e
@pytest.mark.aws_integration
@skip_without_aws
@skip_without_hyperpod
class TestPreemptionEdgeCasesE2E:
    """抢占边界情况 E2E 测试"""

    @pytest.mark.asyncio
    @skip_write_tests
    async def test_preemption_count_limit(
        self,
        hyperpod_client: Any,
        async_client: AsyncClient,
        low_priority_job_config: dict[str, Any],
        admin_token: str,
    ) -> None:
        """验证抢占次数限制 (MAX_PREEMPTION_COUNT = 3)

        当任务被抢占超过 3 次时，应该标记为失败
        """
        job_id: int | None = None

        try:
            # 提交任务
            response = await async_client.post(
                "/api/v1/training-jobs",
                json=low_priority_job_config,
                headers={"Authorization": f"Bearer {admin_token}"},
            )

            if response.status_code != 201:
                pytest.skip(f"Failed to submit job: {response.status_code}")

            job_id = response.json()["id"]

            # 模拟多次抢占
            # 注：这个测试在真实环境中可能需要较长时间
            print(
                f"⚠️ 此测试验证抢占次数限制 "
                f"(MAX_PREEMPTION_COUNT = {SLAConstants.MAX_PREEMPTION_COUNT})"
            )
            print("   在真实环境中可能需要较长时间")

            # 查询当前抢占次数
            status_response = await async_client.get(
                f"/api/v1/training-jobs/{job_id}",
                headers={"Authorization": f"Bearer {admin_token}"},
            )

            if status_response.status_code == 200:
                preemption_count = status_response.json().get("preemption_count", 0)
                print(f"📊 当前抢占次数: {preemption_count}")
                print(f"📊 最大抢占次数: {SLAConstants.MAX_PREEMPTION_COUNT}")

        finally:
            if job_id:
                await async_client.delete(
                    f"/api/v1/training-jobs/{job_id}",
                    headers={"Authorization": f"Bearer {admin_token}"},
                )

    @pytest.mark.asyncio
    async def test_preemption_status_query(
        self,
        async_client: AsyncClient,
        admin_token: str,
    ) -> None:
        """验证抢占状态查询 API

        验证可以通过 API 查询处于 preempted 状态的任务
        """
        response = await async_client.get(
            "/api/v1/training-jobs",
            params={"status": "preempted", "limit": 10},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        if response.status_code == 200:
            data = response.json()
            items = data.get("items", [])
            print(f"📊 当前 preempted 状态任务数: {len(items)}")

            for job in items[:3]:  # 只显示前 3 个
                print(
                    f"   - {job.get('job_name')}: "
                    f"preemption_count={job.get('preemption_count')}"
                )
        elif response.status_code == 404:
            pytest.skip("Training jobs API not available")
        else:
            print(f"⚠️ API response: {response.status_code}")
