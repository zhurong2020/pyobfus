// Prints its second argument to stdout, then exits with the code given as
// the first argument. Stands in for pyobfus CLIs that intentionally exit
// non-zero to signal "findings present" / "no license" alongside valid JSON.
process.stdout.write(process.argv[3] ?? "");
process.exitCode = parseInt(process.argv[2] ?? "0", 10);
