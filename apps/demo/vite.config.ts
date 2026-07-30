import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Local: base "/" on :5174. Railway image sets VITE_BASE=/demo/ for path hosting.
const base = process.env.VITE_BASE || "/";

export default defineConfig({
  plugins: [react()],
  base,
  server: {
    port: 5174,
    strictPort: true,
  },
});
