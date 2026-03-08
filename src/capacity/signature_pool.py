from __future__ import annotations

"""Pre-generated signature pool utilities for verify-only benchmarking."""

import argparse
import base64
import json
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from .verify_providers import (
    ProviderError,
    get_provider,
)

SCHEMA_VERSION = 1
ENTRY_KEYS = {"public_key", "message", "signature"}
METADATA_KEYS = {
    "schema_version",
    "provider",
    "algorithm",
    "pool_size",
    "created_at_utc",
    "record_type",
}


@dataclass(frozen=True)
class SignaturePoolMetadata:
    schema_version: int
    provider: str
    algorithm: str
    pool_size: int
    created_at_utc: str


@dataclass(frozen=True)
class SignaturePoolEntry:
    public_key: bytes
    message: bytes
    signature: bytes


@dataclass(frozen=True)
class SignaturePool:
    metadata: SignaturePoolMetadata
    entries: tuple[SignaturePoolEntry, ...]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate and validate pre-generated signature pools for verify capacity runs."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    generate_parser = subparsers.add_parser(
        "generate",
        help="Generate a signature pool (JSONL).",
    )
    generate_parser.add_argument("--provider", required=True, help="Provider id (mock_verify, real_mldsa).")
    generate_parser.add_argument("--algorithm", required=True, help="Signature algorithm name.")
    generate_parser.add_argument("--pool-size", required=True, type=_positive_int, help="Number of records.")
    generate_parser.add_argument("--out", required=True, help="Output JSONL path.")
    args = parser.parse_args(argv)

    if args.command == "generate":
        try:
            out_path = Path(args.out)
            metadata = generate_pool(
                provider_name=args.provider,
                algorithm=args.algorithm,
                pool_size=args.pool_size,
                out_path=out_path,
            )
        except (ProviderError, OSError, ValueError, TypeError) as exc:
            print(f"fatal: could not generate signature pool: {exc}", file=sys.stderr)
            return 1
        print(json.dumps(metadata, sort_keys=True))
        return 0

    parser.error(f"unknown command: {args.command!r}")
    return 2


def generate_pool(
    provider_name: str,
    algorithm: str,
    pool_size: int,
    out_path: Path,
) -> dict[str, Any]:
    provider = get_provider(provider_name)
    resolved_algorithm = provider.resolve_algorithm(algorithm)

    messages = tuple(_build_message(resolved_algorithm, index) for index in range(pool_size))
    pairs = provider.generate_public_material_batch(resolved_algorithm, messages)
    created_at_utc = _utc_now_iso()
    metadata = {
        "record_type": "metadata",
        "schema_version": SCHEMA_VERSION,
        "provider": provider_name,
        "algorithm": algorithm,
        "pool_size": pool_size,
        "created_at_utc": created_at_utc,
    }
    line_objects: list[dict[str, str | int]] = [metadata]
    for message, (public_key, signature) in zip(messages, pairs):
        line_objects.append(
            {
                "public_key": _b64_encode(public_key),
                "message": _b64_encode(message),
                "signature": _b64_encode(signature),
            }
        )

    payload = "\n".join(_encode_json_line(obj) for obj in line_objects) + "\n"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(payload, encoding="utf-8")
    return {
        "provider": provider_name,
        "algorithm": algorithm,
        "resolved_algorithm": resolved_algorithm,
        "pool_size": pool_size,
        "out_path": str(out_path),
        "created_at_utc": created_at_utc,
        "schema_version": SCHEMA_VERSION,
    }


