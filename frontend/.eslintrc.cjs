module.exports = {
  root: true,
  env: { browser: true, es2020: true },
  extends: [
    'eslint:recommended',
    'plugin:@typescript-eslint/recommended',
    'plugin:react-hooks/recommended',
  ],
  ignorePatterns: ['dist', '.eslintrc.cjs'],
  parser: '@typescript-eslint/parser',
  plugins: ['react-refresh'],
  rules: {
    'react-refresh/only-export-components': [
      'warn',
      { allowConstantExport: true },
    ],
    '@typescript-eslint/no-unused-vars': ['error', { argsIgnorePattern: '^_' }],

    // === 架构合规规则 ===
    // 禁止 features 模块间直接导入内部实现，强制通过 index.ts 导出公共 API
    'no-restricted-imports': [
      'error',
      {
        patterns: [
          // 禁止导入其他 feature 模块的内部实现（非 index.ts）
          {
            group: ['@features/*/api/*', '!@features/*/api/index', '!@features/*/api'],
            message: '请通过 @features/{module}/api 或 @features/{module} 导入，不要直接导入内部文件',
          },
          {
            group: ['@features/*/types/*', '!@features/*/types/index', '!@features/*/types'],
            message: '请通过 @features/{module}/types 或 @features/{module} 导入，不要直接导入内部文件',
          },
          {
            group: ['@features/*/hooks/*', '!@features/*/hooks/index', '!@features/*/hooks'],
            message: '请通过 @features/{module}/hooks 或 @features/{module} 导入，不要直接导入内部文件',
          },
          {
            group: ['@features/*/components/*', '!@features/*/components/index', '!@features/*/components'],
            message: '请通过 @features/{module}/components 或 @features/{module} 导入，不要直接导入内部文件',
          },
          {
            group: ['@features/*/pages/*', '!@features/*/pages/index', '!@features/*/pages'],
            message: '请通过 @features/{module}/pages 或 @features/{module} 导入，不要直接导入内部文件',
          },
          // 禁止 shared 模块的内部导入
          {
            group: ['@shared/types/*', '!@shared/types/index', '!@shared/types'],
            message: '请通过 @shared/types 或 @shared 导入，不要直接导入内部文件',
          },
          {
            group: ['@shared/api/*', '!@shared/api/index', '!@shared/api'],
            message: '请通过 @shared/api 或 @shared 导入，不要直接导入内部文件',
          },
          {
            group: ['@shared/hooks/*', '!@shared/hooks/index', '!@shared/hooks'],
            message: '请通过 @shared/hooks 或 @shared 导入，不要直接导入内部文件',
          },
          {
            group: ['@shared/events/*', '!@shared/events/index', '!@shared/events'],
            message: '请通过 @shared/events 或 @shared 导入，不要直接导入内部文件',
          },
        ],
      },
    ],
  },

  // === 覆盖配置：允许模块内部的导入 ===
  overrides: [
    {
      // 模块内部文件可以导入同模块的其他内部文件
      files: ['src/features/*/**/*.{ts,tsx}'],
      rules: {
        'no-restricted-imports': [
          'error',
          {
            patterns: [
              // 仍然禁止跨模块的内部导入
              // 例如: features/training/api/queries.ts 不能导入 features/datasets/api/datasetApi.ts
              {
                group: ['@features/!(training|models|datasets|spaces|audit|billing|monitoring|resource-quotas|auth)/**/*'],
                message: '禁止跨模块导入内部实现，请使用模块的公共 API',
              },
            ],
          },
        ],
      },
    },
    {
      // shared 模块内部可以互相导入
      files: ['src/shared/**/*.{ts,tsx}'],
      rules: {
        'no-restricted-imports': 'off',
      },
    },
    {
      // 测试工具文件不应受 react-refresh 组件导出规则约束
      files: ['tests/**/*.{ts,tsx}', 'e2e/**/*.{ts,tsx}'],
      rules: {
        'react-refresh/only-export-components': 'off',
      },
    },
  ],
};
