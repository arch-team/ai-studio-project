#!/usr/bin/env python3
"""MLflow 训练指标记录示例 (T037a)

本示例展示如何在 PyTorch 训练脚本中集成 MLflow，
使 AI 训练平台能够通过 MLflowService 查询训练指标。

指标命名规范:
- 损失函数: loss, train_loss, val_loss
- 准确率: accuracy, train_accuracy, val_accuracy
- 学习率: learning_rate, lr
- 吞吐量: throughput, samples_per_second

记录频率建议:
- 训练损失: 每 100 steps
- 验证指标: 每 epoch
- 学习率: 调度器更新时

环境变量:
- MLFLOW_TRACKING_URI: MLflow 服务地址
- MLFLOW_EXPERIMENT_NAME: 实验名称 (可选)
- JOB_ID: 训练任务 ID (平台自动设置)

使用方法:
    # 本地测试
    export MLFLOW_TRACKING_URI=http://localhost:5000
    export JOB_ID=12345
    python mlflow_training_example.py

    # HyperPod 环境 (平台自动设置环境变量)
    python mlflow_training_example.py
"""

import os
import random
import time

import mlflow


def setup_mlflow() -> None:
    """配置 MLflow 连接和实验"""
    tracking_uri = os.getenv(
        "MLFLOW_TRACKING_URI", "http://mlflow.kubeflow.svc.cluster.local:5000"
    )
    experiment_name = os.getenv(
        "MLFLOW_EXPERIMENT_NAME", "ai-training-platform/default"
    )
    job_id = os.getenv("JOB_ID", "unknown")

    mlflow.set_tracking_uri(tracking_uri)
    mlflow.set_experiment(experiment_name)

    print(f"MLflow Tracking URI: {tracking_uri}")
    print(f"Experiment: {experiment_name}")
    print(f"Job ID: {job_id}")


def train_epoch(epoch: int, model: dict, optimizer_state: dict) -> dict:
    """模拟单个 epoch 的训练

    Args:
        epoch: 当前 epoch
        model: 模型参数 (模拟)
        optimizer_state: 优化器状态 (模拟)

    Returns:
        dict: 训练指标
    """
    # 模拟训练过程
    time.sleep(0.1)

    # 模拟递减的 loss 和递增的 accuracy
    base_loss = 1.0 / (epoch + 1)
    noise = random.uniform(-0.05, 0.05)

    train_loss = max(0.01, base_loss + noise)
    train_accuracy = min(0.99, 0.5 + epoch * 0.05 + random.uniform(-0.02, 0.02))

    return {
        "train_loss": train_loss,
        "train_accuracy": train_accuracy,
    }


def validate(epoch: int, model: dict) -> dict:
    """模拟验证过程

    Args:
        epoch: 当前 epoch
        model: 模型参数 (模拟)

    Returns:
        dict: 验证指标
    """
    time.sleep(0.05)

    val_loss = 1.0 / (epoch + 1) + random.uniform(0, 0.1)
    val_accuracy = 0.5 + epoch * 0.04 + random.uniform(-0.03, 0.03)

    return {
        "val_loss": val_loss,
        "val_accuracy": min(0.99, val_accuracy),
    }


def main():
    """主训练流程"""
    setup_mlflow()

    # 训练超参数
    hyperparams = {
        "learning_rate": 0.001,
        "batch_size": 32,
        "epochs": 10,
        "optimizer": "Adam",
        "model_type": "ResNet50",
        "distributed_strategy": "DDP",
    }

    # 获取 job_id 用于 MLflow tag
    job_id = os.getenv("JOB_ID", "local-test")

    with mlflow.start_run(tags={"job_id": job_id}):
        # 记录超参数
        mlflow.log_params(hyperparams)

        # 记录系统信息
        mlflow.set_tags(
            {
                "job_id": job_id,  # 关键: 平台通过此 tag 查找 run
                "framework": "pytorch",
                "environment": os.getenv("ENVIRONMENT", "local"),
            }
        )

        # 模拟模型和优化器
        model = {"weights": "initialized"}
        optimizer_state = {"lr": hyperparams["learning_rate"]}

        print(f"\n开始训练 (共 {hyperparams['epochs']} 个 epoch)")
        print("-" * 50)

        for epoch in range(hyperparams["epochs"]):
            # 训练一个 epoch
            train_metrics = train_epoch(epoch, model, optimizer_state)

            # 记录训练指标
            mlflow.log_metrics(
                {
                    "loss": train_metrics["train_loss"],  # 主指标 (停滞检测使用)
                    "train_loss": train_metrics["train_loss"],
                    "train_accuracy": train_metrics["train_accuracy"],
                },
                step=epoch,
            )

            # 验证
            val_metrics = validate(epoch, model)

            # 记录验证指标
            mlflow.log_metrics(
                {
                    "val_loss": val_metrics["val_loss"],
                    "val_accuracy": val_metrics["val_accuracy"],
                },
                step=epoch,
            )

            # 记录学习率
            current_lr = hyperparams["learning_rate"] * (0.95**epoch)
            mlflow.log_metric("learning_rate", current_lr, step=epoch)

            print(
                f"Epoch {epoch:3d} | "
                f"loss: {train_metrics['train_loss']:.4f} | "
                f"acc: {train_metrics['train_accuracy']:.4f} | "
                f"val_loss: {val_metrics['val_loss']:.4f} | "
                f"val_acc: {val_metrics['val_accuracy']:.4f}"
            )

        print("-" * 50)
        print("训练完成!")

        # 记录最终指标
        mlflow.log_metric("final_accuracy", train_metrics["train_accuracy"])

        # 获取 run 信息
        run = mlflow.active_run()
        print(f"\nMLflow Run ID: {run.info.run_id}")
        print(f"Job ID Tag: {job_id}")


if __name__ == "__main__":
    main()
