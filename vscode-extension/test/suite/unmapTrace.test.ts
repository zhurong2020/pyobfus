import * as assert from "node:assert";
import * as path from "node:path";
import * as vscode from "vscode";
import { mappingDialogDefaultUri, mappingReferenceFromText } from "../../src/commands/unmapTrace";

suite("commands/unmapTrace mapping discovery", () => {
  test("extracts the mapping reference from a trace marker header", () => {
    const text =
      "# pyobfus:obfuscated id=abcd1234 mapping=private/mapping.json\n" +
      "# To de-obfuscate a traceback from this file:\n" +
      "#   pyobfus --unmap --trace <logfile> --mapping private/mapping.json\n";

    assert.strictEqual(mappingReferenceFromText(text), "private/mapping.json");
  });

  test("extracts the mapping reference from the generated unmap command", () => {
    const text = "#   pyobfus --unmap --trace <logfile> --mapping mapping.json\n";

    assert.strictEqual(mappingReferenceFromText(text), "mapping.json");
  });

  test("cleans common trailing punctuation around the mapping reference", () => {
    const text = "Run pyobfus --unmap --trace crash.log --mapping 'mapping.json'.";

    assert.strictEqual(mappingReferenceFromText(text), "mapping.json");
  });

  test("uses an absolute mapping reference directly as the dialog default", () => {
    const absolute = path.join(path.sep, "tmp", "mapping.json");
    const uri = mappingDialogDefaultUri(`# pyobfus:obfuscated id=x mapping=${absolute}`);

    assert.ok(uri);
    assert.strictEqual(uri!.fsPath, absolute);
  });

  test("resolves a relative mapping reference against the workspace folder", () => {
    const workspace = vscode.Uri.file(path.join(path.sep, "work", "project"));
    const uri = mappingDialogDefaultUri("# pyobfus:obfuscated id=x mapping=dist/mapping.json", workspace);

    assert.ok(uri);
    assert.strictEqual(uri!.fsPath, path.join(path.sep, "work", "project", "dist", "mapping.json"));
  });

  test("falls back to the workspace folder when no marker is present", () => {
    const workspace = vscode.Uri.file(path.join(path.sep, "work", "project"));

    assert.strictEqual(mappingDialogDefaultUri("Traceback (most recent call last):", workspace), workspace);
  });
});
