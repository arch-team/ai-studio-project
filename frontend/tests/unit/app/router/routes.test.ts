/**
 * Routes Tests
 *
 * Task: T017 - 配置 React Router
 * TDD Step 1: Red - 编写测试
 */

import { describe, it, expect } from "vitest";
import { ROUTES, generatePath } from "@app/router/routes";

describe("ROUTES", () => {
  describe("公共路由", () => {
    it("should define HOME route", () => {
      expect(ROUTES.HOME).toBe("/");
    });

    it("should define LOGIN route", () => {
      expect(ROUTES.LOGIN).toBe("/login");
    });
  });

  describe("训练管理路由", () => {
    it("should define TRAINING_JOBS route", () => {
      expect(ROUTES.TRAINING_JOBS).toBe("/training-jobs");
    });

    it("should define TRAINING_JOB_DETAIL route", () => {
      expect(ROUTES.TRAINING_JOB_DETAIL).toBe("/training-jobs/:id");
    });

    it("should define TRAINING_JOB_CREATE route", () => {
      expect(ROUTES.TRAINING_JOB_CREATE).toBe("/training-jobs/create");
    });

    it("should define MODELS route", () => {
      expect(ROUTES.MODELS).toBe("/models");
    });

    it("should define MODEL_DETAIL route", () => {
      expect(ROUTES.MODEL_DETAIL).toBe("/models/:id");
    });

    it("should define MODEL_VERSIONS route", () => {
      expect(ROUTES.MODEL_VERSIONS).toBe("/models/:id/versions");
    });
  });

  describe("任务模板路由", () => {
    it("should define JOB_TEMPLATES route", () => {
      expect(ROUTES.JOB_TEMPLATES).toBe("/job-templates");
    });

    it("should define JOB_TEMPLATE_DETAIL route", () => {
      expect(ROUTES.JOB_TEMPLATE_DETAIL).toBe("/job-templates/:id");
    });

    it("should define JOB_TEMPLATE_CREATE route", () => {
      expect(ROUTES.JOB_TEMPLATE_CREATE).toBe("/job-templates/create");
    });
  });

  describe("数据管理路由", () => {
    it("should define DATASETS route", () => {
      expect(ROUTES.DATASETS).toBe("/datasets");
    });

    it("should define DATASET_CREATE route", () => {
      expect(ROUTES.DATASET_CREATE).toBe("/datasets/create");
    });

    it("should define DATASET_DETAIL route", () => {
      expect(ROUTES.DATASET_DETAIL).toBe("/datasets/:id");
    });

    it("should define DATASET_VERSIONS route", () => {
      expect(ROUTES.DATASET_VERSIONS).toBe("/datasets/:id/versions");
    });

    it("should define CHECKPOINTS route", () => {
      expect(ROUTES.CHECKPOINTS).toBe("/checkpoints");
    });
  });

  describe("资源管理路由", () => {
    it("should define RESOURCE_QUOTAS route", () => {
      expect(ROUTES.RESOURCE_QUOTAS).toBe("/resource-quotas");
    });
  });

  describe("管理员路由", () => {
    it("should define ADMIN route", () => {
      expect(ROUTES.ADMIN).toBe("/admin");
    });

    it("should define REPORTS route", () => {
      expect(ROUTES.REPORTS).toBe("/reports");
    });

    it("should define REPORTS_RESOURCE_USAGE route", () => {
      expect(ROUTES.REPORTS_RESOURCE_USAGE).toBe("/reports/resource-usage");
    });

    it("should define REPORTS_COST_ANALYSIS route", () => {
      expect(ROUTES.REPORTS_COST_ANALYSIS).toBe("/reports/cost-analysis");
    });
  });

  describe("开发工具路由", () => {
    it("should define IDE route", () => {
      expect(ROUTES.IDE).toBe("/ide");
    });
  });

  describe("错误页面路由", () => {
    it("should define NOT_FOUND route", () => {
      expect(ROUTES.NOT_FOUND).toBe("/404");
    });

    it("should define UNAUTHORIZED route", () => {
      expect(ROUTES.UNAUTHORIZED).toBe("/unauthorized");
    });
  });

  describe("路由路径完整性", () => {
    it("should have all routes defined as strings", () => {
      const routeValues = Object.values(ROUTES);
      routeValues.forEach((route) => {
        expect(typeof route).toBe("string");
        expect(route.startsWith("/")).toBe(true);
      });
    });

    it("should have no duplicate route paths", () => {
      const routeValues = Object.values(ROUTES);
      const uniqueValues = new Set(routeValues);
      expect(uniqueValues.size).toBe(routeValues.length);
    });
  });
});

describe("generatePath", () => {
  it("should replace single parameter", () => {
    const result = generatePath("/training-jobs/:id", { id: "123" });
    expect(result).toBe("/training-jobs/123");
  });

  it("should replace multiple parameters", () => {
    const result = generatePath("/models/:id/versions/:versionId", {
      id: "1",
      versionId: "2",
    });
    expect(result).toBe("/models/1/versions/2");
  });

  it("should return path unchanged when no params match", () => {
    const result = generatePath("/training-jobs", {});
    expect(result).toBe("/training-jobs");
  });

  it("should handle params that do not exist in template", () => {
    const result = generatePath("/training-jobs/:id", {
      id: "5",
      extra: "value",
    });
    expect(result).toBe("/training-jobs/5");
  });
});
