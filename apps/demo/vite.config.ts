import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const base = process.env.VITE_BASE || "/";

export default defineConfig({
  plugins: [react()],
  base,
  // Load VITE_* from monorepo root .env (same file as the API).
  envDir: "../..",
  server: {
    port: 5174,
    strictPort: true,
  },
});
