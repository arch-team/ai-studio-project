/**
 * 审计用检查点 fixture
 * 形状对照: src/features/training/types/index.ts (Checkpoint / CheckpointListResponse)
 * API 路径对照: src/features/training/api/trainingJobApi.ts
 *   GET /training-jobs/{jobId}/checkpoints
 *
 * 注意：CheckpointListResponse 同时含 items 与 checkpoints 两个数组字段
 * （页面读取 items ?? checkpoints），fixture 两者都填同一数组。
 */

export const mockCheckpoints = [
  { id: 12, training_job_id: 1, checkpoint_name: 'ckpt-best-epoch3', storage_path: 's3://ai-studio-ckpt/job-1/ckpt-best-epoch3/', checkpoint_type: 'best', epoch: 3, step: 9000, size_bytes: 15032385536, loss: 0.342, accuracy: 0.917, storage_tier: 'fsx', status: 'available', metadata: { optimizer: 'adamw', saved_by: 'auto' }, created_at: '2026-06-11T21:40:00Z' },
  { id: 11, training_job_id: 1, checkpoint_name: 'ckpt-epoch-3', storage_path: 's3://ai-studio-ckpt/job-1/ckpt-epoch-3/', checkpoint_type: 'epoch', epoch: 3, step: 9000, size_bytes: 15032385536, loss: 0.351, accuracy: 0.912, storage_tier: 'nvme', status: 'available', metadata: null, created_at: '2026-06-11T21:38:00Z' },
  { id: 10, training_job_id: 1, checkpoint_name: 'ckpt-step-7500', storage_path: 's3://ai-studio-ckpt/job-1/ckpt-step-7500/', checkpoint_type: 'step', epoch: 2, step: 7500, size_bytes: 15032385536, loss: 0.418, accuracy: 0.894, storage_tier: 'nvme', status: 'available', metadata: null, created_at: '2026-06-11T15:10:00Z' },
  { id: 9, training_job_id: 1, checkpoint_name: 'ckpt-manual-debug', storage_path: 's3://ai-studio-ckpt/job-1/ckpt-manual-debug/', checkpoint_type: 'manual', epoch: 2, step: 6800, size_bytes: 15032385536, loss: 0.436, accuracy: null, storage_tier: 'fsx', status: 'available', metadata: { note: '排查梯度爆炸前手动保存' }, created_at: '2026-06-11T12:02:00Z' },
  { id: 8, training_job_id: 1, checkpoint_name: 'ckpt-epoch-2', storage_path: 's3://ai-studio-ckpt/job-1/ckpt-epoch-2/', checkpoint_type: 'epoch', epoch: 2, step: 6000, size_bytes: 15032385536, loss: 0.489, accuracy: 0.871, storage_tier: 's3', status: 'archived', metadata: null, created_at: '2026-06-10T23:55:00Z' },
  { id: 7, training_job_id: 1, checkpoint_name: 'ckpt-epoch-1', storage_path: 's3://ai-studio-ckpt/job-1/ckpt-epoch-1/', checkpoint_type: 'epoch', epoch: 1, step: 3000, size_bytes: 15032385536, loss: 0.7124, accuracy: 0.802, storage_tier: 's3', status: 'archived', metadata: null, created_at: '2026-06-10T08:20:00Z' },
  { id: 6, training_job_id: 1, checkpoint_name: 'ckpt-step-500-warmup', storage_path: 's3://ai-studio-ckpt/job-1/ckpt-step-500-warmup/', checkpoint_type: 'step', epoch: 0, step: 500, size_bytes: 15032385536, loss: 1.893, accuracy: null, storage_tier: 's3', status: 'deleted', metadata: null, created_at: '2026-06-09T19:30:00Z' },
];

/** CheckpointListResponse: { items, checkpoints } 双字段 */
export const checkpointListResponse = {
  items: mockCheckpoints,
  checkpoints: mockCheckpoints,
};
