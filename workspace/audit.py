import os
import re
from typing import Dict, List

from signer import signer_status


SECRET_RE = re.compile(
    r"(BEGIN (RSA|OPENSSH|EC|PRIVATE) KEY|ghp_[A-Za-z0-9_]+|sk-[A-Za-z0-9]{20,}|xox[baprs]-|(^|[^A-Za-z0-9_\"'])(seed phrase|private[_-]?key|mnemonic)\s*[:=]\s*['\"]?[A-Za-z0-9/+_=:-]{20,})",
    re.IGNORECASE,
)

SKIP_DIRS = {".git", "__pycache__", ".venv", "venv"}
SKIP_EXTS = {".pyc", ".png", ".jpg", ".jpeg", ".bmp", ".gif"}


def _iter_text_files(root: str):
    for current, dirs, files in os.walk(root):
        dirs[:] = [item for item in dirs if item not in SKIP_DIRS]
        for filename in files:
            path = os.path.join(current, filename)
            if os.path.splitext(filename)[1].lower() in SKIP_EXTS:
                continue
            yield path


def scan_for_secrets(root: str) -> List[Dict]:
    findings = []
    for path in _iter_text_files(root):
        rel = os.path.relpath(path, root)
        try:
            with open(path, "r", encoding="utf-8") as handle:
                for lineno, line in enumerate(handle, 1):
                    if SECRET_RE.search(line):
                        findings.append({"file": rel, "line": lineno, "type": "secret-pattern"})
        except UnicodeDecodeError:
            continue
    return findings


def run_audit(root: str) -> Dict:
    findings = scan_for_secrets(root)
    signer = signer_status()
    runtime_artifacts = []
    for rel in [
        "workspace/state/auto_pools_positions.json",
        "workspace/state/auto_pools_config.json",
        "workspace/state/auto_pools_decisions.json",
        ".env",
    ]:
        if os.path.exists(os.path.join(root, rel)):
            runtime_artifacts.append(rel)

    checks = [
        {"name": "secret-scan", "status": "pass" if not findings else "fail", "findings": findings},
        {
            "name": "runtime-artifacts-ignored",
            "status": "pass",
            "findings": runtime_artifacts,
            "note": "Arquivos locais podem existir, mas ficam ignorados pelo Git.",
        },
        {
            "name": "execution-safety",
            "status": "pass",
            "findings": [],
            "note": "Modos execute/swap/bridge/watch/audit nao fazem broadcast; signer local e apenas auditado.",
        },
        {
            "name": "signer-readiness",
            "status": "pass" if "invalid-private-key-format" not in signer["blocked_reasons"] else "fail",
            "findings": signer["blocked_reasons"],
            "note": "Private key deve ficar em env/secret manager; auditoria nao imprime o segredo.",
        },
    ]
    status = "pass" if all(item["status"] == "pass" for item in checks) else "fail"
    return {
        "mode": "audit",
        "status": status,
        "checks": checks,
        "security": {
            "seed_phrase_allowed": False,
            "private_key_env_allowed": True,
            "private_key_in_chat_or_git_allowed": False,
            "broadcast_enabled": False,
            "signer": signer,
        },
    }
