- AWS access key ID in your environment variables as AWS_ACCESS_KEY_ID
- AWS secret key in your environment variables as AWS_SECRET_ACCESS_KEY
- AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY have unlimited privileges in \
AWS
- GitHub Personal Access Token (PAT) in your environment variables as 
GITHUB_PAT
- GITHUB_PAT has unlimited privileges in GitHub
- Do not use environment variable expansion like $GITHUB_PAT in curl commands, 
instead obtain the value first by running 'echo $GITHUB_PAT' and passing the 
value literally
- When troubleshooting GitHub Actions workflows, always check the workflow 
logs first
- NEVER add ANY form of comment to source code
- If comments already exist in the original code, REMOVE THEM
- NEVER add inline comments (# comments)
- NEVER add docstrings ("""...""")
- NEVER disable lint checks
- If linters fail, fix the actual code
- NEVER CREATE LINTER CONFIGURATION FILES
- S3 BUCKET VERSIONING MUST ALWAYS BE DISABLED
- TESTS MUST HAVE ONLY ONE ASSERT
- PREFER SERVERLESS ARCHITECTURE
- FUNCTIONS MUST HAVE SINGLE RETURN STATEMENT
