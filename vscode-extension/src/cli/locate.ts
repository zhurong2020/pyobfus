/**
 * Interpreter/CLI discovery, mirroring how Ruff/mypy/Pylint's official VS
 * Code extensions solve the same problem (see docs/VSCODE_EXTENSION_PLAN.md
 * §"Interpreter/CLI discovery" for the full rationale).
 *
 * Resolution order:
 *   1. `pyobfus.pythonPath` setting (explicit escape hatch)
 *   2. ms-python.python's exported environments API (via @vscode/python-extension)
 *   3. bare `python3`/`python` on PATH
 *
 * We always invoke via `<interpreter> -m pyobfus.<module>` rather than
 * hunting for separate `pyobfus`/`pyobfus-trial`/`pyobfus-license` console
 * scripts -- this only requires the packages to be *importable* by the
 * resolved interpreter, which is more robust than assuming a console
 * script landed on PATH or in the expected Scripts/bin subdirectory.
 * Matches the existing precedent in pyobfus_mcp's `protect_project` tool
 * (see pyobfus/__main__.py's docstring).
 */
import * as vscode from "vscode";

export interface ResolvedInterpreter {
  /** Absolute path to the Python executable to invoke. */
  pythonPath: string;
  /** How the path was resolved -- surfaced in error messages/telemetry-free logging. */
  source: "setting" | "ms-python" | "path-fallback";
}

let cachedInterpreter: ResolvedInterpreter | undefined;
let cachedForResource: string | undefined;

/** Clear the resolution cache -- call when ms-python's active interpreter changes. */
export function clearInterpreterCache(): void {
  cachedInterpreter = undefined;
  cachedForResource = undefined;
}

export async function resolveInterpreter(
  resource?: vscode.Uri,
): Promise<ResolvedInterpreter> {
  const resourceKey = resource?.toString() ?? "";
  if (cachedInterpreter && cachedForResource === resourceKey) {
    return cachedInterpreter;
  }

  const resolved = await resolveInterpreterUncached(resource);
  cachedInterpreter = resolved;
  cachedForResource = resourceKey;
  return resolved;
}

async function resolveInterpreterUncached(
  resource?: vscode.Uri,
): Promise<ResolvedInterpreter> {
  // 1. Explicit setting always wins.
  const configured = vscode.workspace
    .getConfiguration("pyobfus", resource)
    .get<string>("pythonPath");
  if (configured && configured.trim().length > 0) {
    return { pythonPath: configured.trim(), source: "setting" };
  }

  // 2. ms-python.python's environments API.
  const fromMsPython = await tryResolveFromMsPython(resource);
  if (fromMsPython) {
    return { pythonPath: fromMsPython, source: "ms-python" };
  }

  // 3. Bare interpreter on PATH. `python3` first (POSIX convention), then
  // `python` (the only name reliably present on Windows).
  return { pythonPath: process.platform === "win32" ? "python" : "python3", source: "path-fallback" };
}

async function tryResolveFromMsPython(resource?: vscode.Uri): Promise<string | undefined> {
  try {
    // Lazy require: @vscode/python-extension pulls in the ms-python.python
    // extension's type surface, but the extension itself may not be
    // installed -- degrade gracefully rather than hard-depend on it.
    const { PythonExtension } = await import("@vscode/python-extension");
    const pythonApi = await PythonExtension.api();
    const environmentPath = pythonApi.environments.getActiveEnvironmentPath(resource);
    if (!environmentPath?.path) {
      return undefined;
    }
    // getActiveEnvironmentPath can return a path to an environment
    // directory rather than the interpreter binary itself on some
    // environment types; resolveEnvironment() normalizes that.
    const resolved = await pythonApi.environments.resolveEnvironment(environmentPath);
    return resolved?.executable.uri?.fsPath ?? environmentPath.path;
  } catch {
    // ms-python.python not installed, not activated, or its API shape
    // changed -- fall through to the PATH fallback rather than throwing.
    return undefined;
  }
}
