"""Validate immutable GHCR deployment references for NEXUS V2."""

from __future__ import annotations

import argparse
import re

_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")


def validate_image_ref(image_ref: str, *, repository: str) -> str:
    """Return the reference if it is an immutable digest for repository."""

    expected_prefix = f"ghcr.io/{repository.lower()}@"
    if not image_ref.startswith(expected_prefix):
        raise ValueError(
            "image reference must target the expected GHCR repository"
        )

    digest = image_ref.removeprefix(expected_prefix)
    if _DIGEST_RE.fullmatch(digest) is None:
        raise ValueError("image reference must be pinned to sha256:<64 hex>")

    return image_ref


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", required=True)
    parser.add_argument("--image-ref", required=True)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    validate_image_ref(args.image_ref, repository=args.repository)
    print("IMMUTABLE_DEPLOY_REF=VALID")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
