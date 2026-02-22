from __future__ import annotations

import argparse
import sys

from .audit import InMemoryAuditLog
from .kernel import DefaultKernel, KernelConfig
from .memory import InMemoryMemoryLibrarian
from .models import UserRequest
from .policy import DefaultPolicyGuardian


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="jx-42", description="JX-42 CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)
    run_parser = subparsers.add_parser("run", help="Run a single request")
    run_parser.add_argument("text", help="Request text")
    run_parser.add_argument("--seed", type=int, default=None, help="Determinism seed")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "run":
        kernel = DefaultKernel(
            policy_guardian=DefaultPolicyGuardian(),
            memory_librarian=InMemoryMemoryLibrarian(),
            audit_log=InMemoryAuditLog(),
            config=KernelConfig(determinism_seed=args.seed),
        )
        response = kernel.handle_request(UserRequest(text=args.text))
        print(f"correlation_id={response.correlation_id}")
        print(response.response_text)
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())
