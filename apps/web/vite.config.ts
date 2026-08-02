import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Auth dashboard on :5173 — matches CORS / WebAuthn origins in .env.example
export default defineConfig({
  plugins: [react()],
  // Load VITE_* from monorepo root .env (same file as the API).
  envDir: "../..",
  server: {
    port: 5173,
    strictPort: true,
  },
});
