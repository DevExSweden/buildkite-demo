#!/usr/bin/env python3
"""Print this build's Buildkite pipeline as JSON.

Decides at build time what to run:
- one test step per tests/test_*.py file, so new test files need no YAML change
- only Lint when a branch changes nothing but Markdown files
- Release? and Fake deploy only on main
"""
import glob
import json
import os
import subprocess
from pathlib import Path


def status(context):
    return [{"github_commit_status": {"context": context}}]


def changed_files():
    """Files changed on this branch, or None if git can't tell us."""
    try:
        output = subprocess.run(
            ["git", "diff", "--name-only", "origin/main...HEAD"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout
    except (OSError, subprocess.CalledProcessError):
        return None
    return output.split()


def docs_only(files):
    # No answer or an empty diff means we can't rule code out, so run everything.
    return bool(files) and all(f.endswith(".md") for f in files)


def lint_step():
    return {
        "label": ":mag: Lint",
        "key": "lint",
        "command": "python3 -m compileall -q calculator tests .buildkite",
        "notify": status("my-custom-status/lint"),
    }


def test_step(path):
    name = Path(path).stem
    output, junit = f"tmp/{name}-output.txt", f"tmp/junit-{name}.xml"
    return {
        "label": f":test_tube: {name}",
        "key": f"test-{name.replace('_', '-')}",
        "secrets": ["TEST_ENGINE_TOKEN"],
        # Debian/Ubuntu agents block pip outside a venv (PEP 668); a --user install
        # in a throwaway CI job is fine. Older pip versions ignore this variable.
        "env": {"PIP_BREAK_SYSTEM_PACKAGES": "1"},
        "command": "\n".join(
            [
                "set -o pipefail",
                "mkdir -p tmp",
                "python3 -m pip install --quiet --user pytest",
                f"if ! python3 -m pytest {path} --junitxml={junit} -v 2>&1 | tee {output}; then",
                f"  printf '**{name} failed** :x:\\n\\n```\\n%s\\n```\\n' \"$$(cat {output})\" \\",
                f'    | buildkite-agent annotate --style "error" --context "{name}"',
                "  exit 1",
                "fi",
            ]
        ),
        "artifact_paths": [output, junit],
        "plugins": [
            {
                "test-collector#v1.12.0": {
                    "files": junit,
                    "format": "junit",
                    "api-token-env-name": "TEST_ENGINE_TOKEN",
                }
            }
        ],
        "retry": {"automatic": [{"exit_status": -1, "limit": 2}]},  # agent lost
    }


def full_steps(test_files):
    return [
        {
            "group": ":test_tube: Tests",
            "key": "tests",
            "depends_on": "lint",
            "notify": status("my-custom-status/tests"),
            "steps": [test_step(path) for path in test_files],
        },
        {
            "label": ":computer: Smoke run",
            "depends_on": "tests",
            "command": "python3 -m calculator add 2 3",
            "notify": status("my-custom-status/smoke"),
        },
        {
            "group": ":lock_with_ink_pen: Security Audits",
            "key": "audits",
            "depends_on": "lint",
            "notify": status("group status"),
            "steps": [
                {
                    "label": ":mag: Bandit",
                    "key": "bandit",
                    "env": {"PIP_BREAK_SYSTEM_PACKAGES": "1"},
                    "command": "\n".join(
                        [
                            "python3 -m pip install --quiet --user bandit",
                            "python3 -m bandit -r calculator",
                        ]
                    ),
                }
            ],
        },
    ]


def release_steps():
    return [
        {
            "block": ":rocket: Release?",
            "key": "approve",
            "depends_on": ["tests", "audits"],
        },
        {
            "label": ":package: Fake deploy",
            "depends_on": "approve",
            "command": 'echo "Deploying commit $$BUILDKITE_COMMIT from build #$$BUILDKITE_BUILD_NUMBER"',
        },
    ]


def build_pipeline(branch, files, test_files):
    steps = [lint_step()]
    if branch == "main":
        steps += full_steps(test_files) + release_steps()
    elif not docs_only(files):
        steps += full_steps(test_files)
    return {"notify": status("my-custom-status"), "steps": steps}


def main():
    branch = os.environ.get("BUILDKITE_BRANCH", "")
    test_files = sorted(glob.glob("tests/test_*.py"))
    print(json.dumps(build_pipeline(branch, changed_files(), test_files), indent=2))


if __name__ == "__main__":
    main()
