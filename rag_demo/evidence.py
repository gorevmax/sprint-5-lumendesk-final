"""finalize: проверка ответа ИИ по результату текущего поиска и сохранение истории.

Проверяется происхождение ссылок (ID, документ, дословная цитата, доступ роли, актуальность индекса
и настроек). Проверка происхождения не заменяет смысловую проверку тезисов человеком.
"""
from __future__ import annotations

import json
from pathlib import Path

from .config import COLLECTION, EVIDENCE_DIR, ROOT
from . import documents as D
from . import policy as P
from . import storage as S

RAW_KEYS = {"answer", "citations", "decision"}
CIT_KEYS = {"document_id", "chunk_id", "quote"}
RETRIEVAL_KEYS = {"status", "query_id", "index_id", "question", "role", "top_k", "policy", "context_state",
                  "filtering", "hits", "context", "context_chunk_ids", "retrieval_trace_path"}
HIT_KEYS = {"rank", "chunk_id", "text", "metadata", "distance", "provenance"}


class FinalizeError(RuntimeError):
    def __init__(self, errors: list[str]):
        super().__init__("; ".join(errors))
        self.errors = errors


def _load_json(path: Path, label: str) -> dict:
    if not path.exists():
        raise FinalizeError([f"{label}: файл {path} не найден"])
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as e:
        raise FinalizeError([f"{label}: некорректный JSON ({e})"])


def _abs(p: str) -> Path:
    path = Path(p)
    return path if path.is_absolute() else ROOT / path


# ---------------------------------------------------------------- место в оригинале

def _matched_cells(span: dict, quote: str) -> list[dict]:
    cells = span.get("cells") or []
    hit = [c for c in cells if (c.get("value_ru") and c["value_ru"] in quote) or
           (c.get("header_ru") and c["header_ru"] in quote)]
    return hit or cells


def source_location(meta: dict, span: dict, quote: str) -> dict:
    """Проверяемое место в оригинале по формату файла."""
    fmt = meta["format"]
    loc = span["locator"]
    out = {"file": meta["source_path"], "format": fmt, "fragment_id": span["fragment_id"]}
    section = span.get("section_orig") or span.get("section_ru") or meta["section"]
    if fmt in ("md", "txt"):
        a, b = loc["lines"]
        out.update(section=section, lines=[a, b], where=f"раздел «{section}», строки {a}–{b}" if a != b
                   else f"раздел «{section}», строка {a}")
    elif fmt == "csv":
        cells = _matched_cells(span, quote)
        cols = [c["header"] if c.get("header_ru") in (None, c["header"]) else f"{c['header']} ({c['header_ru']})"
                for c in cells]
        out.update(rows=[loc["csv_row"]], columns=cols,
                   where=f"строка {loc['csv_row']}, столбцы: {', '.join(cols)}")
    elif fmt == "xlsx":
        cells = _matched_cells(span, quote)
        refs = [c["ref"] for c in cells if c.get("ref")]
        rng = loc.get("range")
        out.update(sheet=loc["sheet"], cells=refs, range=rng,
                   where=f"лист «{loc['sheet']}», " + (f"ячейки {', '.join(refs)}" if refs else f"диапазон {rng}"))
    elif fmt == "pdf":
        p1, p2 = loc["page"], loc.get("page_end", loc["page"])
        out.update(pages=sorted({p1, p2}), block=loc.get("block"),
                   where=f"стр. {p1}" if p1 == p2 else f"стр. {p1}–{p2}")
    elif fmt == "docx":
        out.update(section=section, paragraph=loc["paragraph"],
                   where=f"раздел «{section}», абзац {loc['paragraph']}")
    else:
        out["where"] = span["locator_text"]
    if section is None or section == "(введение)":
        out["where"] = out["where"].replace("раздел «None»", "введение").replace("раздел «(введение)»", "введение")
    return out


def locate_quote(hit: dict, quote: str) -> list[dict]:
    """Фрагменты чанка, которые покрывает цитата (по позиции в тексте hit)."""
    pos = hit["text"].find(quote)
    end = pos + len(quote)
    return [s for s in hit["provenance"] if s["start"] < end and s["end"] > pos]


# ---------------------------------------------------------------- проверка

