/**
 * Routes Tests
 *
 * Task: T017 - 配置 React Router
 * TDD Step 1: Red - 编写测试
 */

import { describe, it, expect } from 'vitest';
import { ROUTES } from '@app/router/routes';

describe('ROUTES', () => {
  describe('公共路由', () => {
    it('should define HOME route', () => {
      expect(ROUTES.HOME).toBe('/');
    });

    it('should define LOGIN route', () => {
      expect(ROUTES.LOGIN).toBe('/login');
    });
  });

  describe('训练管理路由', () => {
    it('should define TRAINING_JOBS route', () => {
      expect(ROUTES.TRAINING_JOBS).toBe('/training-jobs');
    });

    it('should define TRAINING_JOB_DETAIL route', () => {
      expect(ROUTES.TRAINING_JOB_DETAIL).toBe('/training-jobs/:id');
    });

    it('should define TRAINING_JOB_CREATE route', () => {
      expect(ROUTES.TRAINING_JOB_CREATE).toBe('/training-jobs/create');
    });

    it('should define MODELS route', () => {
      expect(ROUTES.MODELS).toBe('/models');
    });
  });

  describe('数据管理路由', () => {
    it('should define DATASETS route', () => {
      expect(ROUTES.DATASETS).toBe('/datasets');
    });

    it('should define DATASET_DETAIL route', () => {
      expect(ROUTES.DATASET_DETAIL).toBe('/datasets/:id');
    });

    it('should define CHECKPOINTS route', () => {
      expect(ROUTES.CHECKPOINTS).toBe('/checkpoints');
    });
  });

  describe('资源管理路由', () => {
    it('should define RESOURCE_QUOTAS route', () => {
      expect(ROUTES.RESOURCE_QUOTAS).toBe('/resource-quotas');
    });
  });

  describe('管理员路由', () => {
    it('should define ADMIN route', () => {
      expect(ROUTES.ADMIN).toBe('/admin');
    });

    it('should define REPORTS route', () => {
      expect(ROUTES.REPORTS).toBe('/reports');
    });
  });

  describe('开发工具路由', () => {
    it('should define IDE route', () => {
      expect(ROUTES.IDE).toBe('/ide');
    });
  });

  describe('错误页面路由', () => {
    it('should define NOT_FOUND route', () => {
      expect(ROUTES.NOT_FOUND).toBe('/404');
    });

    it('should define UNAUTHORIZED route', () => {
      expect(ROUTES.UNAUTHORIZED).toBe('/unauthorized');
    });
  });
});
