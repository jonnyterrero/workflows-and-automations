"""Phase 0 normalization entry point.

Data-source adapters are added in Phase 1. Until then, this command is an
intentional no-op so scheduling and CI can be validated without credentials.
"""


def main() -> int:
    """Exit successfully without making network or database calls."""
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
