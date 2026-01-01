/**
 * 训练日志查看器组件
 *
 * 展示训练任务的实时日志,支持自动刷新、搜索和下载功能
 */

import React, { useState, useEffect, useRef } from 'react';
import { Card } from '../shared/Card';
import { Button } from '../shared/Button';

export interface LogEntry {
  timestamp: string;
  level: 'info' | 'warning' | 'error' | 'debug';
  message: string;
  source?: string;
}

interface LogViewerProps {
  jobId: number;
  logs: LogEntry[];
  loading?: boolean;
  autoRefresh?: boolean;
  onRefresh?: () => void;
  refreshInterval?: number; // 毫秒
}

// 日志级别对应的样式
const LOG_LEVEL_STYLES: Record<string, string> = {
  info: 'text-gray-700',
  warning: 'text-yellow-600',
  error: 'text-red-600',
  debug: 'text-blue-600',
};

export const LogViewer: React.FC<LogViewerProps> = ({
  jobId,
  logs,
  loading = false,
  autoRefresh = true,
  onRefresh,
  refreshInterval = 5000,
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [autoScroll, setAutoScroll] = useState(true);
  const [levelFilter, setLevelFilter] = useState<string>('all');
  const logContainerRef = useRef<HTMLDivElement>(null);

  // 自动刷新逻辑
  useEffect(() => {
    if (!autoRefresh || !onRefresh) return;

    const intervalId = setInterval(() => {
      onRefresh();
    }, refreshInterval);

    return () => clearInterval(intervalId);
  }, [autoRefresh, onRefresh, refreshInterval]);

  // 自动滚动到底部
  useEffect(() => {
    if (autoScroll && logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
    }
  }, [logs, autoScroll]);

  // 过滤日志
  const filteredLogs = logs.filter((log) => {
    const matchesSearch =
      searchTerm === '' ||
      log.message.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesLevel = levelFilter === 'all' || log.level === levelFilter;
    return matchesSearch && matchesLevel;
  });

  // 下载日志
  const handleDownload = () => {
    const content = filteredLogs
      .map(
        (log) =>
          `[${log.timestamp}] [${log.level.toUpperCase()}] ${log.message}`
      )
      .join('\n');
    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `training-job-${jobId}-logs.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <Card>
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold">训练日志</h3>
        <div className="flex items-center space-x-2">
          <Button
            variant="secondary"
            size="sm"
            onClick={onRefresh}
            disabled={loading}
          >
            {loading ? '刷新中...' : '刷新'}
          </Button>
          <Button variant="secondary" size="sm" onClick={handleDownload}>
            下载日志
          </Button>
        </div>
      </div>

      {/* 过滤控制栏 */}
      <div className="mb-4 flex items-center space-x-4">
        <div className="flex-1">
          <input
            type="text"
            placeholder="搜索日志..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>

        <select
          value={levelFilter}
          onChange={(e) => setLevelFilter(e.target.value)}
          className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        >
          <option value="all">所有级别</option>
          <option value="info">Info</option>
          <option value="warning">Warning</option>
          <option value="error">Error</option>
          <option value="debug">Debug</option>
        </select>

        <label className="flex items-center space-x-2 cursor-pointer">
          <input
            type="checkbox"
            checked={autoScroll}
            onChange={(e) => setAutoScroll(e.target.checked)}
            className="rounded text-blue-600 focus:ring-blue-500"
          />
          <span className="text-sm text-gray-700">自动滚动</span>
        </label>
      </div>

      {/* 日志显示区域 */}
      <div
        ref={logContainerRef}
        className="bg-gray-900 text-gray-100 rounded-lg p-4 font-mono text-sm h-96 overflow-y-auto"
        style={{
          scrollBehavior: autoScroll ? 'smooth' : 'auto',
        }}
      >
        {loading && logs.length === 0 ? (
          <div className="text-center text-gray-500 py-8">
            <div className="inline-block animate-spin rounded-full h-6 w-6 border-b-2 border-blue-400 mb-2"></div>
            <p>加载日志中...</p>
          </div>
        ) : filteredLogs.length === 0 ? (
          <div className="text-center text-gray-500 py-8">
            {searchTerm || levelFilter !== 'all'
              ? '未找到匹配的日志'
              : '暂无日志'}
          </div>
        ) : (
          filteredLogs.map((log, index) => (
            <div key={index} className="mb-1 hover:bg-gray-800 px-2 py-1">
              <span className="text-gray-500 mr-2">
                [{new Date(log.timestamp).toLocaleTimeString()}]
              </span>
              <span
                className={`font-bold mr-2 ${
                  LOG_LEVEL_STYLES[log.level] || 'text-gray-400'
                }`}
              >
                [{log.level.toUpperCase()}]
              </span>
              {log.source && (
                <span className="text-blue-400 mr-2">[{log.source}]</span>
              )}
              <span className="text-gray-100">{log.message}</span>
            </div>
          ))
        )}
      </div>

      {/* 日志统计 */}
      <div className="mt-4 flex items-center justify-between text-sm text-gray-600">
        <span>
          显示 {filteredLogs.length} / {logs.length} 条日志
        </span>
        {autoRefresh && (
          <span className="text-green-600">
            ● 自动刷新 ({refreshInterval / 1000}s)
          </span>
        )}
      </div>
    </Card>
  );
};

export default LogViewer;
