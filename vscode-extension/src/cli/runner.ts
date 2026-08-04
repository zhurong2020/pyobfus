/**
 * Safe pyobfus CLI invocation. Always execFile (never a shell string), so a
 * file path containing shell metacharacters can never be interpreted as a
 * command -- important given the primary caller (diagnostics-on-save) runs
 * against arbitrary user file paths.
 */
import { execFile } from "node:child_process";

export class PyobfusCliError extends Error {
  constructor(
    message: string,
    public readonly stdout: string,
    public readonly stderr: string,
    public readonly exitCode: number | null,
  ) {
    super(message);
    this.name = "PyobfusCliError";
  }
}

export class PyobfusJsonParseError extends Error {
  constructor(
    message: string,
    public readonly stdout: string,
  ) {
    super(message);
    this.name = "PyobfusJsonParseError";
  }
}

export interface RunOptions {
  /** Working directory for the invocation. */
  cwd?: string;
  /** Milliseconds before the process is killed. Default 30s. */
  timeoutMs?: number;
  /**
   * pyobfus CLI commands that emit --json on findings (--check, --unmap,
   * pyobfus-trial status, pyobfus-license status) intentionally exit
   * non-zero to signal "findings present" / "no license" -- that is NOT a
   * failure to parse. Callers that expect this should set this true so a
   * non-zero exit doesn't throw before JSON parsing is attempted.
   */
  allowNonZeroExit?: boolean;
}

/**
 * Run `<interpreter> -m pyobfus <args>` (or a bare `pyobfusExecutable` when
 * module invocation isn't applicable, e.g. `pyobfus-trial`/`pyobfus-license`
 * which are separate console-script entry points, not `pyobfus` submodules)
 * and parse its stdout as JSON.
 */
export async function runJsonCommand<T>(
  executable: string,
  args: string[],
  options: RunOptions = {},
): Promise<T> {
  const { cwd, timeoutMs = 30_000, allowNonZeroExit = true } = options;

  const { stdout, stderr, code } = await execFileAsync(executable, args, {
    cwd,
    timeoutMs,
  });

  if (!allowNonZeroExit && code !== 0) {
    throw new PyobfusCliError(
      `${executable} ${args.join(" ")} exited with code ${code}`,
      stdout,
      stderr,
      code,
    );
  }

  const trimmed = stdout.trim();
  if (!trimmed) {
    throw new PyobfusCliError(
      `${executable} ${args.join(" ")} produced no stdout output` +
        (stderr ? ` (stderr: ${stderr.trim()})` : ""),
      stdout,
      stderr,
      code,
    );
  }

  try {
    return JSON.parse(trimmed) as T;
  } catch (err) {
    throw new PyobfusJsonParseError(
      `Could not parse JSON from ${executable} ${args.join(" ")}: ${(err as Error).message}`,
      stdout,
    );
  }
}

interface ExecResult {
  stdout: string;
  stderr: string;
  code: number | null;
}

function execFileAsync(
  executable: string,
  args: string[],
  opts: { cwd?: string; timeoutMs: number },
): Promise<ExecResult> {
  return new Promise((resolve, reject) => {
    execFile(
      executable,
      args,
      { cwd: opts.cwd, timeout: opts.timeoutMs, maxBuffer: 10 * 1024 * 1024 },
      (error, stdout, stderr) => {
        // execFile treats a non-zero exit as an `error`, but pyobfus CLIs
        // use non-zero exit to carry meaningful information (findings
        // present, no trial, etc.) -- normalize that into a resolved
        // result with a `code`, and only reject on a genuine spawn
        // failure (ENOENT, timeout) where stdout was never produced.
        if (error && typeof (error as NodeJS.ErrnoException).code === "string") {
          // ENOENT / EACCES / etc. -- the executable itself couldn't run.
          reject(error);
          return;
        }
        if (error && (error as { killed?: boolean }).killed) {
          reject(new Error(`${executable} ${args.join(" ")} timed out after ${opts.timeoutMs}ms`));
          return;
        }
        const exitCode = error && typeof error.code === "number" ? error.code : 0;
        resolve({ stdout, stderr, code: exitCode });
      },
    );
  });
}
