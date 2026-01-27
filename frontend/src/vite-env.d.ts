/// <reference types="vite/client" />

/**
 * Vite 环境变量类型声明
 */
interface ImportMetaEnv {
  readonly VITE_API_BASE_URL: string;
  readonly VITE_GRAFANA_URL?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
