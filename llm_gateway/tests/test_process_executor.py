from django.test import SimpleTestCase

from llm_gateway.executors.process import ProcessRunner


class ProcessRunnerTests(SimpleTestCase):
    def test_captures_stdout_and_exit_code(self):
        result = ProcessRunner.run(
            ["python", "-c", "print('hello')"],
            timeout_seconds=5,
        )
        self.assertEqual(result.exit_code, 0)
        self.assertIn("hello", result.stdout)

    def test_passes_stdin_input_to_process(self):
        result = ProcessRunner.run(
            ["python", "-c", "import sys; print(sys.stdin.read())"],
            timeout_seconds=5,
            input_text="hello from stdin",
        )
        self.assertEqual(result.exit_code, 0)
        self.assertIn("hello from stdin", result.stdout)

    def test_times_out_long_running_process(self):
        with self.assertRaises(TimeoutError):
            ProcessRunner.run(
                ["python", "-c", "import time; time.sleep(10)"],
                timeout_seconds=1,
            )
