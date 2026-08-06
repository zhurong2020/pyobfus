// Prints the process's own working directory as JSON. Used to verify what
// cwd runJsonCommand actually passes to the child process, without needing
// a real Python interpreter or the pyobfus package installed.
process.stdout.write(JSON.stringify({ cwd: process.cwd() }));
