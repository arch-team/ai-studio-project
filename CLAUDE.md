# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Response Language
**所有对话和文档必须（Must）使用中文。**
**除非有特殊说明,请用中文回答。** (Unless otherwise specified, please respond in Chinese.)



## Active Technologies
- Python 3.11 (后端), TypeScript 5.3+ (前端) + FastAPI 0.109+, SQLAlchemy 2.0+, Pydantic v2, `sagemaker-hyperpod` SDK, boto3, aiomysql, React 18, AWS Cloudscape Design System, Vite, Zustand, TanStack Query v5 (001-ai-training-platform)
- MySQL 8.0+ (开发环境本地部署), Amazon Aurora MySQL 3.x+ (生产环境,兼容 MySQL 8.0), Amazon FSx for Lustre (训练数据,≥5GB/s 吞吐量), Amazon S3 + SageMaker Model Registry (模型制品), 分层检查点存储 (NVMe → FSx for Lustre → S3) (001-ai-training-platform)

## Recent Changes
- 001-ai-training-platform: Added Python 3.11 (后端), TypeScript 5.3+ (前端) + FastAPI 0.109+, SQLAlchemy 2.0+, Pydantic v2, `sagemaker-hyperpod` SDK, boto3, aiomysql, React 18, AWS Cloudscape Design System, Vite, Zustand, TanStack Query v5
