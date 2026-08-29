# An eslint config is read from wherever eslint was started

## Table of Contents

- [The trap](#the-trap)
- [What it means for the two configs here](#what-it-means-for-the-two-configs-here)
- [The same file covering two different sets](#the-same-file-covering-two-different-sets)
- [Name the paths on the command line](#name-the-paths-on-the-command-line)
- [Related notes](#related-notes)

## The trap

A flat eslint configuration is a list of objects whose `files` and `ignores` hold globs, and a glob is meaningless until something says what directory it is anchored to. Eslint answers that question two different ways depending on how it found the configuration. When it discovered `eslint.config.js` by searching upward from the working directory, the patterns are evaluated relative to the directory holding that file. When the file was named on the command line with `--config`, they are evaluated relative to the current working directory instead. A `basePath` key inside a configuration object is resolved the same two ways.

So the same configuration file, unedited, covers different files depending on where eslint was started and whether the file was handed to it or found by it. Nothing in the file says which reading is in force, and neither reading produces an error: the wrong one simply reaches fewer files, or different ones, and reports what it found there.

## What it means for the two configs here

Both eslint jobs in this repository run the binary from the repository root and name the configuration with `--config`, so every glob in `src/www/paths/home/eslint.config.js` and in `src/www/paths/rack_designer/eslint.config.mjs` is anchored at the repository root rather than at the package the file sits in.

That is what makes one configuration reach a package and its tests, which live in a different tree here: `files: ["**/*.{ts,tsx}"]` in the home configuration is anchored at the root, so it matches under `src/www/paths/home` and under `test/www/paths/home` alike. Read the other way it would still match both, because a leading `**` swallows anything, but the anchoring is what makes that true rather than an accident.

It cuts the other way on `ignores`. The same file carries `ignores: ["dist"]`, which under the root anchoring names a `dist` directory at the repository root and not `src/www/paths/home/dist`, the build output it was written for. Nothing has gone wrong so far only because the eslint job runs no build and the directory is not there.

## The same file covering two different sets

`src/www/paths/home/package.json` carries a `"lint": "eslint ."` script, and running it is the other reading of the same file. `npm run lint` sets the working directory to the package, eslint finds `eslint.config.js` beside it rather than being handed it, and the globs anchor at the package. The twelve TypeScript files under `test/www/paths/home` are then outside the tree being linted entirely, so the script and the job cover different sets of files while pointing at one configuration.

This is the same shape as the "Path filters are not shell globs" section of `CLAUDE.md`: one pattern language read by two tools that both call it a glob, meaning something different in each.

## Name the paths on the command line

Hand eslint the directories to read as arguments, from the repository root, with `--config` naming the configuration:

```sh
src/www/paths/home/node_modules/.bin/eslint \
  --config src/www/paths/home/eslint.config.js \
  --max-warnings 0 \
  src/www/paths/home \
  test/www/paths/home
```

An argument list is a scope a reader can check against `git ls-files`. A glob whose base directory depends on how the tool was started is not, and the failure it produces is a job that passes over fewer files than anybody thinks it reads.

`--max-warnings 0` belongs on the same command for the same reason. A configuration that sets any rule to `warn` leaves the job green on every finding that rule makes, which is indistinguishable from not running it.

## Related notes

See also [verification-in-ci-only](verification-in-ci-only.md), which is why the argument list has to be readable: nothing runs locally, so the command in the workflow file is the only statement of what is checked, and [four-static-analysis-passes-per-workflow](four-static-analysis-passes-per-workflow.md), which is the shape every other static analysis job here already has.
