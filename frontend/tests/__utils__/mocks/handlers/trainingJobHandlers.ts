/**
 * Training Job API Handlers
 *
 * MSW handlers for /api/v1/training-jobs endpoints
 */

import { http, HttpResponse } from 'msw';
import { mockTrainingJobs, mockTrainingJobDetail } from '../data/trainingJobs';
import type { TrainingJobListResponse } from '@features/training/types';

const API_BASE = '/api/v1';

export const trainingJobHandlers = [
  // GET /training-jobs - 获取任务列表
  http.get(`${API_BASE}/training-jobs`, ({ request }) => {
    const url = new URL(request.url);
    const page = Number(url.searchParams.get('page')) || 1;
    const pageSize = Number(url.searchParams.get('page_size')) || 10;

    const response: TrainingJobListResponse = {
      items: mockTrainingJobs.slice((page - 1) * pageSize, page * pageSize),
      total: mockTrainingJobs.length,
      page,
      page_size: pageSize,
      total_pages: Math.ceil(mockTrainingJobs.length / pageSize),
    };

    return HttpResponse.json(response);
  }),

  // GET /training-jobs/:id - 获取任务详情
  http.get(`${API_BASE}/training-jobs/:id`, ({ params }) => {
    const id = Number(params.id);
    const job = mockTrainingJobDetail(id);

    if (!job) {
      return HttpResponse.json({ detail: '训练任务不存在' }, { status: 404 });
    }

    return HttpResponse.json(job);
  }),

  // POST /training-jobs/:id/pause - 暂停任务
  http.post(`${API_BASE}/training-jobs/:id/pause`, ({ params }) => {
    const id = Number(params.id);
    const job = mockTrainingJobDetail(id);

    if (!job) {
      return HttpResponse.json({ detail: '训练任务不存在' }, { status: 404 });
    }

    return HttpResponse.json({ ...job, status: 'paused' });
  }),

  // POST /training-jobs/:id/resume - 恢复任务
  http.post(`${API_BASE}/training-jobs/:id/resume`, ({ params }) => {
    const id = Number(params.id);
    const job = mockTrainingJobDetail(id);

    if (!job) {
      return HttpResponse.json({ detail: '训练任务不存在' }, { status: 404 });
    }

    return HttpResponse.json({ ...job, status: 'running' });
  }),
];
