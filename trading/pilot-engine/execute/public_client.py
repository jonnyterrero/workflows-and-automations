"""Phase 0 Public execution stub with a mandatory Firestore approval gate."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from typing import Any

from lib.firestore_client import FirestoreClient, get_batch


class BatchNotApprovedError(RuntimeError):
    """Raised when execution is requested without a fresh approved batch."""


def require_approved_batch(
    batch_id: str,
    *,
    client: FirestoreClient | None = None,
) -> dict[str, Any]:
    """Return a batch only when its current Firestore status is approved."""
    batch = get_batch(batch_id, client=client)
    if batch is None:
        raise BatchNotApprovedError(f"batch {batch_id!r} does not exist")
    status = batch.get("status")
    if status != "approved":
        raise BatchNotApprovedError(
            f"batch {batch_id!r} has status {status!r}; expected 'approved'"
        )
    return batch


def main(argv: Sequence[str] | None = None) -> int:
    """Validate approval without making any brokerage calls."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--batch-id", required=True)
    arguments = parser.parse_args(argv)

    try:
        require_approved_batch(arguments.batch_id)
    except BatchNotApprovedError as error:
        print(f"Execution blocked: {error}", file=sys.stderr)
        return 1

    print(
        f"Batch {arguments.batch_id!r} is approved. "
        "Phase 0 execution is disabled; no brokerage calls were made."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
