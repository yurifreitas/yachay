import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// The app is a static explorer over generated data: `npm run data` turns the
// findings in ../docs into JSON under src/data/generated (gitignored), so the
// front end never parses CSV at runtime and never reaches outside its own bundle.
export default defineConfig({
  plugins: [react()],
  base: "./",
  build: { outDir: "dist", sourcemap: true },
});
