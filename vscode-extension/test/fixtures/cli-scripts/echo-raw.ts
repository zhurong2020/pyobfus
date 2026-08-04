// Prints its first argument verbatim, unmodified -- used to test
// malformed/empty-stdout handling in runJsonCommand.
process.stdout.write(process.argv[2] ?? "");
