# Prompt History Plugin

显示和搜索 Claude Code CLI 的 prompt 历史记录，类似于 Linux 的 `history` 命令。

## 功能

- **查看历史**: 显示最近的 prompt 记录
- **搜索过滤**: 使用自然语言描述过滤条件
- **项目过滤**: 按项目路径筛选历史
- **时间过滤**: 按时间范围筛选
- **复用执行**: 选择历史记录重新执行

## 安装

```bash
# 本地测试
claude --plugin-dir /path/to/prompt-history
```

## 权限配置（可选）

为避免每次读取历史文件时询问权限，可添加以下配置到 `~/.claude/settings.local.json`：

```json
{
  "permissions": {
    "allow": [
      "Read(~/.claude/history.jsonl)"
    ]
  }
}
```

或使用命令快速配置：

```bash
# 如果文件不存在，先创建
echo '{"permissions":{"allow":["Read(~/.claude/history.jsonl)"]}}' > ~/.claude/settings.local.json
```

## 使用方法

```bash
/history              # 显示最近 20 条
/history 50           # 显示最近 50 条
/history 搜索 git     # 搜索包含 git 的历史
/history 今天         # 显示今天的记录
/history ai-studio    # 按项目名过滤
```

## 数据源

- **文件**: `~/.claude/history.jsonl`
- **格式**: JSON Lines (每行一条 JSON 记录)
- **字段**:
  - `display`: prompt 内容
  - `timestamp`: Unix 时间戳 (毫秒)
  - `project`: 项目绝对路径
  - `sessionId`: 会话 ID (可选)

## 许可证

MIT
