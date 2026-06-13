/**
 * 审计用任务模板 fixture
 * 形状对照: src/features/templates/types/index.ts (JobTemplateSummary / JobTemplateDetail)
 * API 路径对照: src/features/templates/api/templateApi.ts
 *   GET /job-templates | GET /job-templates/{id} | GET /job-templates/popular（返回裸数组）
 */

export const mockTemplates = [
  { id: 1, name: 'LLM-SFT 标准微调模板', description: '7B/14B 指令微调通用配置，FSDP + 混合精度', visibility: 'public', usage_count: 86, owner_id: 1, created_at: '2026-02-10T08:00:00Z' },
  { id: 2, name: '多机预训练-FSDP', description: '4 节点 p4d 预训练基线，含 NCCL 调优环境变量', visibility: 'team', usage_count: 42, owner_id: 1, created_at: '2026-03-05T10:30:00Z' },
  { id: 3, name: 'CV 目标检测-单机', description: 'YOLO 系列单机 4 卡训练，适合中小数据集', visibility: 'public', usage_count: 31, owner_id: 4, created_at: '2026-03-22T06:00:00Z' },
  { id: 4, name: 'ASR Conformer 训练', description: '语音识别 Conformer 模型 DDP 配置', visibility: 'team', usage_count: 17, owner_id: 5, created_at: '2026-04-11T09:20:00Z' },
  { id: 5, name: 'DeepSpeed ZeRO-3 大模型', description: '70B 级模型 DeepSpeed ZeRO-3 + offload 配置', visibility: 'private', usage_count: 9, owner_id: 1, created_at: '2026-05-08T14:00:00Z' },
  { id: 6, name: '推荐排序模型-夜间例行', description: '行为日志日更训练，spot 实例降本', visibility: 'team', usage_count: 58, owner_id: 3, created_at: '2026-01-20T02:00:00Z' },
  { id: 7, name: '调试用单卡小模板', description: 'g5.xlarge 单卡快速验证脚本可用性', visibility: 'private', usage_count: 3, owner_id: 2, created_at: '2026-06-01T11:00:00Z' },
];

export const templateListResponse = {
  items: mockTemplates,
  total: mockTemplates.length,
  page: 1,
  page_size: 20,
  total_pages: 1,
};

/** GET /job-templates/popular 返回 JobTemplateSummary[]（裸数组，非分页对象） */
export const popularTemplatesResponse = mockTemplates
  .slice()
  .sort((a, b) => b.usage_count - a.usage_count)
  .slice(0, 5);

/** JobTemplateDetail = Summary + training_config / last_used_at / updated_at */
export const templateDetailResponse = {
  ...mockTemplates[0],
  training_config: {
    image: 'public.ecr.aws/pytorch-training:2.3.1-gpu-py311-cu121-ubuntu22.04',
    script_path: 'train_sft.py',
    instance_type: 'ml.p4d.24xlarge',
    instance_count: 2,
    distribution_strategy: 'fsdp',
    environment: { NCCL_DEBUG: 'WARN', TOKENIZERS_PARALLELISM: 'false' },
    hyperparameters: { learning_rate: 0.00002, batch_size: 64, max_epochs: 3 },
  },
  last_used_at: '2026-06-09T15:40:00Z',
  updated_at: '2026-05-30T08:12:00Z',
};
