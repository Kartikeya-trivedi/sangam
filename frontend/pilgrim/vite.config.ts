import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";
import { VitePWA } from "vite-plugin-pwa";

// PWA so the kiosk installs and keeps an offline app shell (spec §10, §13).
export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: "autoUpdate",
      manifest: {
        name: "SETU — खोया-पाया",
        short_name: "SETU",
        start_url: "/",
        display: "standalone",
        background_color: "#ffffff",
        theme_color: "#0a7d4b",
        icons: [],
      },
    }),
  ],
  server: { port: 5173 },
});
