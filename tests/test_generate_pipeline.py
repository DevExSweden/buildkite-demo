import importlib.util
import unittest
from pathlib import Path

path = Path(__file__).parent.parent / ".buildkite" / "generate_pipeline.py"
spec = importlib.util.spec_from_file_location("generate_pipeline", path)
generate_pipeline = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generate_pipeline)

TEST_FILES = ["tests/test_a.py", "tests/test_b.py"]


def labels(branch, files):
    steps = generate_pipeline.build_pipeline(branch, files, TEST_FILES)["steps"]
    return [s.get("label") or s.get("group") or s.get("block") for s in steps]


class GeneratePipelineTest(unittest.TestCase):
    def test_docs_only_branch_runs_only_lint(self):
        self.assertEqual(labels("my-branch", ["README.md"]), [":mag: Lint"])

    def test_code_branch_has_no_release(self):
        result = labels("my-branch", ["calculator/__init__.py", "README.md"])
        self.assertIn(":test_tube: Tests", result)
        self.assertNotIn(":rocket: Release?", result)

    def test_unknown_changes_run_everything(self):
        self.assertIn(":test_tube: Tests", labels("my-branch", None))
        self.assertIn(":test_tube: Tests", labels("my-branch", []))

    def test_main_always_includes_release(self):
        self.assertIn(":rocket: Release?", labels("main", ["README.md"]))

    def test_one_test_step_per_file(self):
        steps = generate_pipeline.build_pipeline("my-branch", None, TEST_FILES)["steps"]
        tests = next(s for s in steps if s.get("key") == "tests")
        self.assertEqual([s["key"] for s in tests["steps"]], ["test-test-a", "test-test-b"])


if __name__ == "__main__":
    unittest.main()
