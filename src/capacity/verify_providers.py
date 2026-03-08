from __future__ import annotations

"""Provider adapters for signature-verify capacity benchmarks."""

import hashlib
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

PREFERRED_MLDSA_ALGORITHMS = ("ML-DSA-65", "ML-DSA-44", "ML-DSA-87")
PQC_REAL_HINT = (
    "hint: run `pixi run --environment pqc-real bootstrap-oqs` and "
    "`pixi run --environment pqc-real preflight-real-mldsa`"
)


class ProviderError(RuntimeError):
    """Base class for provider adapter failures."""


class ProviderUnavailableError(ProviderError):
    """Raised when a requested provider is unavailable at runtime."""


class ProviderConfigurationError(ProviderError):
    """Raised when a provider is available but misconfigured for a request."""


@dataclass(frozen=True)
class ProviderStatus:
    provider: str
    available: bool
    test_only: bool
    details: str


class VerifySession(ABC):
    @abstractmethod
    def verify(self, public_key: bytes, message: bytes, signature: bytes) -> bool:
        raise NotImplementedError

    def close(self) -> None:
        return None


class VerifyProvider(ABC):
    name: str
    test_only: bool

    @abstractmethod
    def status(self) -> ProviderStatus:
        raise NotImplementedError

    @abstractmethod
    def resolve_algorithm(self, algorithm: str) -> str:
        raise NotImplementedError

    @abstractmethod
    def create_verify_session(self, algorithm: str) -> VerifySession:
        raise NotImplementedError

    @abstractmethod
    def generate_public_material(
        self,
        algorithm: str,
        message: bytes,
        index: int,
    ) -> tuple[bytes, bytes]:
        """Return (public_key, signature) for message."""

    def generate_public_material_batch(
        self,
        algorithm: str,
        messages: tuple[bytes, ...],
    ) -> tuple[tuple[bytes, bytes], ...]:
        return tuple(
            self.generate_public_material(algorithm, message, index)
            for index, message in enumerate(messages)
        )


class _MockVerifySession(VerifySession):
    def __init__(self, algorithm: str) -> None:
        self._algorithm = algorithm

    def verify(self, public_key: bytes, message: bytes, signature: bytes) -> bool:
        expected = _mock_signature(self._algorithm, public_key, message)
        return signature == expected


class MockVerifyProvider(VerifyProvider):
    """Deterministic test-only provider for harness validation."""

    name = "mock_verify"
    test_only = True

    def status(self) -> ProviderStatus:
        return ProviderStatus(
            provider=self.name,
            available=True,
            test_only=True,
            details="deterministic test-only mock provider (not cryptographic validation)",
        )

    def resolve_algorithm(self, algorithm: str) -> str:
        if not isinstance(algorithm, str) or not algorithm.strip():
            raise ProviderConfigurationError("algorithm must be a non-empty string")
        return algorithm.strip()

    def create_verify_session(self, algorithm: str) -> VerifySession:
        resolved = self.resolve_algorithm(algorithm)
        return _MockVerifySession(resolved)

    def generate_public_material(
        self,
        algorithm: str,
        message: bytes,
        index: int,
    ) -> tuple[bytes, bytes]:
        resolved = self.resolve_algorithm(algorithm)
        public_key = hashlib.sha256(
            f"mock-verify-public-key-v1:{resolved}:{index}".encode("utf-8")
        ).digest()
        signature = _mock_signature(resolved, public_key, message)
        return public_key, signature


def _mock_signature(algorithm: str, public_key: bytes, message: bytes) -> bytes:
    # Test-only deterministic helper; this is not a cryptographic signature scheme.
    digest = hashlib.sha256()
    digest.update(b"mock-verify-signature-v1")
    digest.update(algorithm.encode("utf-8"))
    digest.update(public_key)
    digest.update(message)
    return digest.digest()


class _RealMldsaVerifySession(VerifySession):
    def __init__(self, verifier: Any) -> None:
        self._verifier = verifier

    def verify(self, public_key: bytes, message: bytes, signature: bytes) -> bool:
        return bool(self._verifier.verify(message, signature, public_key))

    def close(self) -> None:
        _cleanup_signature_instance(self._verifier)


