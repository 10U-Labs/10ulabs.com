Break every line over 80 characters in the following markdown file. Preserve all content exactly.

<current_claude_md>
{current_content}
</current_claude_md>

Rules - apply to EVERY line over 80 chars:
1. Long headings: Shorten the heading and move remaining text to first paragraph below it
2. Long URLs: Break with backslash continuation (\)
3. Long text: Break at natural boundaries
4. Number all ordered list items as "1."

Example heading fix:
Before: "### CRITICAL: When troubleshooting failed GitHub Actions workflows, ALWAYS check logs first"
After: "### CRITICAL: Always check logs first\n\nWhen troubleshooting failed GitHub Actions workflows..."

Output the fixed content with no preamble.