def load_pool(path: str | Path) -> SignaturePool:
    pool_path = Path(path)
    lines = [line for line in pool_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not lines:
        raise ValueError(f"signature pool is empty: {pool_path}")

    objects = [_decode_json_line(line, line_number=index + 1) for index, line in enumerate(lines)]
    metadata_obj, entry_objects = _split_metadata_and_entries(objects)
    metadata = _parse_metadata(metadata_obj)
    entries = tuple(_parse_entry(entry, index=index + 1) for index, entry in enumerate(entry_objects))

    if len(entries) != metadata.pool_size:
        raise ValueError(
            f"pool_size mismatch: metadata={metadata.pool_size}, entries={len(entries)}"
        )

    return SignaturePool(metadata=metadata, entries=entries)


def _split_metadata_and_entries(
    objects: list[dict[str, Any]]
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    first = objects[0]
    if _looks_like_entry(first):
        metadata = {
            "schema_version": SCHEMA_VERSION,
            "provider": "unknown",
            "algorithm": "unknown",
            "pool_size": len(objects),
            "created_at_utc": "",
            "record_type": "metadata",
        }
        return metadata, objects

    return first, objects[1:]


def _parse_metadata(obj: Mapping[str, Any]) -> SignaturePoolMetadata:
    extra = set(obj.keys()) - METADATA_KEYS
    if extra:
        raise ValueError(f"unknown metadata fields: {sorted(extra)}")

    missing = METADATA_KEYS - set(obj.keys())
    if missing:
        raise ValueError(f"missing metadata fields: {sorted(missing)}")

    if obj.get("record_type") != "metadata":
        raise ValueError("metadata record_type must be 'metadata'")

    schema_version = obj.get("schema_version")
    if schema_version != SCHEMA_VERSION:
        raise ValueError(f"unsupported schema_version: {schema_version!r}")

    provider = obj.get("provider")
    algorithm = obj.get("algorithm")
    created_at_utc = obj.get("created_at_utc")
    pool_size = obj.get("pool_size")
    if not isinstance(provider, str) or not provider.strip():
        raise ValueError("metadata.provider must be a non-empty string")
    if not isinstance(algorithm, str) or not algorithm.strip():
        raise ValueError("metadata.algorithm must be a non-empty string")
    if not isinstance(created_at_utc, str):
        raise ValueError("metadata.created_at_utc must be a string")
    if not isinstance(pool_size, int) or pool_size <= 0:
        raise ValueError("metadata.pool_size must be an int > 0")

    return SignaturePoolMetadata(
        schema_version=SCHEMA_VERSION,
        provider=provider,
        algorithm=algorithm,
        pool_size=pool_size,
        created_at_utc=created_at_utc,
    )


def _parse_entry(obj: Mapping[str, Any], index: int) -> SignaturePoolEntry:
    extra = set(obj.keys()) - ENTRY_KEYS
    if extra:
        raise ValueError(f"entry {index} has unknown fields: {sorted(extra)}")

    missing = ENTRY_KEYS - set(obj.keys())
    if missing:
        raise ValueError(f"entry {index} is missing fields: {sorted(missing)}")

    public_key = _b64_decode(obj["public_key"], field=f"entry {index}.public_key")
    message = _b64_decode(obj["message"], field=f"entry {index}.message")
    signature = _b64_decode(obj["signature"], field=f"entry {index}.signature")
    return SignaturePoolEntry(public_key=public_key, message=message, signature=signature)


def _build_message(algorithm: str, index: int) -> bytes:
    return f"pqc-lab-verify-pool-v1:{algorithm}:{index:08d}".encode("utf-8")


def _looks_like_entry(obj: Mapping[str, Any]) -> bool:
    return set(obj.keys()) == ENTRY_KEYS


def _encode_json_line(obj: Mapping[str, Any]) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _decode_json_line(raw_line: str, line_number: int) -> dict[str, Any]:
    try:
        loaded = json.loads(raw_line)
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSONL at line {line_number}: {exc.msg}") from exc
    if not isinstance(loaded, dict):
        raise ValueError(f"line {line_number} must be a JSON object")
    return loaded


def _b64_encode(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def _b64_decode(value: Any, field: str) -> bytes:
    if not isinstance(value, str):
        raise ValueError(f"{field} must be a base64 string")
    try:
        return base64.b64decode(value.encode("ascii"), validate=True)
    except Exception as exc:
        raise ValueError(f"{field} is not valid base64") from exc


def _positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be an integer") from exc
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be > 0")
    return parsed


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


if __name__ == "__main__":
    raise SystemExit(main())
