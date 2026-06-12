/**
 * 审计用数据集 fixture
 * 形状对照: src/features/datasets/types/index.ts (DatasetSummary / DatasetDetail / DatasetVersion)
 * API 路径对照: src/features/datasets/api/datasetApi.ts
 *   GET /datasets | GET /datasets/{id} | GET /datasets/{id}/versions
 */

const base = {
  visibility: 'private' as const,
  owner_id: 1,
  owner_username: 'admin',
  tags: null as string[] | null,
  last_accessed_at: '2026-06-10T08:30:00Z',
};

export const mockDatasets = [
  { ...base, id: 1, name: '通用大模型预训练语料-v2', description: 'CommonCrawl 清洗后中英混合语料，约 1.2TB', version: 'v2.1.0', storage_type: 'fsx', storage_uri: 'fsx://fs-0a1b/datasets/pretrain-v2', total_size_bytes: 1319413953331, file_count: 18420, dataset_type: 'text', data_format: 'jsonl', status: 'available', tags: ['预训练', 'NLP'], created_at: '2026-03-02T10:00:00Z', updated_at: '2026-05-28T09:12:00Z' },
  { ...base, id: 2, name: '指令微调数据集-中文客服', description: '客服对话指令微调样本 48 万条', version: 'v1.4.2', storage_type: 's3', storage_uri: 's3://ai-studio-data/sft/customer-service', total_size_bytes: 2147483648, file_count: 12, dataset_type: 'text', data_format: 'parquet', status: 'available', tags: ['SFT'], owner_username: 'mlops-zhang', owner_id: 3, visibility: 'public' as const, created_at: '2026-04-11T06:20:00Z', updated_at: '2026-06-01T11:00:00Z' },
  { ...base, id: 3, name: '工业质检图像集', description: '产线缺陷检测标注图像', version: 'v3.0.0', storage_type: 'fsx', storage_uri: 'fsx://fs-0a1b/datasets/qc-images', total_size_bytes: 549755813888, file_count: 230400, dataset_type: 'image', data_format: 'coco', status: 'preparing', tags: ['CV', '质检'], created_at: '2026-05-19T02:00:00Z', updated_at: '2026-06-11T15:45:00Z' },
  { ...base, id: 4, name: '语音指令音频库', description: '智能家居唤醒词与指令音频', version: 'v1.0.0', storage_type: 's3', storage_uri: 's3://ai-studio-data/audio/voice-cmd', total_size_bytes: 107374182400, file_count: 96000, dataset_type: 'audio', data_format: 'wav', status: 'available', tags: ['语音'], owner_username: 'audio-team', owner_id: 5, created_at: '2026-02-25T09:00:00Z', updated_at: '2026-04-30T10:10:00Z' },
  { ...base, id: 5, name: '推荐系统行为日志', description: '匿名化用户行为序列，用于排序模型训练', version: 'v0.9.1', storage_type: 'efs', storage_uri: 'efs://fs-77aa/datasets/rec-logs', total_size_bytes: 3298534883328, file_count: 412, dataset_type: 'tabular', data_format: 'parquet', status: 'archived', tags: ['推荐'], visibility: 'restricted' as const, last_accessed_at: '2026-01-10T12:00:00Z', created_at: '2025-12-01T00:00:00Z', updated_at: '2026-01-15T08:00:00Z' },
  { ...base, id: 6, name: '多模态对齐数据-图文对', description: 'LAION 子集精洗图文对', version: 'v2.0.0-beta', storage_type: 'fsx', storage_uri: 'fsx://fs-0a1b/datasets/mm-pairs', total_size_bytes: 879609302220, file_count: 5120000, dataset_type: 'custom', data_format: 'webdataset', status: 'error', tags: ['多模态'], created_at: '2026-05-30T13:00:00Z', updated_at: '2026-06-12T01:20:00Z' },
  { ...base, id: 7, name: '安防视频片段集', description: '园区监控异常行为检测片段', version: 'v1.2.0', storage_type: 's3', storage_uri: 's3://ai-studio-data/video/security-clips', total_size_bytes: 2199023255552, file_count: 8400, dataset_type: 'video', data_format: 'mp4', status: 'available', tags: ['CV', '视频'], owner_username: 'cv-team', owner_id: 4, created_at: '2026-01-18T07:30:00Z', updated_at: '2026-03-22T16:40:00Z' },
];

export const datasetListResponse = {
  items: mockDatasets,
  total: mockDatasets.length,
  page: 1,
  page_size: 20,
  total_pages: 1,
};

export const datasetDetailResponse = {
  ...mockDatasets[0],
  training_jobs_count: 3,
};

/** 版本列表（字段按 DatasetVersion 类型核对：无 status/tags，含 created_by_username） */
export const mockDatasetVersions = [
  { id: 31, dataset_id: 1, version: 'v2.1.0', description: '补充 2026Q1 增量语料并去重', storage_uri: 'fsx://fs-0a1b/datasets/pretrain-v2/v2.1.0', total_size_bytes: 1319413953331, file_count: 18420, created_at: '2026-05-28T09:12:00Z', created_by_username: 'admin' },
  { id: 30, dataset_id: 1, version: 'v2.0.1', description: '修复 jsonl 编码异常样本', storage_uri: 'fsx://fs-0a1b/datasets/pretrain-v2/v2.0.1', total_size_bytes: 1287354842316, file_count: 18102, created_at: '2026-04-15T03:40:00Z', created_by_username: 'mlops-zhang' },
  { id: 29, dataset_id: 1, version: 'v2.0.0', description: '升级清洗管线，重切分训练/验证集', storage_uri: 'fsx://fs-0a1b/datasets/pretrain-v2/v2.0.0', total_size_bytes: 1254839572110, file_count: 17856, created_at: '2026-03-02T10:00:00Z', created_by_username: 'admin' },
  { id: 18, dataset_id: 1, version: 'v1.1.0', description: null, storage_uri: 'fsx://fs-0a1b/datasets/pretrain-v2/v1.1.0', total_size_bytes: 998579896320, file_count: 15210, created_at: '2025-12-20T08:00:00Z', created_by_username: 'data-eng-li' },
  { id: 12, dataset_id: 1, version: 'v1.0.0', description: '初始版本', storage_uri: 'fsx://fs-0a1b/datasets/pretrain-v2/v1.0.0', total_size_bytes: 912680550400, file_count: 14305, created_at: '2025-11-08T06:30:00Z', created_by_username: 'data-eng-li' },
];

/** DatasetVersionListResponse 形状: { items, total }（无分页字段） */
export const datasetVersionListResponse = {
  items: mockDatasetVersions,
  total: mockDatasetVersions.length,
};

export const emptyDatasetVersionListResponse = {
  items: [],
  total: 0,
};
