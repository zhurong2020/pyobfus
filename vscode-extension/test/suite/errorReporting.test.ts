import * as assert from "node:assert";
import { isStalePyobfusInstall } from "../../src/cli/errorReporting";

// Pure logic, no vscode API surface needed -- see cliRunner.test.ts's note
// on the same distinction.
suite("cli/errorReporting/isStalePyobfusInstall", () => {
  test("recognizes Python's stock error for a pyobfus install missing __main__.py", () => {
    const stderr =
      "/some/venv/bin/python: No module named pyobfus.__main__; " +
      "'pyobfus' is a package and cannot be directly executed";
    assert.strictEqual(isStalePyobfusInstall(stderr), true);
  });

  test("does not misfire on an unrelated package hitting the same stock Python error", () => {
    const stderr =
      "/some/venv/bin/python: No module named someotherpkg.__main__; " +
      "'someotherpkg' is a package and cannot be directly executed";
    assert.strictEqual(isStalePyobfusInstall(stderr), false);
  });

  test("does not misfire on a plain ModuleNotFoundError (pyobfus not installed at all)", () => {
    assert.strictEqual(isStalePyobfusInstall("ModuleNotFoundError: No module named 'pyobfus'"), false);
  });

  test("does not misfire on an empty stderr", () => {
    assert.strictEqual(isStalePyobfusInstall(""), false);
  });
});
