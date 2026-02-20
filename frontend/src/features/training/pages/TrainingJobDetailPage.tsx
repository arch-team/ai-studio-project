/**
 * Training Job Detail Page
 *
 * 训练任务详情页面 - 显示任务配置、状态、检查点和操作
 */

import {
  Box,
  BreadcrumbGroup,
  Button,
  ColumnLayout,
  Container,
  Header,
  KeyValuePairs,
  Modal,
  SpaceBetween,
  Spinner,
  Table,
  Tabs,
} from "@cloudscape-design/components";
import { useState, useCallback } from "react";
import { useNavigate, useParams } from "react-router-dom";
import {
  useTrainingJob,
  useTrainingJobCheckpoints,
  useTrainingJobLogs,
  usePauseTrainingJob,
  useResumeTrainingJob,
  useDeleteTrainingJob,
} from "../api";
import { TrainingStatusBadge, TrainingStatusMonitor } from "../components";
import { formatDateTime, formatDuration, formatFileSize } from "@shared/utils";
import type { LogEntry } from "../types";
import type { Checkpoint } from "../types";
import { JOB_PRIORITY_LABELS, DISTRIBUTION_STRATEGY_LABELS } from "../types";

/**
 * 检查点表格列定义
 */
const checkpointColumns = [
  {
    id: "checkpoint_name",
    header: "检查点名称",
    cell: (item: Checkpoint) => item.checkpoint_name,
  },
  {
    id: "epoch",
    header: "Epoch",
    cell: (item: Checkpoint) => item.epoch ?? "-",
  },
  {
    id: "step",
    header: "Step",
    cell: (item: Checkpoint) => item.step ?? "-",
  },
  {
    id: "storage_path",
    header: "存储路径",
    cell: (item: Checkpoint) => (
      <Box fontSize="body-s">
        <code>{item.storage_path}</code>
      </Box>
    ),
  },
  {
    id: "size_bytes",
    header: "大小",
    cell: (item: Checkpoint) => formatFileSize(item.size_bytes),
  },
  {
    id: "created_at",
    header: "创建时间",
    cell: (item: Checkpoint) => formatDateTime(item.created_at),
  },
];

/**
 * 训练任务详情页面
 */
