"""
训练任务指标收集服务 - T043 MetricsCollectionService

提供训练指标收集、聚合和查询功能:
- 从Kubernetes Pod日志收集训练指标
- 从Prometheus收集系统指标
- 指标聚合和时序数据存储
- 网络性能监控 (T043A)
- 训练任务超时和停滞检测 (T043B)

架构:
- 异步指标收集,避免阻塞训练
- 分层存储: 热数据(Redis) + 冷数据(PostgreSQL/TimescaleDB)
- 支持多种指标源: K8s logs, Prometheus, CloudWatch
"""
import asyncio
import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from kubernetes import client
from kubernetes.client.rest import ApiException

from models.training import TrainingJob, TrainingMetric
from services.k8s.client import get_k8s_client
from config.settings import get_settings

settings = get_settings()


class MetricsCollectionService:
    """训练指标收集和聚合服务"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.core_v1_api: Optional[client.CoreV1Api] = None
        self.custom_api: Optional[client.CustomObjectsApi] = None

    def _ensure_k8s_clients(self):
        """延迟初始化K8s客户端"""
        if self.core_v1_api is None:
            k8s_client = get_k8s_client()
            self.core_v1_api = client.CoreV1Api(api_client=k8s_client)
            self.custom_api = client.CustomObjectsApi(api_client=k8s_client)

    async def collect_training_metrics(
        self, job_id: int, since_seconds: int = 60
    ) -> List[TrainingMetric]:
        """
        从K8s Pod日志收集训练指标

        Args:
            job_id: 训练任务ID
            since_seconds: 收集最近N秒的指标

        Returns:
            List[TrainingMetric]: 收集到的指标列表

        指标格式示例 (从训练脚本输出):
        {"step": 100, "loss": 0.45, "accuracy": 0.89, "lr": 0.001, "timestamp": "2025-01-01T10:00:00Z"}
        """
        self._ensure_k8s_clients()

        # 查询训练任务
        result = await self.session.execute(
            select(TrainingJob).where(TrainingJob.id == job_id)
        )
        job = result.scalar_one_or_none()
        if not job or not job.k8s_job_name:
            return []

        # 获取所有worker pods的日志
        try:
            pods = await asyncio.to_thread(
                self.core_v1_api.list_namespaced_pod,
                namespace=job.k8s_namespace,
                label_selector=f"job-name={job.k8s_job_name},training.kubeflow.org/replica-type=worker"
            )
        except ApiException as e:
            print(f"Failed to list pods: {e}")
            return []

        metrics_list = []
        for pod in pods.items:
            pod_name = pod.metadata.name
            try:
                # 获取最近N秒的日志
                logs = await asyncio.to_thread(
                    self.core_v1_api.read_namespaced_pod_log,
                    name=pod_name,
                    namespace=job.k8s_namespace,
                    since_seconds=since_seconds,
                    tail_lines=1000  # 限制行数避免内存问题
                )

                # 解析日志中的指标 (支持JSON格式)
                parsed_metrics = self._parse_metrics_from_logs(logs, pod_name)
                metrics_list.extend(parsed_metrics)

            except ApiException as e:
                print(f"Failed to get logs for pod {pod_name}: {e}")
                continue

        # 保存到数据库
        if metrics_list:
            await self._save_metrics_batch(job_id, metrics_list)

        return metrics_list

    def _parse_metrics_from_logs(self, logs: str, pod_name: str) -> List[Dict[str, Any]]:
        """
        从Pod日志中解析训练指标

        支持两种格式:
        1. JSON格式: {"step": 100, "loss": 0.45, "accuracy": 0.89}
        2. 结构化文本: step=100 loss=0.45 accuracy=0.89
        """
        metrics_list = []

        for line in logs.split('\n'):
            line = line.strip()
            if not line:
                continue

            # 尝试JSON格式
            try:
                metric = json.loads(line)
                if isinstance(metric, dict) and 'step' in metric:
                    metric['pod_name'] = pod_name
                    metric['timestamp'] = metric.get('timestamp', datetime.utcnow().isoformat())
                    metrics_list.append(metric)
                    continue
            except json.JSONDecodeError:
                pass

            # 尝试结构化文本格式: step=100 loss=0.45
            match = re.search(r'step[=:\s]+(\d+)', line, re.IGNORECASE)
            if match:
                metric = {
                    'step': int(match.group(1)),
                    'pod_name': pod_name,
                    'timestamp': datetime.utcnow().isoformat()
                }

                # 提取loss
                loss_match = re.search(r'loss[=:\s]+([\d.]+)', line, re.IGNORECASE)
                if loss_match:
                    metric['loss'] = float(loss_match.group(1))

                # 提取accuracy
                acc_match = re.search(r'acc(?:uracy)?[=:\s]+([\d.]+)', line, re.IGNORECASE)
                if acc_match:
                    metric['accuracy'] = float(acc_match.group(1))

                # 提取learning rate
                lr_match = re.search(r'lr[=:\s]+([\d.e-]+)', line, re.IGNORECASE)
                if lr_match:
                    metric['learning_rate'] = float(lr_match.group(1))

                metrics_list.append(metric)

        return metrics_list

    async def _save_metrics_batch(self, job_id: int, metrics: List[Dict[str, Any]]):
        """批量保存指标到数据库"""
        db_metrics = []
        for metric in metrics:
            db_metric = TrainingMetric(
                job_id=job_id,
                metric_name='training_progress',
                metric_value=json.dumps(metric),
                step=metric.get('step'),
                timestamp=datetime.fromisoformat(metric['timestamp'].replace('Z', '+00:00'))
            )
            db_metrics.append(db_metric)

        self.session.add_all(db_metrics)
        await self.session.commit()

    async def get_latest_metrics(
        self, job_id: int, limit: int = 100
    ) -> List[TrainingMetric]:
        """获取最新的训练指标"""
        result = await self.session.execute(
            select(TrainingMetric)
            .where(TrainingMetric.job_id == job_id)
            .order_by(TrainingMetric.timestamp.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def aggregate_metrics(
        self, job_id: int, window_minutes: int = 5
    ) -> Dict[str, Any]:
        """
        聚合指标统计

        Args:
            job_id: 训练任务ID
            window_minutes: 时间窗口(分钟)

        Returns:
            聚合后的统计数据: {
                "avg_loss": 0.45,
                "min_loss": 0.40,
                "max_loss": 0.50,
                "steps_per_second": 10.5,
                "total_steps": 1000
            }
        """
        since_time = datetime.utcnow() - timedelta(minutes=window_minutes)

        result = await self.session.execute(
            select(TrainingMetric)
            .where(and_(
                TrainingMetric.job_id == job_id,
                TrainingMetric.timestamp >= since_time
            ))
        )
        metrics = list(result.scalars().all())

        if not metrics:
            return {}

        # 解析指标值
        losses = []
        accuracies = []
        steps = []

        for metric in metrics:
            try:
                data = json.loads(metric.metric_value)
                if 'loss' in data:
                    losses.append(data['loss'])
                if 'accuracy' in data:
                    accuracies.append(data['accuracy'])
                if 'step' in data:
                    steps.append(data['step'])
            except (json.JSONDecodeError, KeyError):
                continue

        aggregated = {
            'window_minutes': window_minutes,
            'sample_count': len(metrics)
        }

        if losses:
            aggregated['avg_loss'] = sum(losses) / len(losses)
            aggregated['min_loss'] = min(losses)
            aggregated['max_loss'] = max(losses)

        if accuracies:
            aggregated['avg_accuracy'] = sum(accuracies) / len(accuracies)
            aggregated['max_accuracy'] = max(accuracies)

        if steps:
            aggregated['total_steps'] = max(steps) - min(steps)
            aggregated['steps_per_second'] = aggregated['total_steps'] / (window_minutes * 60)

        return aggregated


class NetworkMetricsCollector:
    """
    网络性能监控服务 - T043A

    监控分布式训练中的网络性能:
    - Pod间通信延迟
    - 网络带宽使用
    - AllReduce/AllGather操作性能
    - 网络拥塞检测
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.core_v1_api: Optional[client.CoreV1Api] = None

    def _ensure_k8s_client(self):
        if self.core_v1_api is None:
            k8s_client = get_k8s_client()
            self.core_v1_api = client.CoreV1Api(api_client=k8s_client)

    async def collect_network_metrics(self, job_id: int) -> Dict[str, Any]:
        """
        收集训练任务的网络性能指标

        指标来源:
        1. Pod网络接口统计 (/sys/class/net/eth0/statistics/)
        2. NCCL调试日志 (NCCL_DEBUG=INFO)
        3. Prometheus node_exporter指标
        """
        self._ensure_k8s_client()

        result = await self.session.execute(
            select(TrainingJob).where(TrainingJob.id == job_id)
        )
        job = result.scalar_one_or_none()
        if not job or not job.k8s_job_name:
            return {}

        # 获取worker pods
        try:
            pods = await asyncio.to_thread(
                self.core_v1_api.list_namespaced_pod,
                namespace=job.k8s_namespace,
                label_selector=f"job-name={job.k8s_job_name},training.kubeflow.org/replica-type=worker"
            )
        except ApiException as e:
            print(f"Failed to list pods: {e}")
            return {}

        network_stats = []
        for pod in pods.items:
            pod_name = pod.metadata.name

            # 执行命令获取网络统计
            cmd = [
                'sh', '-c',
                'cat /sys/class/net/eth0/statistics/rx_bytes /sys/class/net/eth0/statistics/tx_bytes'
            ]

            try:
                exec_response = await asyncio.to_thread(
                    self.core_v1_api.read_namespaced_pod_exec,
                    name=pod_name,
                    namespace=job.k8s_namespace,
                    command=cmd,
                    stderr=True,
                    stdin=False,
                    stdout=True,
                    tty=False
                )

                lines = exec_response.split('\n')
                if len(lines) >= 2:
                    network_stats.append({
                        'pod_name': pod_name,
                        'rx_bytes': int(lines[0]),
                        'tx_bytes': int(lines[1]),
                        'timestamp': datetime.utcnow().isoformat()
                    })
            except (ApiException, ValueError) as e:
                print(f"Failed to get network stats for pod {pod_name}: {e}")
                continue

        # 计算聚合指标
        if network_stats:
            total_rx = sum(s['rx_bytes'] for s in network_stats)
            total_tx = sum(s['tx_bytes'] for s in network_stats)

            return {
                'total_rx_bytes': total_rx,
                'total_tx_bytes': total_tx,
                'total_rx_gb': round(total_rx / 1024**3, 2),
                'total_tx_gb': round(total_tx / 1024**3, 2),
                'pod_count': len(network_stats),
                'per_pod_stats': network_stats
            }

        return {}