def check(retrieval: dict, raw: dict) -> tuple[list[str], dict]:
    errors: list[str] = []
    # raw
    if set(raw) != RAW_KEYS:
        errors.append(f"raw-ответ: поля должны быть ровно {sorted(RAW_KEYS)}, получено {sorted(raw)}")
    answer, cits, decision = raw.get("answer"), raw.get("citations"), raw.get("decision")
    if not isinstance(answer, str) or not answer.strip():
        errors.append("answer должен быть непустой строкой")
    if not isinstance(cits, list):
        errors.append("citations должен быть массивом")
        cits = []
    for i, c in enumerate(cits):
        if not isinstance(c, dict) or set(c) != CIT_KEYS:
            errors.append(f"citations[{i}]: поля должны быть ровно {sorted(CIT_KEYS)}")
        elif not all(isinstance(c[k], str) and c[k].strip() for k in CIT_KEYS):
            errors.append(f"citations[{i}]: document_id, chunk_id и quote — непустые строки")
    # retrieval
    miss = RETRIEVAL_KEYS - set(retrieval)
    if miss:
        errors.append(f"результат поиска: нет полей {sorted(miss)}")
        return errors, {}
    if retrieval["status"] != "retrieval_only":
        errors.append(f"результат поиска: status={retrieval['status']!r}, ожидается retrieval_only")
    try:
        man = S.check_index()
    except S.StaleIndex as e:
        errors.append(str(e))
        return errors, {}
    if retrieval["index_id"] != man["index_id"]:
        errors.append(f"результат поиска относится к индексу {retrieval['index_id']}, текущий {man['index_id']}: "
                      "выполните новый поиск")
    pol = P.load_policy()
    if retrieval["policy"] != P.snapshot(pol):
        errors.append("настройки поиска не совпадают с активной политикой (версия или хеши изменились): нужен новый поиск")
    if decision not in pol["decisions"]:
        errors.append(f"decision={decision!r}; допустимы {pol['decisions']}")
    role = retrieval["role"]
    if role not in pol["roles"]:
        errors.append(f"неизвестная роль {role!r}")
    hits = retrieval["hits"]
    for h in hits:
        if set(h) != HIT_KEYS:
            errors.append(f"hit {h.get('chunk_id')}: изменён состав полей")
    if retrieval["context_chunk_ids"] != [h["chunk_id"] for h in hits]:
        errors.append("context_chunk_ids не совпадает с hits")
    thr = pol["retrieval_threshold"]
    if any(h["distance"] > thr for h in hits):
        errors.append("в hits есть фрагменты дальше порога retrieval_threshold")
    if len(hits) > retrieval["top_k"] + pol.get("lexical_extra", 0):
        errors.append("hits больше, чем top_k + lexical_extra")
    state = retrieval["context_state"]
    if (state == "available") != bool(hits):
        errors.append(f"context_state={state} не соответствует числу hits ({len(hits)})")
    # hits против коллекции и хранилища
    access = D.load_access()
    store = S.load_chunk_store()
    col = S.client().get_collection(COLLECTION, embedding_function=None)
    got = col.get(ids=[h["chunk_id"] for h in hits], include=["documents", "metadatas"]) if hits else \
        {"ids": [], "documents": [], "metadatas": []}
    by_id = {i: (d, m) for i, d, m in zip(got["ids"], got["documents"], got["metadatas"])}
    expected_context = "\n\n".join(f"[{h['chunk_id']}] {h['metadata']['title']} — {h['metadata']['source_path']}, "
                                   f"{h['metadata']['locator']}\n{h['text']}" for h in hits)
    if retrieval["context"] != expected_context:
        errors.append("context не совпадает с текстами hits")
    for h in hits:
        cid = h["chunk_id"]
        if cid not in by_id:
            errors.append(f"hit {cid}: нет в коллекции {COLLECTION}")
            continue
        doc, meta = by_id[cid]
        if doc != h["text"]:
            errors.append(f"hit {cid}: text изменён относительно коллекции")
        if meta != h["metadata"]:
            errors.append(f"hit {cid}: metadata изменены относительно коллекции")
        if S.provenance(store[cid]) != h["provenance"]:
            errors.append(f"hit {cid}: provenance изменено относительно хранилища фрагментов")
        if role not in access.get(meta["document_id"], []):
            errors.append(f"hit {cid}: документ недоступен роли {role} по текущему access.csv — нужен новый поиск")
    # решения
    if state in ("empty", "forbidden") and decision != "refuse":
        errors.append(f"context_state={state}: допустимо только decision=refuse")
    if decision == "refuse" and cits:
        errors.append("decision=refuse: citations должен быть пустым")
    if decision in ("answer", "escalate") and not cits:
        errors.append(f"decision={decision}: нужна хотя бы одна цитата из текущих hits")
    # цитаты
    hit_by_id = {h["chunk_id"]: h for h in hits}
    enriched = []
    for i, c in enumerate(cits):
        if not isinstance(c, dict) or set(c) != CIT_KEYS:
            continue
        h = hit_by_id.get(c["chunk_id"])
        if h is None:
            errors.append(f"citations[{i}]: chunk_id {c['chunk_id']!r} отсутствует в hits текущего поиска")
            continue
        if c["document_id"] != h["metadata"]["document_id"]:
            errors.append(f"citations[{i}]: document_id {c['document_id']!r} не равен metadata.document_id "
                          f"найденного {c['chunk_id']} ({h['metadata']['document_id']})")
            continue
        if c["quote"] not in h["text"]:
            errors.append(f"citations[{i}]: quote не является дословной подстрокой text фрагмента {c['chunk_id']}")
            continue
        spans = locate_quote(h, c["quote"])
        meta = h["metadata"]
        enriched.append({
            "citation_index": i, "document_id": c["document_id"], "chunk_id": c["chunk_id"], "quote": c["quote"],
            "rank": h["rank"], "distance": h["distance"],
            "title": meta["title"], "title_orig": meta["title_orig"], "source_path": meta["source_path"],
            "section": meta["section"], "version": meta["version"], "updated": meta["updated"],
            "owner": meta["owner"], "source_lang": meta["source_lang"], "is_translation": meta["is_translation"],
            "fragments": [{
                "fragment_id": s["fragment_id"], "location": source_location(meta, s, c["quote"]),
                "translation": s["translation"],
                "original_excerpt": s.get("text_orig"),
                "original_cells": [{k: x.get(k) for k in ("ref", "col", "header", "value") if x.get(k) is not None}
                                   for x in _matched_cells(s, c["quote"])] if s.get("cells") else None,
                "handling": s.get("handling"), "also_in": s.get("also_in"), "similar_to": s.get("similar_to"),
            } for s in spans],
        })
    return errors, {"manifest": man, "policy": pol, "citations": enriched}


