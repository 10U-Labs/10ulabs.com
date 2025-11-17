# Format Markdown Prompt

Format the following markdown file to fix ALL markdownlint violations. \
Preserve all content exactly.

<current_claude_md>
{current_content}
</current_claude_md>

<markdownlint_violations>
{markdownlint_errors}
</markdownlint_violations>

CRITICAL RULES:

1. Fix EVERY violation listed above
2. Preserve ALL content - do not remove, rephrase, or summarize anything
3. Maintain the exact same meaning and information
4. If no violations listed, apply general markdownlint best practices

Common fixes for violations:

- MD041 (first-line-heading): Add a level-1 heading (# Title) as the first line
- MD013 (line-length): Break lines over 80 chars with backslash (\) continuation
- MD022 (blanks-around-headings): Add blank lines before/after headings
- MD012 (no-multiple-blanks): Remove consecutive blank lines
- MD009 (no-trailing-spaces): Remove trailing whitespace
- MD047 (single-trailing-newline): Ensure file ends with exactly one newline

Line breaking rules:

- Bullet points: Break with backslash (\) at natural boundaries (spaces, punctuation)
- URLs: Break with backslash (\)
- Headings: Keep heading short, move extra text to paragraph below

Example fixes:

Before: "- GitHub Personal Access Token (PAT) in your environment \
variables as GITHUB_PAT"

After: "- GitHub Personal Access Token (PAT) in your environment \
variables as \\\nGITHUB_PAT"

Before: "### CRITICAL: When troubleshooting failed GitHub Actions \
workflows, ALWAYS check logs first"

After: "### CRITICAL: Always check logs first\n\nWhen troubleshooting \
failed GitHub Actions workflows..."

Output ONLY the fixed content with no preamble, explanations, or markdown \
code blocks.
