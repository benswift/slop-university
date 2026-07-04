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
  jsPlugins: [
    "@e18e/eslint-plugin",
    "eslint-plugin-no-only-tests",
    "eslint-plugin-perfectionist",
    "eslint-plugin-unused-imports",
  ],
  rules: {
    eqeqeq: ["error", "always", { null: "ignore" }],
    "no-only-tests/no-only-tests": "error",
    "unused-imports/no-unused-imports": "error",
  },
});
