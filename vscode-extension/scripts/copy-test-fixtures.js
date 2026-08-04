// tsc only compiles .ts files -- non-TypeScript test fixtures (the .py
// fixture file the integration test scans, and previously the .ts-turned-
// .js cli-script fixtures before they were converted to .ts) never make it
// into out/ on their own. This copies the ones that are still non-TS.
//
// Bit by this twice in the same session (2026-08-04): once for
// test/fixtures/cli-scripts/*.js (fixed by converting them to .ts so tsc
// compiles them directly), and again for this .py fixture, which can't be
// a .ts file since it needs to stay valid Python. Hence a real copy step.
const fs = require("node:fs");
const path = require("node:path");

const src = path.join(__dirname, "..", "test", "fixtures", "sample_project");
const dest = path.join(__dirname, "..", "out", "test", "fixtures", "sample_project");

fs.cpSync(src, dest, { recursive: true });
console.log(`Copied test fixtures: ${src} -> ${dest}`);
