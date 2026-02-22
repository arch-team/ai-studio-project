# CloudWatch Logs 配置

## 概述

本目录包含 AI Training Platform 的 CloudWatch Logs 配置和验证工具。

## 文件说明

| 文件 | 用途 |
|------|------|
| `log-groups.yaml` | CloudWatch Log Groups 定义 (CDK 参考) |
| `insights-queries.md` | CloudWatch Logs Insights 查询模板 |
| `validate-cloudwatch.sh` | CloudWatch 配置验证脚本 |

## 日志组设计

| 日志组 | 留存策略 | 用途 |
|--------|---------|------|
| `/aws/hyperpod/training-platform` | 30 天 | 平台应用日志 |
| `/aws/hyperpod/training-platform/api` | 30 天 | API 请求/响应日志 |
| `/aws/hyperpod/training-platform/training-jobs` | 90 天 | 训练任务执行日志 |
| `/aws/hyperpod/training-platform/audit` | 365 天 | 安全审计日志 |

## 使用方式

```bash
# 验证 CloudWatch 配置
chmod +x validate-cloudwatch.sh
./validate-cloudwatch.sh --region us-east-1 --env dev
```
