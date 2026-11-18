"""Настройки поведения помощника (behavior/<version>.json + системный файл правил ответа).

Политика не входит в профиль индекса: её смена требует только нового поиска.
"""
from __future__ import annotations

import hashlib
import json

from .config import ACTIVE_POLICY, BEHAVIOR_DIR, ROOT

REQUIRED = {"version", "retrieval_threshold", "authorization_probe_distance", "top_k", "roles", "decisions",
            "context_states", "system_file"}


class PolicyError(RuntimeError):
    pass


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_policy(version: str | None = None) -> dict:
    if version is None:
        if not ACTIVE_POLICY.exists():
            raise PolicyError("нет behavior/active.json — выполните python -m rag_demo policy use --version v2")
        version = json.loads(ACTIVE_POLICY.read_text(encoding="utf-8"))["version"]
    path = BEHAVIOR_DIR / f"{version}.json"
    if not path.exists():
        raise PolicyError(f"нет файла политики {path.relative_to(ROOT).as_posix()}")
    raw = path.read_bytes()
    cfg = json.loads(raw.decode("utf-8-sig"))
    miss = REQUIRED - cfg.keys()
    if miss:
        raise PolicyError(f"{path.name}: нет полей {sorted(miss)}")
    if cfg["version"] != version:
        raise PolicyError(f"{path.name}: version={cfg['version']!r} не совпадает с именем файла")
    for k in ("retrieval_threshold", "authorization_probe_distance"):
        v = cfg[k]
        if not isinstance(v, (int, float)) or isinstance(v, bool) or not 0 < v < 2:
            raise PolicyError(f"{k} должен быть числом в (0, 2), получено {v!r}")
    if not isinstance(cfg["top_k"], int) or isinstance(cfg["top_k"], bool) or cfg["top_k"] < 1:
        raise PolicyError("top_k должен быть положительным целым")
    if sorted(cfg["decisions"]) != sorted(["answer", "clarify", "escalate", "refuse"]):
        raise PolicyError("decisions должны быть ровно answer, clarify, escalate, refuse")
    for k in ("lexical_extra", "lexical_pool", "lexical_stem"):
        if k in cfg and (not isinstance(cfg[k], int) or isinstance(cfg[k], bool) or cfg[k] < 0):
            raise PolicyError(f"{k} должен быть неотрицательным целым")
    if cfg.get("forbidden_rule", "probe_only") not in ("probe_only", "probe_and_closer_than_allowed"):
        raise PolicyError("forbidden_rule: probe_only или probe_and_closer_than_allowed")
    sysfile = ROOT / cfg["system_file"]
    if not sysfile.exists():
        raise PolicyError(f"нет системного файла {cfg['system_file']}")
    return {**cfg, "config_path": path.relative_to(ROOT).as_posix(), "config_sha256": _sha(raw),
            "system_sha256": _sha(sysfile.read_bytes())}


def snapshot(p: dict) -> dict:
    """Что записывается в результат поиска и сверяется в finalize."""
    keys = ("version", "retrieval_threshold", "authorization_probe_distance", "top_k", "config_path",
            "config_sha256", "system_file", "system_sha256")
    snap = {k: p[k] for k in keys}
    for k in ("lexical_extra", "lexical_pool", "lexical_stem", "forbidden_rule"):
        if k in p:  # v2 не содержит этих полей — её снимок не меняется
            snap[k] = p[k]
    return snap


def use(version: str) -> dict:
    p = load_policy(version)
    ACTIVE_POLICY.write_text(json.dumps({"version": version}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"status": "policy_active", **snapshot(p)}


def show() -> dict:
    p = load_policy()
    return {"status": "policy_active", **snapshot(p), "roles": p["roles"], "decisions": p["decisions"],
            "context_states": p["context_states"]}
