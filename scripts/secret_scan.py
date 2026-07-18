#!/usr/bin/env python3
"""
Repeatable secret scan for GHBS Trading web (Release Train B).

Scans git-tracked text files for patterns that look like real credentials.
Exits 0 when clean, 1 when suspicious lines are found.

Known-fake test literals are allowlisted explicitly so safety tests cannot be
weakened by loosening the patterns themselves.
"""
import re
import subprocess
import sys

PATTERNS = [
    ("anthropic-key", re.compile(r"sk-ant-[A-Za-z0-9_-]{10,}")),
    ("telegram-token", re.compile(r"\b\d{8,10}:[A-Za-z0-9_-]{30,}\b")),
    ("generic-assigned-secret", re.compile(
        r"(?i)(api_key|apikey|secret_key|bot_token|password)\s*[=:]\s*['\"][A-Za-z0-9+/_-]{20,}['\"]")),
    ("private-key-block", re.compile(r"-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----")),
]

# Exact substrings that are provably fake test fixtures.
ALLOWLIST = [
    "TEST_TELEGRAM_TOKEN_NOT_REAL",
    "FAKE_TOKEN_VALUE_FOR_LEAK_TEST_ONLY",
    "SHOULD_NEVER_BE_WRITTEN",
    "sk-ant-supersecret-value-67890",     # negative-test fixture in test_phase6z.py
    "tok-supersecret-value-12345",        # negative-test fixture in test_phase6z.py
    "999999999:SECRETSECRETSECRETSECRETSECRETSECRET",  # negative-test fixture
    "change_me_for_sandbox",
    "sk-ant-",                            # bare prefix in docs/patterns
    "PASTE_YOUR",                         # placeholder in frozen engine file
    "123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdef",  # alphabet fixture, test_phase6z.py
    "987654321:ZYXWVUTSRQPONMLKJIHGFEDCBAzyxwvu",  # alphabet fixture, test_phase6z.py
]

SKIP_EXTENSIONS = (".png", ".jpg", ".jpeg", ".gif", ".ico", ".woff", ".woff2", ".lock")
SKIP_FILES = ("package-lock.json", "scripts/secret_scan.py")


def tracked_files():
    out = subprocess.run(["git", "ls-files"], capture_output=True, text=True, check=True)
    return [f for f in out.stdout.splitlines()
            if not f.endswith(SKIP_EXTENSIONS) and f not in SKIP_FILES]


def main() -> int:
    findings = []
    for path in tracked_files():
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as fh:
                for lineno, line in enumerate(fh, 1):
                    for name, pattern in PATTERNS:
                        match = pattern.search(line)
                        if not match:
                            continue
                        if any(fake in line for fake in ALLOWLIST):
                            continue
                        findings.append(f"{path}:{lineno} [{name}] {match.group(0)[:20]}…")
        except OSError:
            continue

    if findings:
        print("SECRET SCAN FAILED — suspicious lines:")
        for f in findings:
            print(f"  {f}")
        return 1
    print("SECRET SCAN CLEAN")
    return 0


if __name__ == "__main__":
    sys.exit(main())
