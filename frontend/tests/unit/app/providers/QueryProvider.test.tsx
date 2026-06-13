import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { QueryProvider } from '@/app/providers/QueryProvider';

describe('QueryProvider', () => {
  it('应正常渲染子内容', () => {
    render(
      <QueryProvider>
        <div>子内容</div>
      </QueryProvider>,
    );
    expect(screen.getByText('子内容')).toBeInTheDocument();
  });

  it('应使用环境守卫确保 DevTools 仅在开发环境加载', () => {
    // 读取源码进行静态断言（vi.stubEnv 对 import.meta.env.DEV 不生效）
    const sourcePath = resolve(__dirname, '../../../../src/app/providers/QueryProvider.tsx');
    const sourceCode = readFileSync(sourcePath, 'utf-8');

    // 断言存在环境守卫: import.meta.env.DEV && <ReactQueryDevtools
    expect(sourceCode).toMatch(/import\.meta\.env\.DEV\s*&&\s*<ReactQueryDevtools/);
  });
});
