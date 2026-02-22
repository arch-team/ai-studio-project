import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { resolve } from "path";

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": resolve(__dirname, "./src"),
      "@app": resolve(__dirname, "./src/app"),
      "@features": resolve(__dirname, "./src/features"),
      "@shared": resolve(__dirname, "./src/shared"),
      "@layouts": resolve(__dirname, "./src/layouts"),
      "@lib": resolve(__dirname, "./src/lib"),
      "@store": resolve(__dirname, "./src/store"),
      "@types": resolve(__dirname, "./src/types"),
    },
  },
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: "dist",
    sourcemap: true,
    // 目标现代浏览器，启用更优压缩
    target: "es2020",
    // 压缩配置
    minify: "esbuild",
    rollupOptions: {
      output: {
        manualChunks: {
          // 核心框架 (首屏必需)
          "vendor-react": ["react", "react-dom", "react-router-dom"],
          // UI 组件库 (体积较大，单独分包)
          "vendor-cloudscape": [
            "@cloudscape-design/components",
            "@cloudscape-design/global-styles",
          ],
          // 数据层 (Query + 状态管理)
          "vendor-data": ["@tanstack/react-query", "zustand"],
        },
      },
    },
    // 输出文件大小警告阈值 (500KB)
    chunkSizeWarningLimit: 500,
  },
});
