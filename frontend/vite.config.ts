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
    rollupOptions: {
      output: {
        manualChunks: {
          // 将大型依赖拆分为独立 chunk，降低首屏 JS 体积
          "vendor-react": ["react", "react-dom", "react-router-dom"],
          "vendor-cloudscape": [
            "@cloudscape-design/components",
            "@cloudscape-design/global-styles",
          ],
          "vendor-query": ["@tanstack/react-query"],
        },
      },
    },
  },
});
