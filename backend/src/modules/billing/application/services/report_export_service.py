"""报表导出服务 - T078。

提供 CSV 和 PDF 报表导出功能。

功能:
1. 资源使用报表 CSV 导出
2. 成本分析报表 CSV 导出
3. 支持列选择和格式化
4. UTF-8 编码支持中文列名
5. 数值格式化 (货币、存储容量、百分比)

技术实现:
- 使用 pandas DataFrame 处理数据
- 使用 io.BytesIO 在内存中生成文件
- 支持自定义列映射和格式化规则
"""

from datetime import datetime
from io import BytesIO

import pandas as pd


class ReportExportService:
    """报表导出服务 - 提供多种格式的报表导出。"""

    # 资源使用报表列映射 (英文字段名 -> 中文列名)
    RESOURCE_USAGE_COLUMN_MAP = {
        "user_id": "用户ID",
        "username": "用户名",
        "total_gpu_hours": "总GPU时数",
        "total_cost_usd": "总成本(USD)",
        "total_storage_bytes": "总存储空间",
        "total_training_jobs": "训练任务总数",
        "created_at": "创建时间",
        "updated_at": "更新时间",
    }

    # 成本分析报表列映射
    COST_ANALYSIS_COLUMN_MAP = {
        "period": "周期",
        "compute_cost": "计算成本",
        "storage_cost": "存储成本",
        "network_cost": "网络成本",
        "total_cost": "总成本",
        "job_count": "任务数量",
    }

    def export_resource_usage_csv(self, data: list[dict], columns: list[str] | None = None) -> bytes:
        """导出资源使用报表为 CSV 格式。

        Args:
            data: 资源使用数据列表，每个元素为字典
            columns: 可选，指定要导出的列（英文字段名）

        Returns:
            bytes: CSV 文件的字节内容 (UTF-8 编码)

        数据格式化:
        - total_gpu_hours: 保留 2 位小数
        - total_cost_usd: $ 符号 + 2 位小数
        - total_storage_bytes: 转换为 GB 单位
        - created_at/updated_at: YYYY-MM-DD HH:MM:SS
        """
        if not data:
            # 空数据时返回只有列头的 CSV
            df = pd.DataFrame(columns=list(self.RESOURCE_USAGE_COLUMN_MAP.keys()))
        else:
            df = pd.DataFrame(data)

        # 列选择
        if columns:
            df = df[[col for col in columns if col in df.columns]]

        # 格式化数值和日期
        df = self._format_resource_usage_dataframe(df)

        # 列名映射为中文
        df = df.rename(columns=self.RESOURCE_USAGE_COLUMN_MAP)

        # 导出为 CSV (UTF-8 编码)
        output = BytesIO()
        df.to_csv(output, index=False, encoding="utf-8")
        return output.getvalue()

    def export_cost_analysis_csv(self, data: list[dict], columns: list[str] | None = None) -> bytes:
        """导出成本分析报表为 CSV 格式。

        Args:
            data: 成本分析数据列表
            columns: 可选，指定要导出的列（英文字段名）

        Returns:
            bytes: CSV 文件的字节内容 (UTF-8 编码)

        数据格式化:
        - 所有成本字段: $ 符号 + 千位分隔符 + 2 位小数
        - job_count: 整数
        """
        if not data:
            df = pd.DataFrame(columns=list(self.COST_ANALYSIS_COLUMN_MAP.keys()))
        else:
            df = pd.DataFrame(data)

        # 列选择
        if columns:
            df = df[[col for col in columns if col in df.columns]]

        # 格式化成本数据
        df = self._format_cost_analysis_dataframe(df)

        # 列名映射为中文
        df = df.rename(columns=self.COST_ANALYSIS_COLUMN_MAP)

        # 导出为 CSV
        output = BytesIO()
        df.to_csv(output, index=False, encoding="utf-8")
        return output.getvalue()

    def _format_resource_usage_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """格式化资源使用数据。

        Args:
            df: pandas DataFrame

        Returns:
            格式化后的 DataFrame
        """
        df = df.copy()

        # GPU 时数: 保留 2 位小数
        if "total_gpu_hours" in df.columns:
            df["total_gpu_hours"] = df["total_gpu_hours"].apply(lambda x: f"{float(x):.2f}" if pd.notna(x) else "0.00")

        # 成本: $ 符号 + 2 位小数
        if "total_cost_usd" in df.columns:
            df["total_cost_usd"] = df["total_cost_usd"].apply(lambda x: f"${float(x):.2f}" if pd.notna(x) else "$0.00")

        # 存储空间: 字节转 GB
        if "total_storage_bytes" in df.columns:
            df["total_storage_bytes"] = df["total_storage_bytes"].apply(
                lambda x: f"{float(x) / (1024 ** 3):.2f} GB" if pd.notna(x) and x > 0 else "0.00 GB"
            )

        # 日期时间格式化
        for date_col in ["created_at", "updated_at"]:
            if date_col in df.columns:
                df[date_col] = df[date_col].apply(
                    lambda x: x.strftime("%Y-%m-%d %H:%M:%S") if isinstance(x, datetime) else str(x)
                )

        return df

    def _format_cost_analysis_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """格式化成本分析数据。

        Args:
            df: pandas DataFrame

        Returns:
            格式化后的 DataFrame
        """
        df = df.copy()

        # 成本字段: $ 符号 + 千位分隔符 + 2 位小数
        cost_columns = ["compute_cost", "storage_cost", "network_cost", "total_cost"]
        for col in cost_columns:
            if col in df.columns:
                df[col] = df[col].apply(lambda x: f"${float(x):,.2f}" if pd.notna(x) else "$0.00")

        return df
