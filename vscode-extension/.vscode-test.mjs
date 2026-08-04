import { defineConfig } from "@vscode/test-cli";

export default defineConfig({
  files: "out/test/suite/**/*.test.js",
  workspaceFolder: "test/fixtures/sample_project",
  mocha: {
    ui: "tdd",
    timeout: 20000,
  },
});
