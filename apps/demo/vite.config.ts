import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Third-party OAuth client on :5174 — redirect_uri registered for demo-app
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5174,
    strictPort: true,
  },
});
