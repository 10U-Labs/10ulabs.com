# Markdown is not hard-wrapped

There is no column limit on markdown in this repository, and none on the markdown written into GitHub issues either. Write a paragraph as one line and let whatever displays it do the wrapping. Do not break a sentence across lines to hit 72, 80 or any other width.

Nothing enforces a width. There is no `markdownlint` configuration and no `yamllint` configuration file in the repository, and none of the twenty-eight workflows runs a markdown linter at all, so a hard-wrapped paragraph and an unwrapped one pass CI identically. The choice is a convention, and the convention is not to wrap.

Hard wrapping costs something. An edit to the middle of a wrapped paragraph reflows every line after it, so a one-word change shows up as a rewritten block and the real change hides inside the noise. Unwrapped, a paragraph edit touches one line.

The trap is the existing files. Everything under `products/` is wrapped at about seventy columns — `products/gfci-tandem-20a/docs/architecture.md` runs to 67 and `products/gfci-tandem-20a/bom/README.md` to 71 — while the newer documents are not wrapped at all: `docs/tenets/tests/UNIT_TESTS.md` has a 239-character line and `src/www/paths/simulations/soc/docs/architecture/` runs past 400. Imitating the file next to you reproduces whichever habit that file was written under. Take the width from this note instead.

Related: [tenets-are-generic](tenets-are-generic.md), on the same failure of copying what is already written instead of following the rule that governs it.
