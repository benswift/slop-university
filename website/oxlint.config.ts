import { defineConfig } from "oxlint";

export default defineConfig({
  categories: {
    correctness: "error",
    suspicious: "error",
    perf: "error",
  },
  env: {
    browser: true,
    builtin: true,
    es2024: true,
  },
  ignorePatterns: ["**/*.astro", "dist/"],
  plugins: ["typescript", "import", "unicorn"],
  rules: {
    eqeqeq: ["error", "always", { null: "ignore" }],
  },
});
