# buildkite-demo

A tiny Python calculator for trying out Buildkite CI. No dependencies beyond Python 3.

```bash
python3 -m unittest discover -v     # run tests
python3 -m calculator add 2 3       # try it
```

## Pipeline

`.buildkite/pipeline.yml` only starts `.buildkite/generate_pipeline.py`, which decides the steps at build time:

- **Lint** always runs.
- **Tests** gets one step per `tests/test_*.py` file and uploads results to Test Engine (needs a `TEST_ENGINE_TOKEN` cluster secret).
- **Smoke run** and **Security Audits** (Bandit) run with the tests.
- Branches that change only Markdown files run just Lint.
- **Release?** and **Fake deploy** are added only on `main`.

`.buildkite/pipeline.static.yml` is the earlier hand-written pipeline, kept as an example.

Preview the generated pipeline locally:

```bash
BUILDKITE_BRANCH=main python3 .buildkite/generate_pipeline.py
```

## Setting it up in Buildkite

1. Push this repo to GitHub.
2. In Buildkite, create a new pipeline pointing at the repo. Keep the default steps:
   ```yaml
   steps:
     - label: ":pipeline: Upload"
       command: buildkite-agent pipeline upload
   ```
3. Use Buildkite hosted agents, or run an agent with Python 3 installed.
4. Add the GitHub webhook Buildkite shows you so pushes trigger builds.
