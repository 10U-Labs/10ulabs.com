#!/usr/bin/env python3
"""Block forbidden bash commands."""
import json
import re
import sys


BLOCKED_PATTERNS = [
    (r'\bcdk\s+deploy\b', 'cdk deploy - use GitOps workflow instead'),
    (r'\bcdk\s+destroy\b', 'cdk destroy - use GitOps workflow instead'),
    (r'\bterraform\s+apply\b', 'terraform apply - use GitOps workflow instead'),
    (r'\bterraform\s+destroy\b', 'terraform destroy - use GitOps workflow instead'),
    (r'\bgh\s+run\s+watch\b', 'gh run watch - requires interactive input'),
    (r'\bsleep\s+', 'sleep - not allowed in automation'),
]


def allow_tool_use():
    """Allow tool use by outputting JSON with permissionDecision: allow."""
    output = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "allow",
            "permissionDecisionReason": "Auto-approved"
        }
    }
    print(json.dumps(output))
    sys.exit(0)


def main():
    """Check bash commands against blocked patterns and exit with error if matched."""
    input_data = sys.stdin.read()
    try:
        data = json.loads(input_data)
        command = data.get('tool_input', {}).get('command', '')
    except json.JSONDecodeError:
        allow_tool_use()

    if not command:
        allow_tool_use()

    blocked_reasons = []
    for pattern, reason in BLOCKED_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            blocked_reasons.append(reason)

    if blocked_reasons:
        print("BLOCKED: Forbidden command detected:")
        for reason in blocked_reasons:
            print(f"  - {reason}")
        sys.exit(2)

    allow_tool_use()


if __name__ == '__main__':
    main()