def finalize(retrieval_path: str, answer_path: str) -> dict:
    rp, ap = _abs(retrieval_path), _abs(answer_path)
    retrieval = _load_json(rp, "результат поиска")
    raw = _load_json(ap, "raw-ответ")
    errors, ctx = check(retrieval, raw)
    at = S.now()
    if errors:
        S.append_history({"event": "finalize_rejected", "at": at, "retrieval": S.rel(rp), "answer_file": S.rel(ap),
                          "question": retrieval.get("question"), "role": retrieval.get("role"), "errors": errors})
        raise FinalizeError(errors)
    capture_id = "cap-" + S.stamp_id()
    EVIDENCE_DIR.mkdir(exist_ok=True)
    paths = {k: EVIDENCE_DIR / f"{k}-{capture_id}.json" for k in ("result", "trace", "citation-map")}
    cits = ctx["citations"]
    result = {
        "status": "finalized", "capture_id": capture_id, "created_at": at,
        "question": retrieval["question"], "role": retrieval["role"], "decision": raw["decision"],
        "answer": raw["answer"],
        "citations": [{
            "document_id": c["document_id"], "chunk_id": c["chunk_id"], "quote": c["quote"],
            "source_path": c["source_path"], "title": c["title"], "title_orig": c["title_orig"],
            "section": c["section"], "version": c["version"], "updated": c["updated"],
            "source_lang": c["source_lang"],
            "where": "; ".join(f["location"]["where"] for f in c["fragments"]),
            "original_excerpt": [f["original_excerpt"] for f in c["fragments"] if f["original_excerpt"]] or None,
        } for c in cits],
        "context_state": retrieval["context_state"], "policy_version": ctx["policy"]["version"],
        "index_id": retrieval["index_id"], "query_id": retrieval["query_id"],
        "retrieval_path": S.rel(rp), "answer_file": S.rel(ap),
        "trace_path": S.rel(paths["trace"]), "citation_map_path": S.rel(paths["citation-map"]),
        "checks": "происхождение ссылок подтверждено: ID из текущих hits, document_id совпадает, quote дословна, "
                  "документ доступен роли, индекс и настройки актуальны. Смысл тезисов проверяет человек.",
    }
    trace = {
        "capture_id": capture_id, "created_at": at, "question": retrieval["question"], "role": retrieval["role"],
        "index_id": retrieval["index_id"], "policy": retrieval["policy"], "profile": ctx["manifest"]["profile"],
        "retrieval": retrieval, "context": retrieval["context"], "raw_answer": raw,
        "verification": {"status": "passed", "errors": [], "citations_checked": len(cits)},
        "result_path": S.rel(paths["result"]),
    }
    cmap = {"capture_id": capture_id, "question": retrieval["question"], "role": retrieval["role"],
            "citations": cits}
    for k, obj in (("trace", trace), ("citation-map", cmap), ("result", result)):
        paths[k].write_text(json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8")
    S.append_history({"event": "finalize", "at": at, "capture_id": capture_id, "question": retrieval["question"],
                      "role": retrieval["role"], "decision": raw["decision"], "query_id": retrieval["query_id"],
                      "index_id": retrieval["index_id"], "citations": [
                          {"chunk_id": c["chunk_id"], "source_path": c["source_path"], "where": r["where"]}
                          for c, r in zip(cits, result["citations"])],
                      "result": S.rel(paths["result"]), "trace": S.rel(paths["trace"]),
                      "citation_map": S.rel(paths["citation-map"])})
    return result
