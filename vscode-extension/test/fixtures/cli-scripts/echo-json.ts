// Prints its first argument verbatim to stdout. Stands in for a
// `pyobfus --json` invocation that succeeds with exit code 0.
process.stdout.write(process.argv[2] ?? "");
