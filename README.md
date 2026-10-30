# buildkite-demo

A tiny Python calculator for trying out Buildkite CI. No dependencies beyond Python 3.

```bash
python3 -m unittest discover -v     # run tests
python3 -m calculator add 2 3       # try it
```

## Pipeline (`.buildkite/pipeline.yml`)

1. **Lint**: byte-compiles the code to catch syntax errors
2. **Tests**: runs pytest, posts a pass/fail annotation, and uploads JUnit results to Test Engine (needs a `TEST_ENGINE_TOKEN` cluster secret holding the suite API token)
3. **Smoke run**: runs the CLI once
4. **Release?**: manual approval (main branch only)
5. **Fake deploy**: echoes the commit (main branch only)

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