class RealMldsaProvider(VerifyProvider):
    name = "real_mldsa"
    test_only = False

    def status(self) -> ProviderStatus:
        try:
            oqs = _import_oqs()
        except ProviderUnavailableError as exc:
            return ProviderStatus(
                provider=self.name,
                available=False,
                test_only=False,
                details=str(exc),
            )

        algorithms = _list_signature_algorithms(oqs)
        available, details = _mldsa_support_status(algorithms)
        if not available and not algorithms:
            details = "python-oqs imported but signature algorithm discovery returned no values"
        return ProviderStatus(
            provider=self.name,
            available=available,
            test_only=False,
            details=details,
        )

    def resolve_algorithm(self, algorithm: str) -> str:
        requested = _clean_algorithm_name(algorithm)
        oqs = _import_oqs()
        algorithms = _list_signature_algorithms(oqs)
        if not algorithms:
            raise ProviderConfigurationError(
                "real_mldsa provider cannot list signature mechanisms from python-oqs"
            )

        if requested in algorithms:
            return requested

        requested_norm = _normalize_algorithm_name(requested)
        if requested_norm == "mldsa":
            preferred = _pick_preferred_mldsa(algorithms)
            if preferred is not None:
                return preferred

        for candidate in algorithms:
            if _normalize_algorithm_name(candidate) == requested_norm:
                return candidate

        raise ProviderConfigurationError(
            "real_mldsa provider does not support algorithm "
            f"{requested!r}; available ML-DSA mechanisms: {sorted(_mldsa_candidates(algorithms))}"
        )

    def create_verify_session(self, algorithm: str) -> VerifySession:
        resolved = self.resolve_algorithm(algorithm)
        oqs = _import_oqs()
        signature_instance = _new_signature_instance(oqs, resolved)
        return _RealMldsaVerifySession(signature_instance)

    def generate_public_material(
        self,
        algorithm: str,
        message: bytes,
        index: int,
    ) -> tuple[bytes, bytes]:
        resolved = self.resolve_algorithm(algorithm)
        oqs = _import_oqs()
        signer = _new_signature_instance(oqs, resolved)
        try:
            public_key = signer.generate_keypair()
            signature = signer.sign(message)
            return bytes(public_key), bytes(signature)
        finally:
            _cleanup_signature_instance(signer)

    def generate_public_material_batch(
        self,
        algorithm: str,
        messages: tuple[bytes, ...],
    ) -> tuple[tuple[bytes, bytes], ...]:
        resolved = self.resolve_algorithm(algorithm)
        oqs = _import_oqs()
        signer = _new_signature_instance(oqs, resolved)
        try:
            public_key = bytes(signer.generate_keypair())
            pairs: list[tuple[bytes, bytes]] = []
            for message in messages:
                signature = bytes(signer.sign(message))
                pairs.append((public_key, signature))
            return tuple(pairs)
        finally:
            _cleanup_signature_instance(signer)


def _clean_algorithm_name(algorithm: str) -> str:
    if not isinstance(algorithm, str):
        raise ProviderConfigurationError("algorithm must be a string")
    cleaned = algorithm.strip()
    if not cleaned:
        raise ProviderConfigurationError("algorithm must be a non-empty string")
    return cleaned


def _normalize_algorithm_name(name: str) -> str:
    return "".join(ch for ch in name.lower() if ch.isalnum())


def _mldsa_candidates(algorithms: list[str]) -> list[str]:
    return [alg for alg in algorithms if _normalize_algorithm_name(alg).startswith("mldsa")]


def _pick_preferred_mldsa(algorithms: list[str]) -> str | None:
    for preferred in PREFERRED_MLDSA_ALGORITHMS:
        for algorithm in algorithms:
            if _normalize_algorithm_name(algorithm) == _normalize_algorithm_name(preferred):
                return algorithm
    mldsa_options = sorted(_mldsa_candidates(algorithms))
    if mldsa_options:
        return mldsa_options[0]
    return None


def _mldsa_support_status(algorithms: list[str]) -> tuple[bool, str]:
    if not algorithms:
        return False, "python-oqs imported, but no signature mechanisms were detected"
    preferred = _pick_preferred_mldsa(algorithms)
    if preferred is None:
        return False, f"no ML-DSA mechanism exposed; signature mechanisms count={len(algorithms)}"
    return True, f"available via python-oqs (resolved default: {preferred})"


def _import_oqs() -> Any:
    try:
        import oqs  # type: ignore
    except ModuleNotFoundError as exc:  # pragma: no cover - exercised through status() in tests
        if getattr(exc, "name", None) == "oqs":
            raise ProviderUnavailableError(
                f"missing module 'oqs'; {PQC_REAL_HINT}"
            ) from exc
        raise ProviderUnavailableError(
            f"failed while importing oqs dependency: {exc}; {PQC_REAL_HINT}"
        ) from exc
    except Exception as exc:  # pragma: no cover - exercised through status() in tests
        raise ProviderUnavailableError(
            f"failed to import oqs runtime: {exc}; {PQC_REAL_HINT}"
        ) from exc
    return oqs


def _list_signature_algorithms(oqs_module: Any) -> list[str]:
    for attr_name in (
        "get_enabled_sig_mechanisms",
        "get_sig_mechanisms",
        "get_supported_sig_mechanisms",
    ):
        fn = getattr(oqs_module, attr_name, None)
        if not callable(fn):
            continue
        try:
            values = fn()
        except Exception:
            continue
        if values is None:
            continue
        if isinstance(values, (list, tuple, set)):
            return [str(item) for item in values if isinstance(item, str)]
    return []


def _new_signature_instance(oqs_module: Any, algorithm: str) -> Any:
    signature_cls = getattr(oqs_module, "Signature", None)
    if not callable(signature_cls):
        raise ProviderConfigurationError("python-oqs does not expose Signature")
    try:
        return signature_cls(algorithm)
    except Exception as exc:
        raise ProviderConfigurationError(
            f"could not initialize oqs.Signature({algorithm!r})"
        ) from exc


def _cleanup_signature_instance(instance: Any) -> None:
    free_fn = getattr(instance, "free", None)
    if callable(free_fn):
        try:
            free_fn()
        except Exception:
            return


_PROVIDERS: dict[str, VerifyProvider] = {
    "mock_verify": MockVerifyProvider(),
    "real_mldsa": RealMldsaProvider(),
}


def list_provider_statuses() -> list[ProviderStatus]:
    ordered_names = ("mock_verify", "real_mldsa")
    return [_PROVIDERS[name].status() for name in ordered_names]


def get_provider(provider_name: str) -> VerifyProvider:
    provider = _PROVIDERS.get(provider_name)
    if provider is None:
        raise ProviderConfigurationError(
            f"unknown provider {provider_name!r}; expected one of {sorted(_PROVIDERS)}"
        )
    status = provider.status()
    if not status.available:
        raise ProviderUnavailableError(
            f"provider {provider_name!r} is unavailable: {status.details}"
        )
    return provider