export function TrainingJobDetailPage() {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const jobId = id ? parseInt(id, 10) : undefined;

  // 删除确认弹窗
  const [showDeleteModal, setShowDeleteModal] = useState(false);

  // 获取任务详情
  const { data: job, isLoading, error, refetch } = useTrainingJob(jobId);

  // 获取检查点列表
  const { data: checkpointsData, isLoading: checkpointsLoading } =
    useTrainingJobCheckpoints(jobId);

  // 获取日志（running 状态时 5 秒轮询）
  const isRunning = job?.status === "running";
  const {
    data: logsData,
    isLoading: logsLoading,
    refetch: refetchLogs,
  } = useTrainingJobLogs(jobId, { limit: 100 }, isRunning ? 5000 : undefined);

  // Mutations
  const pauseMutation = usePauseTrainingJob();
  const resumeMutation = useResumeTrainingJob();
  const deleteMutation = useDeleteTrainingJob();

  // 判断是否可以暂停
  const canPause = job?.status === "running";
  // 判断是否可以恢复
  const canResume = job?.status === "paused" || job?.status === "preempted";
  // 判断是否可以删除
  const canDelete = job?.status !== "running";

  // 暂停任务
  const handlePause = useCallback(async () => {
    if (!jobId) return;
    await pauseMutation.mutateAsync(jobId);
    refetch();
  }, [jobId, pauseMutation, refetch]);

  // 恢复任务
  const handleResume = useCallback(async () => {
    if (!jobId) return;
    await resumeMutation.mutateAsync(jobId);
    refetch();
  }, [jobId, resumeMutation, refetch]);

  // 删除任务
  const handleDelete = useCallback(async () => {
    if (!jobId) return;
    await deleteMutation.mutateAsync(jobId);
    setShowDeleteModal(false);
    navigate("/training-jobs");
  }, [jobId, deleteMutation, navigate]);

  // 加载状态
  if (isLoading) {
    return (
      <Box textAlign="center" padding="xxl">
        <Spinner size="large" />
        <Box margin={{ top: "m" }}>加载中...</Box>
      </Box>
    );
  }

  // 错误状态
  if (error || !job) {
    return (
      <Container>
        <Box textAlign="center" color="text-status-error" padding="xl">
          {error?.message || "任务不存在"}
        </Box>
      </Container>
    );
  }

  return (
    <SpaceBetween size="l">
      {/* 面包屑导航 */}
      <BreadcrumbGroup
        items={[
          { text: "训练任务", href: "/training-jobs" },
          { text: job.job_name, href: "#" },
        ]}
        onFollow={(e) => {
          e.preventDefault();
          if (e.detail.href !== "#") {
            navigate(e.detail.href);
          }
        }}
      />

      {/* 页面标题和操作 */}
      <Header
        variant="h1"
        actions={
          <SpaceBetween direction="horizontal" size="xs">
            <Button iconName="refresh" onClick={() => refetch()}>
              刷新
            </Button>
            {canPause && (
              <Button onClick={handlePause} loading={pauseMutation.isPending}>
                暂停
              </Button>
            )}
            {canResume && (
              <Button
                variant="primary"
                onClick={handleResume}
                loading={resumeMutation.isPending}
              >
                恢复
              </Button>
            )}
            <Button
              onClick={() => setShowDeleteModal(true)}
              disabled={!canDelete}
            >
              删除
            </Button>
          </SpaceBetween>
        }
      >
        {job.job_name}
      </Header>

      {/* 概览信息 */}
      <Container header={<Header variant="h2">概览</Header>}>
        <ColumnLayout columns={4} variant="text-grid">
          <div>
            <Box variant="awsui-key-label">状态</Box>
            <TrainingStatusBadge status={job.status} />
          </div>
          <div>
            <Box variant="awsui-key-label">优先级</Box>
            <Box>{JOB_PRIORITY_LABELS[job.priority]}</Box>
          </div>
          <div>
            <Box variant="awsui-key-label">分布式策略</Box>
            <Box>
              {job.distribution_strategy
                ? DISTRIBUTION_STRATEGY_LABELS[job.distribution_strategy]
                : "-"}
            </Box>
          </div>
          <div>
            <Box variant="awsui-key-label">持续时间</Box>
            <Box>{formatDuration(job.started_at, job.completed_at)}</Box>
          </div>
        </ColumnLayout>
      </Container>

      {/* 进度信息 */}
      {(job.current_epoch != null || job.current_step != null) && (
        <Container header={<Header variant="h2">训练进度</Header>}>
          <ColumnLayout columns={4} variant="text-grid">
            <div>
              <Box variant="awsui-key-label">当前 Epoch</Box>
              <Box>
                {job.current_epoch ?? "-"} / {job.total_epochs ?? "-"}
              </Box>
            </div>
            <div>
              <Box variant="awsui-key-label">当前 Step</Box>
              <Box>{job.current_step ?? "-"}</Box>
            </div>
            <div>
              <Box variant="awsui-key-label">检查点数量</Box>
              <Box>{job.checkpoints_count ?? 0}</Box>
            </div>
            <div>
              <Box variant="awsui-key-label">完成度</Box>
              <Box>
                {job.current_epoch != null && job.total_epochs != null
                  ? `${Math.round((job.current_epoch / job.total_epochs) * 100)}%`
                  : "-"}
              </Box>
            </div>
          </ColumnLayout>
        </Container>
      )}

      {/* 详细信息标签页 */}
      <Tabs
        tabs={[
          {
            id: "config",
            label: "配置信息",
            content: (
              <Container>
                <KeyValuePairs
                  columns={2}
                  items={[
                    { label: "任务 ID", value: String(job.id) },
                    { label: "任务名称", value: job.job_name },
                    { label: "描述", value: job.description || "-" },
                    { label: "实例类型", value: job.instance_type || "-" },
                    { label: "节点数量", value: String(job.node_count) },
                    { label: "每节点 GPU", value: String(job.gpu_per_node) },
                    {
                      label: "总 GPU 数",
                      value: String(job.node_count * job.gpu_per_node),
                    },
                    { label: "容器镜像", value: job.image_uri || "-" },
                    { label: "训练脚本", value: job.entry_point || "-" },
                    {
                      label: "创建时间",
                      value: formatDateTime(job.created_at),
                    },
                    {
                      label: "开始时间",
                      value: formatDateTime(job.started_at),
                    },
                    {
                      label: "完成时间",
                      value: formatDateTime(job.completed_at),
                    },
                  ]}
                />
              </Container>
            ),
          },
          {
            id: "checkpoints",
            label: `检查点 (${checkpointsData?.items?.length || 0})`,
            content: (
              <Table
                columnDefinitions={checkpointColumns}
                items={checkpointsData?.items || []}
                loading={checkpointsLoading}
                loadingText="加载检查点..."
                variant="embedded"
                empty={
                  <Box textAlign="center" color="inherit" padding="l">
                    暂无检查点
                  </Box>
                }
              />
            ),
          },
          {
            id: "logs",
            label: "日志",
            content: (
              <Container
                header={
                  <Header
                    variant="h2"
                    actions={
                      <Button
                        iconName="refresh"
                        onClick={() => refetchLogs()}
                        loading={logsLoading}
                      >
                        刷新
                      </Button>
                    }
                  >
                    训练日志
                    {isRunning && (
                      <Box
                        display="inline"
                        margin={{ left: "s" }}
                        fontSize="body-s"
                        color="text-body-secondary"
                      >
                        (每 5 秒自动刷新)
                      </Box>
                    )}
                  </Header>
                }
              >
                {logsLoading && !logsData ? (
                  <Box textAlign="center" padding="l">
                    <Spinner /> 加载日志中...
                  </Box>
                ) : logsData?.logs && logsData.logs.length > 0 ? (
                  <Box padding="s" fontSize="body-s">
                    <div
                      style={{
                        fontFamily: "monospace",
                        whiteSpace: "pre-wrap",
                        maxHeight: "500px",
                        overflow: "auto",
                        backgroundColor:
                          "var(--color-background-container-content)",
                        padding: "12px",
                        borderRadius: "8px",
                      }}
                    >
                      {logsData.logs.map((log: LogEntry, index: number) => (
                        <div key={index} style={{ marginBottom: "4px" }}>
                          <span
                            style={{
                              color: "var(--color-text-body-secondary)",
                            }}
                          >
                            [
                            {new Date(log.timestamp).toLocaleTimeString(
                              "zh-CN",
                            )}
                            ]
                          </span>{" "}
                          <span
                            style={{ color: "var(--color-text-status-info)" }}
                          >
                            [{log.pod_name}]
                          </span>{" "}
                          {log.message}
                        </div>
                      ))}
                    </div>
                  </Box>
                ) : (
                  <Box
                    textAlign="center"
                    color="text-body-secondary"
                    padding="l"
                  >
                    暂无日志数据
                  </Box>
                )}
              </Container>
            ),
          },
          {
            id: "metrics",
            label: "训练指标",
            content: <TrainingStatusMonitor job={job} />,
          },
        ]}
      />

      {/* 删除确认弹窗 */}
      <Modal
        visible={showDeleteModal}
        onDismiss={() => setShowDeleteModal(false)}
        header="确认删除"
        footer={
          <Box float="right">
            <SpaceBetween direction="horizontal" size="xs">
              <Button variant="link" onClick={() => setShowDeleteModal(false)}>
                取消
              </Button>
              <Button
                variant="primary"
                onClick={handleDelete}
                loading={deleteMutation.isPending}
              >
                确认删除
              </Button>
            </SpaceBetween>
          </Box>
        }
      >
        确定要删除训练任务 <b>{job.job_name}</b> 吗？此操作不可恢复。
      </Modal>
    </SpaceBetween>
  );
}

export default TrainingJobDetailPage;
