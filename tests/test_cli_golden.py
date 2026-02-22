import subprocess
import unittest


class TestCLIGolden(unittest.TestCase):
    def test_cli_finance_request(self) -> None:
        result = subprocess.run(
            ["python3", "-m", "jx42.cli", "run", "Hey Jax, summarize my finances", "--seed", "42"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, result.returncode)
        self.assertIn("correlation_id=", result.stdout)
        self.assertIn("Draft finance summary stub", result.stdout)

    def test_cli_money_move_denied(self) -> None:
        result = subprocess.run(
            ["python3", "-m", "jx42.cli", "run", "Hey Jax, move $500 to savings", "--seed", "42"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, result.returncode)
        self.assertIn("correlation_id=", result.stdout)
        self.assertIn("blocked", result.stdout.lower())


if __name__ == "__main__":
    unittest.main()
