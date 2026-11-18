"""Проверки контрактов. Интеграционные тесты выполняются только при актуальном индексе.

Запуск: python -m pytest -q tests
"""
from __future__ import annotations

import copy
import json

import pytest

from rag_demo import documents as D
from rag_demo import evidence as E
from rag_demo import policy as P
from rag_demo import storage as S


def test_sentences_are_verbatim():
    t = "Первое. Второе предложение!  Третье? Хвост"
    assert "".join(D._sentences(t)) == t


def test_policy_v2_valid():
    p = P.load_policy("v2")
    assert p["retrieval_threshold"] == 0.20 and p["authorization_probe_distance"] == 0.35
    assert sorted(p["decisions"]) == ["answer", "clarify", "escalate", "refuse"]


def test_access_lead_only():
    acc = D.load_access()
    assert acc["abuse-review"] == ["support_lead"]
    assert all("support_lead" in r for r in acc.values())


def test_validate_docs():
    r = D.validate_docs()
    assert r["status"] == "documents_valid", r["errors"]
    assert r["documents_total"] == 50


def _index_ready():
    try:
        S.check_index()
        return True
    except Exception:
        return False


needs_index = pytest.mark.skipif(not _index_ready(), reason="индекс не построен или устарел")


@pytest.fixture(scope="module")
def retrieval(tmp_path_factory):
    out = tmp_path_factory.mktemp("r") / "retrieval.json"
    res, _ = S.retrieve("Какой предел одного вложения на Team?", "support_agent", 8, str(out))
    return res


@needs_index
def test_retrieval_contract(retrieval):
    r = retrieval
    assert r["status"] == "retrieval_only" and r["role"] == "support_agent"
    assert r["context_chunk_ids"] == [h["chunk_id"] for h in r["hits"]]
    for h in r["hits"]:
        assert set(h) == E.HIT_KEYS
        assert h["distance"] <= r["policy"]["retrieval_threshold"]
        for k in ("document_id", "title", "source_path", "section", "version", "updated", "owner", "line_start",
                  "line_end", "document_sha256", "chunk_sha256", "token_count"):
            assert k in h["metadata"]


@needs_index
def test_agent_never_gets_lead_documents(retrieval):
    acc = D.load_access()
    assert all("support_agent" in acc[h["metadata"]["document_id"]] for h in retrieval["hits"])
    assert "abuse-review" not in json.dumps(retrieval["filtering"], ensure_ascii=False)


@needs_index
def test_finalize_rejects_bad_answers(retrieval):
    h = retrieval["hits"][0]
    good = {"answer": "x", "decision": "answer",
            "citations": [{"document_id": h["metadata"]["document_id"], "chunk_id": h["chunk_id"],
                           "quote": h["text"][:20]}]}
    assert E.check(retrieval, good)[0] == []
    bad_id = copy.deepcopy(good)
    bad_id["citations"][0]["chunk_id"] = "unknown::chunk-99"
    assert E.check(retrieval, bad_id)[0]
    bad_quote = copy.deepcopy(good)
    bad_quote["citations"][0]["quote"] = "выдуманная цитата 999 МБ"
    assert E.check(retrieval, bad_quote)[0]
    refuse_with_cit = copy.deepcopy(good)
    refuse_with_cit["decision"] = "refuse"
    assert E.check(retrieval, refuse_with_cit)[0]
    extra = copy.deepcopy(good)
    extra["note"] = "лишнее поле"
    assert E.check(retrieval, extra)[0]
    tampered = copy.deepcopy(retrieval)
    tampered["hits"][0]["text"] = tampered["hits"][0]["text"].replace("Team", "Teams", 1) + " "
    assert E.check(tampered, good)[0]


@needs_index
def test_v3_forbidden_only_when_restricted_is_closer(tmp_path):
    if P.load_policy()["version"] != "v3":
        pytest.skip("активна не v3")
    off, _ = S.retrieve("Какая погода будет завтра в Париже?", "support_agent", 8, str(tmp_path / "off.json"))
    assert off["context_state"] == "empty" and not off["hits"]
    lead, _ = S.retrieve("Какие внутренние пороги используются для проверки злоупотреблений?", "support_agent", 8,
                         str(tmp_path / "lead.json"))
    assert lead["context_state"] == "forbidden" and not lead["hits"]
    assert "abuse-review" not in json.dumps(lead, ensure_ascii=False)


@needs_index
def test_v3_lexical_extra_keeps_dense_top_k(tmp_path):
    if P.load_policy()["version"] != "v3":
        pytest.skip("активна не v3")
    q = "Какой предел одного вложения на Team?"
    r, _ = S.retrieve(q, "support_agent", 8, str(tmp_path / "r.json"))
    import json as _j
    trace = _j.loads((S.ROOT / r["retrieval_trace_path"]).read_text(encoding="utf-8"))
    dense = [c["chunk_id"] for c in trace["candidates"] if c["within_threshold"]][:8]
    assert r["context_chunk_ids"][:8] == dense
    assert len(r["hits"]) <= 8 + P.load_policy()["lexical_extra"]
    assert [h["chunk_id"] for h in r["hits"][8:]] == [x["chunk_id"] for x in r["filtering"]["lexical_added"]]
