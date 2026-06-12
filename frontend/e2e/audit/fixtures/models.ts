/**
 * 审计用模型 fixture
 * 形状对照: src/features/models/types/index.ts (ModelSummary / ModelDetail / ModelVersionsResponse)
 * API 路径对照: src/features/models/api/modelApi.ts
 *   GET /models | GET /models/{id} | GET /models/{id}/versions
 */

export const mockModels = [
  { id: 1, model_name: 'qwen2-7b-chat-sft', version: 'v3.2.0', display_name: '客服大模型-指令微调版', owner_id: 1, training_job_id: 1, status: 'deployed', framework: 'pytorch', metrics: { accuracy: 0.924, f1: 0.897, perplexity: 6.21 }, tags: ['LLM', '客服'], created_at: '2026-05-20T08:00:00Z', registered_at: '2026-05-21T02:30:00Z' },
  { id: 2, model_name: 'defect-detector-yolov9', version: 'v1.5.1', display_name: '产线缺陷检测模型', owner_id: 4, training_job_id: 3, status: 'registered', framework: 'pytorch', metrics: { mAP50: 0.913, recall: 0.886 }, tags: ['CV', '质检'], created_at: '2026-04-28T11:20:00Z', registered_at: '2026-04-29T01:00:00Z' },
  { id: 3, model_name: 'voice-cmd-asr-conformer', version: 'v2.0.0', display_name: '语音指令识别', owner_id: 5, training_job_id: 2, status: 'training', framework: 'pytorch', metrics: null, tags: ['语音', 'ASR'], created_at: '2026-06-10T06:40:00Z', registered_at: null },
  { id: 4, model_name: 'rec-ranker-din', version: 'v0.8.3', display_name: '推荐排序模型', owner_id: 3, training_job_id: 5, status: 'archived', framework: 'tensorflow', metrics: { auc: 0.781, gauc: 0.742 }, tags: ['推荐'], created_at: '2026-01-12T09:00:00Z', registered_at: '2026-01-13T03:10:00Z' },
  { id: 5, model_name: 'mm-clip-align', version: 'v1.0.0-rc1', display_name: '图文对齐编码器', owner_id: 1, training_job_id: 4, status: 'failed', framework: 'jax', metrics: { 'recall@1': 0.412 }, tags: ['多模态'], created_at: '2026-06-01T14:00:00Z', registered_at: null },
  { id: 6, model_name: 'doc-layout-parser', version: 'v2.3.0', display_name: '文档版面解析', owner_id: 4, training_job_id: null, status: 'registered', framework: 'pytorch', metrics: { f1: 0.951 }, tags: ['CV', 'OCR'], created_at: '2026-03-15T05:30:00Z', registered_at: '2026-03-16T08:00:00Z' },
  { id: 7, model_name: 'risk-tabnet-scorer', version: 'v1.1.0', display_name: '风控评分模型', owner_id: 3, training_job_id: null, status: 'deployed', framework: 'other', metrics: { ks: 0.46, auc: 0.823 }, tags: ['风控', '表格'], created_at: '2026-02-08T10:10:00Z', registered_at: '2026-02-09T00:20:00Z' },
];

export const modelListResponse = {
  items: mockModels,
  total: mockModels.length,
  page: 1,
  page_size: 20,
  total_pages: 1,
};

/** ModelDetail 为独立接口（非 extends Summary），逐字段对照类型编写 */
export const modelDetailResponse = {
  id: 1,
  model_name: 'qwen2-7b-chat-sft',
  version: 'v3.2.0',
  display_name: '客服大模型-指令微调版',
  description: '基于 Qwen2-7B 在 48 万条客服对话上做 SFT，已通过线上 A/B 验证',
  owner_id: 1,
  training_job_id: 1,
  checkpoint_id: 12,
  model_uri: 's3://ai-studio-models/qwen2-7b-chat-sft/v3.2.0/',
  model_path: '/models/qwen2-7b-chat-sft/v3.2.0',
  registry_arn: 'arn:aws:sagemaker:us-west-2:123456789012:model-package/qwen2-7b-chat-sft/3',
  registry_status: 'synced',
  metrics: { accuracy: 0.924, f1: 0.897, perplexity: 6.21 },
  hyperparameters: { learning_rate: 0.00002, batch_size: 64, max_epochs: 3, warmup_ratio: 0.03 },
  framework: 'pytorch',
  framework_version: '2.3.1',
  status: 'deployed',
  size_bytes: 15032385536,
  model_format: 'safetensors',
  tags: ['LLM', '客服'],
  created_at: '2026-05-20T08:00:00Z',
  updated_at: '2026-06-02T07:45:00Z',
  registered_at: '2026-05-21T02:30:00Z',
  archived_at: null,
};

/** ModelVersionsResponse 形状: { model_name, versions, comparison }（非标准分页） */
export const modelVersionsResponse = {
  model_name: 'qwen2-7b-chat-sft',
  versions: [
    { id: 1, version: 'v3.2.0', status: 'deployed', metrics: { accuracy: 0.924, f1: 0.897 }, hyperparameters: { learning_rate: 0.00002, batch_size: 64 }, created_at: '2026-05-20T08:00:00Z', registered_at: '2026-05-21T02:30:00Z' },
    { id: 11, version: 'v3.1.0', status: 'registered', metrics: { accuracy: 0.911, f1: 0.882 }, hyperparameters: { learning_rate: 0.00003, batch_size: 64 }, created_at: '2026-04-18T09:00:00Z', registered_at: '2026-04-19T01:10:00Z' },
    { id: 10, version: 'v3.0.0', status: 'registered', metrics: { accuracy: 0.902, f1: 0.871 }, hyperparameters: { learning_rate: 0.00003, batch_size: 32 }, created_at: '2026-03-25T12:00:00Z', registered_at: '2026-03-26T02:00:00Z' },
    { id: 9, version: 'v2.4.1', status: 'archived', metrics: { accuracy: 0.886, f1: 0.852 }, hyperparameters: { learning_rate: 0.00005, batch_size: 32 }, created_at: '2026-02-10T07:30:00Z', registered_at: '2026-02-11T00:00:00Z' },
    { id: 8, version: 'v2.4.0', status: 'failed', metrics: null, hyperparameters: { learning_rate: 0.0001, batch_size: 32 }, created_at: '2026-02-02T10:00:00Z', registered_at: null },
  ],
  comparison: null,
};

/** model-versions 页 empty 态返回体（标准 EMPTY_LIST 形状与本响应不一致，需显式声明） */
export const emptyModelVersionsResponse = {
  model_name: 'qwen2-7b-chat-sft',
  versions: [],
  comparison: null,
};
