import hashlib
import os
import re
from typing import Dict


RECOMMENDED_PRIVATE_KEY_ENV = "AUTO_POOLS_PRIVATE_KEY"
LEGACY_PRIVATE_KEY_ENVS = ("AUTO_POOLS_EVM_PRIVATE_KEY", "EVM_PRIVATE_KEY")
SIGNER_REF_ENV = "AUTO_POOLS_SIGNER_REF"
ALLOW_LOCAL_PRIVATE_KEY_ENV = "AUTO_POOLS_ALLOW_PRIVATE_KEY_SIGNER"

_EVM_PRIVATE_KEY_RE = re.compile(r"^(0x)?[0-9a-fA-F]{64}$")


def _truthy(value: str) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def _private_key_candidates() -> Dict[str, str]:
    names = (RECOMMENDED_PRIVATE_KEY_ENV,) + LEGACY_PRIVATE_KEY_ENVS
    return {name: os.getenv(name, "").strip() for name in names if os.getenv(name, "").strip()}


def _fingerprint(secret: str) -> str:
    normalized = secret.strip().lower()
    if normalized.startswith("0x"):
        normalized = normalized[2:]
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]


def signer_status(chain: str = "") -> Dict:
    """Return signer readiness without exposing any secret material."""
    signer_ref = os.getenv(SIGNER_REF_ENV, "").strip()
    private_keys = _private_key_candidates()
    chain = (chain or "").strip().lower()
    local_private_key_allowed = _truthy(os.getenv(ALLOW_LOCAL_PRIVATE_KEY_ENV, "false"))

    status = {
        "signer_ref_present": bool(signer_ref),
        "private_key_present": bool(private_keys),
        "private_key_env": None,
        "private_key_format": "absent",
        "private_key_fingerprint": None,
        "local_private_key_allowed": local_private_key_allowed,
        "can_prepare_local_signature": False,
        "recommended_env": RECOMMENDED_PRIVATE_KEY_ENV,
        "blocked_reasons": [],
        "notes": [
            "Private key deve ficar somente em env/secret manager.",
            "A skill nunca imprime, salva ou commita a chave privada.",
        ],
    }

    if signer_ref:
        status["signer_type"] = "external-signer-ref"
        status["can_prepare_local_signature"] = True
        return status

    status["signer_type"] = "none"
    if not private_keys:
        status["blocked_reasons"].append("missing-signer")
        return status

    env_name, private_key = next(iter(private_keys.items()))
    status["private_key_env"] = env_name
    status["private_key_fingerprint"] = _fingerprint(private_key)

    if chain == "solana":
        status["signer_type"] = "unsupported-local-private-key"
        status["private_key_format"] = "unsupported-for-solana"
        status["blocked_reasons"].append("solana-local-private-key-unsupported")
        return status

    if not _EVM_PRIVATE_KEY_RE.match(private_key):
        status["signer_type"] = "invalid-local-private-key"
        status["private_key_format"] = "invalid"
        status["blocked_reasons"].append("invalid-private-key-format")
        return status

    status["signer_type"] = "evm-local-private-key"
    status["private_key_format"] = "evm-hex-32-byte"
    if not local_private_key_allowed:
        status["blocked_reasons"].append("local-private-key-signer-disabled")
        status["notes"].append(
            f"Para testes locais, habilite {ALLOW_LOCAL_PRIVATE_KEY_ENV}=true somente em ambiente controlado."
        )
        return status

    status["can_prepare_local_signature"] = True
    return status