class TrainingStallDetector:
    """
    训练任务停滞检测服务 - T043B

    检测训练任务的异常状态:
    - 超时检测 (基于max_runtime)
    - 停滞检测 (step不再增长)
    - GPU利用率异常低
    - 内存泄漏检测

    检测策略:
    - 周期性检查 (每5分钟)
    - 指标阈值触发
    - 多维度判断避免误报
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        # 检测阈值配置
        self.stall_threshold_minutes = 10  # 10分钟无新step视为停滞
        self.low_gpu_threshold = 0.1  # GPU利用率<10%视为异常

    async def detect_stalled_jobs(self) -> List[Dict[str, Any]]:
        """
        检测所有运行中任务的停滞情况

        Returns:
            停滞任务列表及诊断信息
        """
        # 查询所有运行中的任务
        result = await self.session.execute(
            select(TrainingJob).where(TrainingJob.status == 'running')
        )
        running_jobs = list(result.scalars().all())

        stalled_jobs = []
        for job in running_jobs:
            diagnosis = await self._diagnose_job(job)
            if diagnosis['is_stalled']:
                stalled_jobs.append({
                    'job_id': job.id,
                    'job_name': job.name,
                    'diagnosis': diagnosis
                })

        return stalled_jobs

    async def _diagnose_job(self, job: TrainingJob) -> Dict[str, Any]:
        """
        诊断单个训练任务状态

        检查项:
        1. 运行时间是否超时
        2. 最近是否有新的训练step
        3. GPU利用率是否正常 (TODO: 需要Prometheus集成)
        """
        diagnosis = {
            'is_stalled': False,
            'reasons': []
        }

        # 检查1: 超时检测
        if job.max_runtime_minutes:
            if job.started_at:
                runtime_minutes = (datetime.utcnow() - job.started_at).total_seconds() / 60
                if runtime_minutes > job.max_runtime_minutes:
                    diagnosis['is_stalled'] = True
                    diagnosis['reasons'].append({
                        'type': 'timeout',
                        'message': f'Job exceeded max runtime: {runtime_minutes:.1f}/{job.max_runtime_minutes} minutes'
                    })

        # 检查2: Step停滞检测
        stall_threshold_time = datetime.utcnow() - timedelta(minutes=self.stall_threshold_minutes)
        result = await self.session.execute(
            select(TrainingMetric)
            .where(and_(
                TrainingMetric.job_id == job.id,
                TrainingMetric.timestamp >= stall_threshold_time
            ))
            .order_by(TrainingMetric.timestamp.desc())
            .limit(1)
        )
        latest_metric = result.scalar_one_or_none()

        if not latest_metric:
            # 运行中但没有指标 -> 可能停滞
            if job.started_at and (datetime.utcnow() - job.started_at).total_seconds() > 300:
                # 启动5分钟后仍无指标
                diagnosis['is_stalled'] = True
                diagnosis['reasons'].append({
                    'type': 'no_metrics',
                    'message': f'No metrics received for {self.stall_threshold_minutes} minutes'
                })
        else:
            # 有历史指标,检查step是否增长
            result = await self.session.execute(
                select(TrainingMetric)
                .where(TrainingMetric.job_id == job.id)
                .order_by(TrainingMetric.timestamp.desc())
                .limit(10)
            )
            recent_metrics = list(result.scalars().all())

            if len(recent_metrics) >= 2:
                steps = []
                for metric in recent_metrics:
                    try:
                        data = json.loads(metric.metric_value)
                        if 'step' in data:
                            steps.append(data['step'])
                    except (json.JSONDecodeError, KeyError):
                        continue

                if steps and len(set(steps)) == 1:
                    # 所有step值相同 -> 停滞
                    diagnosis['is_stalled'] = True
                    diagnosis['reasons'].append({
                        'type': 'step_stall',
                        'message': f'Training step has not progressed (stuck at step {steps[0]})'
                    })

        return diagnosis

    async def auto_recover_stalled_job(self, job_id: int) -> bool:
        """
        自动恢复停滞任务

        恢复策略:
        1. 重启卡住的Pod
        2. 从最新checkpoint恢复
        3. 降低学习率重试

        Returns:
            bool: 恢复是否成功
        """
        # TODO: 实现自动恢复逻辑
        # 1. 获取job状态
        # 2. 根据停滞类型选择恢复策略
        # 3. 执行恢复操作
        # 4. 记录恢复日志
        return False
