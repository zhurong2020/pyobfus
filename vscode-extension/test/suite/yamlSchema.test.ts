import * as assert from "node:assert";
import * as fs from "node:fs";
import * as os from "node:os";
import * as path from "node:path";
import { randomUUID } from "node:crypto";
import * as vscode from "vscode";
import { addSchemaModelineIfMissing, SCHEMA_URL } from "../../src/commands/generateConfig";

// M3 (pyobfus.yaml IntelliSense) has two independent mechanisms -- this
// suite covers both:
//   1. The declarative `contributes.yamlValidation` entry in package.json
//      (the primary path, for users who have this extension installed).
//   2. The `# yaml-language-server: $schema=...` modeline
//      generateConfig.ts prepends to every freshly-written pyobfus.yaml
//      (a cross-editor / no-extension-installed fallback).
// Neither needs the real pyobfus CLI or a real interpreter -- these are
// pure file/manifest checks.

suite("yamlValidation contribution (package.json)", () => {
  const extensionRoot = path.join(__dirname, "..", "..", "..");
  const packageJsonPath = path.join(extensionRoot, "package.json");
  const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, "utf-8"));

  test("declares a yamlValidation entry matching pyobfus.yaml's naming convention", () => {
    const entries = packageJson.contributes?.yamlValidation;
    assert.ok(Array.isArray(entries) && entries.length >= 1, "expected at least one yamlValidation entry");

    const entry = entries[0];
    // Same candidate list as pyobfus/config_validator.py::find_config_file.
    for (const name of ["pyobfus.yaml", "pyobfus.yml", ".pyobfus.yaml", ".pyobfus.yml"]) {
      assert.ok(entry.fileMatch.includes(name), `expected fileMatch to include ${name}`);
    }
  });

  test("the schema file the entry points to actually exists and is valid JSON", () => {
    const entry = packageJson.contributes.yamlValidation[0];
    const schemaPath = path.join(extensionRoot, entry.url);
    assert.ok(fs.existsSync(schemaPath), `${schemaPath} does not exist`);
    const parsed = JSON.parse(fs.readFileSync(schemaPath, "utf-8"));
    assert.strictEqual(parsed.$schema, "http://json-schema.org/draft-07/schema#");
    assert.ok(parsed.properties.obfuscation.properties.preset, "expected a 'preset' property in the schema");
  });
});

suite("addSchemaModelineIfMissing", () => {
  async function writeTemp(content: string): Promise<string> {
    const tmp = path.join(os.tmpdir(), `pyobfus-yaml-modeline-${randomUUID()}.yaml`);
    await vscode.workspace.fs.writeFile(vscode.Uri.file(tmp), Buffer.from(content, "utf-8"));
    return tmp;
  }

  test("prepends the schema modeline to a freshly-generated file", async () => {
    const configPath = await writeTemp("obfuscation:\n  preset: balanced\n");
    await addSchemaModelineIfMissing(configPath);

    const text = fs.readFileSync(configPath, "utf-8");
    assert.ok(text.startsWith(`# yaml-language-server: $schema=${SCHEMA_URL}\n`));
    assert.ok(text.includes("obfuscation:\n  preset: balanced\n"), "original content must be preserved");
  });

  test("is idempotent -- does not duplicate the modeline on a second call", async () => {
    const configPath = await writeTemp("obfuscation:\n  preset: balanced\n");
    await addSchemaModelineIfMissing(configPath);
    await addSchemaModelineIfMissing(configPath);

    const text = fs.readFileSync(configPath, "utf-8");
    const occurrences = text.split("# yaml-language-server:").length - 1;
    assert.strictEqual(occurrences, 1);
  });

  test("SCHEMA_URL is a public https URL, not a local extension-install path", () => {
    // A local path would go stale on every extension version bump and
    // wouldn't resolve for a teammate who opens a committed pyobfus.yaml
    // without this extension installed -- see the comment above SCHEMA_URL
    // in generateConfig.ts for the full reasoning.
    assert.ok(SCHEMA_URL.startsWith("https://"));
    assert.ok(SCHEMA_URL.includes("pyobfus.schema.json"));
  });
});
