"""API Contract 测试公共 Fixtures。

提供 OpenAPI schema 获取和 contract YAML 加载能力。
部分 contract YAML 文件存在格式问题无法被 safe_load 解析，
因此提供基于正则表达式的备用解析方案。
"""

import re
from pathlib import Path
from typing import Any

import pytest
import yaml
from httpx import AsyncClient

# contract YAML 文件所在目录
CONTRACTS_DIR = (
    Path(__file__).resolve().parents[4]
    / "specs"
    / "001-ai-training-platform"
    / "contracts"
)


@pytest.fixture
async def openapi_schema(client: AsyncClient) -> dict[str, Any]:
    """获取 FastAPI 自动生成的 OpenAPI schema。"""
    response = await client.get("/openapi.json")
    assert response.status_code == 200, "无法获取 OpenAPI schema"
    return response.json()


@pytest.fixture
def openapi_paths(openapi_schema: dict[str, Any]) -> dict[str, Any]:
    """从 OpenAPI schema 中提取 paths 字典。"""
    return openapi_schema.get("paths", {})


def load_contract_yaml(filename: str) -> dict[str, Any]:
    """加载 contract YAML 文件。

    优先使用 yaml.safe_load 解析，如果 YAML 格式有问题则回退到正则提取。
    """
    filepath = CONTRACTS_DIR / filename
    assert filepath.exists(), f"Contract 文件不存在: {filepath}"
    with open(filepath, encoding="utf-8") as f:
        content = f.read()

    try:
        return yaml.safe_load(content)
    except yaml.YAMLError:
        # YAML 格式问题 (如示例值中包含特殊字符), 回退到正则提取
        return _extract_paths_via_regex(content)


def _extract_paths_via_regex(content: str) -> dict[str, Any]:
    """通过正则表达式从 YAML 文本中提取路径和方法。

    适用于 YAML 格式存在解析问题的情况。
    """
    # 提取 paths 段落
    parts = content.split("paths:")
    if len(parts) < 2:
        return {"paths": {}}

    paths_section = parts[1]
    if "components:" in paths_section:
        paths_section = paths_section.split("components:")[0]

    current_path: str | None = None
    result: dict[str, dict[str, Any]] = {}

    for line in paths_section.split("\n"):
        # 匹配路径行: '  /xxx:'
        path_match = re.match(r"^  (/[^\s:]+):", line)
        if path_match:
            current_path = path_match.group(1)
            result[current_path] = {}
            continue
        # 匹配方法行: '    get/post/etc:'
        method_match = re.match(
            r"^    (get|post|put|patch|delete|head|options):", line
        )
        if method_match and current_path is not None:
            result[current_path][method_match.group(1)] = {}

    return {"paths": result}


def extract_contract_paths(
    contract: dict[str, Any],
) -> dict[str, set[str]]:
    """从 contract 数据中提取路径和 HTTP 方法。

    Returns:
        dict 映射: {路径: {方法集合}}
        例如: {"/training-jobs": {"get", "post"}}
    """
    result: dict[str, set[str]] = {}
    http_methods = {"get", "post", "put", "patch", "delete", "head", "options"}
    for path, path_item in contract.get("paths", {}).items():
        methods = {m for m in path_item if m.lower() in http_methods}
        result[path] = methods
    return result
