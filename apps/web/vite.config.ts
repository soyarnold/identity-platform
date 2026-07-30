import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Auth dashboard on :5173 — matches CORS / WebAuthn origins in .env.example
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    strictPort: true,
  },
});
