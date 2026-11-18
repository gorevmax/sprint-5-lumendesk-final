"""Индекс Chroma, манифест, проверка актуальности и поиск с учётом роли."""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
import platform
import re
import secrets
import sys
from pathlib import Path

from .config import (CHUNK_STORE, COLLECTION, EVIDENCE_DIR, HISTORY, INVENTORY, MANIFEST, MODEL_DIR, MODEL_ID,
                     PROFILE, ROOT, STORE_DIR)
from . import documents as D
from . import model as M
from . import policy as P


class StaleIndex(RuntimeError):
    pass


class RetrievalError(RuntimeError):
    pass


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def stamp_id() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + secrets.token_hex(3)


def sha_json(obj) -> str:
    return hashlib.sha256(json.dumps(obj, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def rel(p: Path) -> str:
    p = Path(p).resolve()
    try:
        return p.relative_to(ROOT).as_posix()
    except ValueError:  # файл вне проекта (например, временный каталог тестов)
        return p.as_posix()


def log(msg: str):
    print(msg, file=sys.stderr, flush=True)


def append_history(rec: dict):
    EVIDENCE_DIR.mkdir(exist_ok=True)
    with HISTORY.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")


def client():
    import chromadb
    from chromadb.config import Settings

    return chromadb.PersistentClient(path=str(STORE_DIR), settings=Settings(anonymized_telemetry=False))


def translation_inputs(source_path: str) -> dict:
    """Файлы, из которых собран перевод документа (их изменение без prepare делает индекс устаревшим)."""
    rel_doc = source_path[len("documents/"):]
    out = {}
    for p in (ROOT / "translations" / (rel_doc + ".ru.txt"), ROOT / "translations" / "_review.json",
              ROOT / "registry" / "decisions.json"):
        if p.exists():
            out[rel(p)] = D.sha256_file(p)
    return out


def corpus_state() -> dict:
    docs = []
    for d in D.included_documents():
        inv = d["inventory"]
        src = ROOT / inv["path"]
        docs.append({"document_id": inv["id"], "source_path": inv["path"],
                     "document_sha256": D.sha256_file(src) if src.exists() else None,
                     "prepared_sha256": D.sha256_file(d["prepared_path"]) if d["prepared_path"].exists() else None,
                     "translation_inputs": translation_inputs(inv["path"])})
    return {"inventory_sha256": D.sha256_file(INVENTORY), "documents": docs}


# ---------------------------------------------------------------- index

def build_index() -> dict:
    v = D.validate_docs()
    if v["status"] != "documents_valid":
        raise D.CorpusError("validate-docs: " + "; ".join(v["errors"]))
    log("загрузка локальной модели…")
    model = M.load_local_model()
    log("SHA-256 файлов модели…")
    hashes = M.model_hashes()
    M.write_model_source(hashes)
    log("нарезка подготовленного корпуса…")
    chunks, docs_meta = D.build_chunks(M.token_count)
    ids = [c["chunk_id"] for c in chunks]
    if len(ids) != len(set(ids)):
        raise D.CorpusError("повторяющиеся chunk_id")
    log(f"эмбеддинги {len(chunks)} чанков на CPU…")
    emb = M.encode_passages([c["embedding_text"] for c in chunks])
    if emb.shape != (len(chunks), PROFILE["dimension"]):
        raise M.ModelError(f"форма эмбеддингов {emb.shape}")
    state = corpus_state()
    index_id = "idx-" + stamp_id()
    STORE_DIR.mkdir(exist_ok=True)
    cl = client()
    if COLLECTION in [c.name for c in cl.list_collections()]:
        cl.delete_collection(COLLECTION)  # пересоздаётся только своя коллекция
    col = cl.create_collection(name=COLLECTION, configuration={"hnsw": {"space": "cosine"}},
                               embedding_function=None, metadata={"index_id": index_id})
    B = 256
    for i in range(0, len(chunks), B):
        part = chunks[i:i + B]
        col.upsert(ids=[c["chunk_id"] for c in part], embeddings=emb[i:i + B].tolist(),
                   documents=[c["text"] for c in part], metadatas=[c["metadata"] for c in part])
    store = {"index_id": index_id, "chunks": {c["chunk_id"]: {k: c[k] for k in (
        "chunk_id", "document_id", "title", "title_orig", "text", "token_count", "kind", "part", "parts",
        "section", "spans", "metadata")} for c in chunks}}
    CHUNK_STORE.write_text(json.dumps(store, ensure_ascii=False), encoding="utf-8")
    excluded = [{"path": r["path"], "id": r["id"], "reason": r["reason"]}
                for r in D.load_inventory() if r["status"] == "exclude"]
    manifest = {
        "index_id": index_id, "created_at": now(), "collection": COLLECTION, "metric": PROFILE["metric"],
        "store": rel(STORE_DIR), "profile": PROFILE, "profile_sha256": sha_json(PROFILE),
        "model": {"model_id": MODEL_ID, "local_path": rel(MODEL_DIR), "device": str(model.device),
                  "dimension": model.get_sentence_embedding_dimension(), "files_sha256": hashes},
        "inventory_sha256": state["inventory_sha256"], "documents": state["documents"],
        "document_count": len(docs_meta), "chunk_count": len(chunks),
        "chunks_per_document": {d["document_id"]: d["chunks"] for d in docs_meta},
        "excluded": excluded, "excluded_count": len(excluded),
        "chunk_store_sha256": D.sha256_file(CHUNK_STORE),
        "chunks": [{"chunk_id": c["chunk_id"], "chunk_sha256": c["metadata"]["chunk_sha256"],
                    "document_id": c["document_id"]} for c in chunks],
    }
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
    write_technical_passport(manifest)
    tc = [c["token_count"] for c in chunks]
    out = {"status": "indexed", "index_id": index_id, "collection": COLLECTION, "metric": PROFILE["metric"],
           "device": str(model.device), "dimension": manifest["model"]["dimension"],
           "document_count": len(docs_meta), "chunk_count": len(chunks), "excluded_count": len(excluded),
           "token_count_max": max(tc), "token_count_limit": PROFILE["chunk_token_limit"],
           "manifest": rel(MANIFEST), "technical_passport": "evidence/technical-passport.json"}
    append_history({"event": "index", "at": now(), **out})
    return out


def write_chunks_evidence() -> dict:
    model_tc = M.token_count
    chunks, docs_meta = D.build_chunks(model_tc)
    EVIDENCE_DIR.mkdir(exist_ok=True)
    out = EVIDENCE_DIR / "chunks.json"
    out.write_text(json.dumps({"profile": PROFILE, "chunks": [{k: v for k, v in c.items() if k != "embedding_text"}
                                                              for c in chunks]}, ensure_ascii=False, indent=1),
                   encoding="utf-8")
    # дословность: каждый span текста чанка совпадает с подготовленным текстом фрагмента
    bad = [c["chunk_id"] for c in chunks for s in c["spans"] if c["text"][s["start"]:s["end"]] != s["text_ru"]]
    return {"status": "chunks_written", "path": rel(out), "documents": len(docs_meta), "chunks": len(chunks),
            "token_count_max": max(c["token_count"] for c in chunks), "verbatim_errors": bad}


def write_technical_passport(manifest: dict):
    import importlib.metadata as md

    libs = {}
    for name in ("sentence-transformers", "transformers", "huggingface-hub", "chromadb", "numpy", "tokenizers",
                 "torch", "sentencepiece", "safetensors"):
        try:
            libs[name] = md.version(name)
        except md.PackageNotFoundError:
            libs[name] = None
    try:
        interp = Path(sys.executable).resolve().relative_to(ROOT).as_posix()
    except ValueError:
        interp = sys.executable
    passport = {
        "written_at": now(), "os": platform.platform(), "system": platform.system(),
        "architecture": platform.machine(), "python": sys.version, "interpreter": interp, "libraries": libs,
        "model_id": MODEL_ID, "model_path": manifest["model"]["local_path"], "device": manifest["model"]["device"],
        "dimension": manifest["model"]["dimension"], "model_files_sha256": manifest["model"]["files_sha256"],
        "prefixes": {"passage": PROFILE["passage_prefix"], "query": PROFILE["query_prefix"]},
        "normalization": PROFILE["text_normalization"], "chunker": PROFILE["chunker"],
        "chunk_rule": PROFILE["chunk_rule"], "chunk_token_limit": PROFILE["chunk_token_limit"],
        "chunk_overlap": PROFILE["chunk_overlap"],
        "line_rule": "line_start/line_end — строки md/txt или номера строк csv; для pdf/docx/xlsx 0, точное место — в locator и spans",
        "collection": manifest["collection"], "metric": manifest["metric"], "index_id": manifest["index_id"],
        "document_count": manifest["document_count"], "chunk_count": manifest["chunk_count"],
        "inventory_sha256": manifest["inventory_sha256"],
        "documents_sha256": {d["document_id"]: d["document_sha256"] for d in manifest["documents"]},
    }
    EVIDENCE_DIR.mkdir(exist_ok=True)
    (EVIDENCE_DIR / "technical-passport.json").write_text(json.dumps(passport, ensure_ascii=False, indent=1),
                                                          encoding="utf-8")


# ---------------------------------------------------------------- актуальность

def check_index(check_model: bool = True) -> dict:
    if not MANIFEST.exists() or not CHUNK_STORE.exists():
        raise StaleIndex("индекс не построен: выполните python -m rag_demo index")
    man = json.loads(MANIFEST.read_text(encoding="utf-8"))
    reasons = []
    if man["profile"] != PROFILE:
        reasons.append("изменён профиль построения эмбеддингов/нарезки")
    state = corpus_state()
    if state["inventory_sha256"] != man["inventory_sha256"]:
        reasons.append("изменён inventory.csv")
    cur = {d["document_id"]: d for d in state["documents"]}
    old = {d["document_id"]: d for d in man["documents"]}
    if cur.keys() != old.keys():
        reasons.append(f"изменён список include: +{sorted(cur.keys() - old.keys())} -{sorted(old.keys() - cur.keys())}")
    for k in cur.keys() & old.keys():
        for f, label in (("document_sha256", "исходник"), ("prepared_sha256", "подготовленный текст"),
                         ("translation_inputs", "перевод/решения")):
            if cur[k][f] != old[k][f]:
                reasons.append(f"{cur[k]['source_path']}: изменён {label}")
    if D.sha256_file(CHUNK_STORE) != man["chunk_store_sha256"]:
        reasons.append("изменено хранилище фрагментов .rag_store/chunks.json")
    if check_model:
        miss = M.missing_files()
        if miss:
            reasons.append(f"нет файлов модели: {miss}")
        elif M.model_hashes() != man["model"]["files_sha256"]:
            reasons.append("изменены файлы модели (SHA-256 не совпадает с manifest)")
    if reasons:
        raise StaleIndex("индекс устарел (stale): " + "; ".join(reasons) + ". Выполните python -m rag_demo index")
    cl = client()
    if COLLECTION not in [c.name for c in cl.list_collections()]:
        raise StaleIndex(f"коллекция {COLLECTION} отсутствует: выполните python -m rag_demo index")
    col = cl.get_collection(COLLECTION, embedding_function=None)
    if col.count() != man["chunk_count"] or (col.metadata or {}).get("index_id") != man["index_id"]:
        raise StaleIndex("коллекция не соответствует manifest: выполните python -m rag_demo index")
    return man


def load_chunk_store() -> dict:
    return json.loads(CHUNK_STORE.read_text(encoding="utf-8"))["chunks"]


# ---------------------------------------------------------------- поиск

def provenance(chunk: dict) -> list[dict]:
    """Происхождение каждого подготовленного фрагмента внутри чанка: оригинал и точное место."""
    out = []
    for s in chunk["spans"]:
        item = {"fragment_id": s["fragment_id"], "role": s["role"], "start": s["start"], "end": s["end"],
                "locator": s["locator"], "locator_text": s["locator_text"],
                "section_orig": s.get("section"), "section_ru": s.get("section_ru"),
                "translation": s["translation"]}
        if s.get("text_orig") and s["translation"] == "translated":
            item["text_orig"] = s["text_orig"]
        if s.get("cells"):
            item["cells"] = [{k: c.get(k) for k in ("ref", "col", "header", "header_ru", "value", "value_ru")
                              if c.get(k) is not None} for c in s["cells"]]
        if s.get("also_in"):
            item["also_in"] = s["also_in"]
        if s.get("similar_to"):
            item["similar_to"] = s["similar_to"]
        item["handling"] = s.get("handling")
        out.append(item)
    return out


_BM25 = {}


def _toks(text: str, stem: int) -> list[str]:
    """Слова длиннее 2 символов, усечённые до stem символов (грубая замена стемминга для русского)."""
    return [w[:stem] for w in re.findall(r"\w+", text.lower()) if len(w) > 2]


def bm25_scores(question: str, chunk_ids: list[str], store: dict, stem: int, k1: float = 1.2, b: float = 0.75) -> dict:
    key = (stem, len(store))
    if key not in _BM25:
        docs = {cid: _toks(c["title"] + " " + c["text"], stem) for cid, c in store.items()}
        df = {}
        for ts in docs.values():
            for w in set(ts):
                df[w] = df.get(w, 0) + 1
        _BM25[key] = (docs, df, sum(map(len, docs.values())) / len(docs))
    docs, df, avg = _BM25[key]
    n = len(docs)
    q = set(_toks(question, stem))
    out = {}
    for cid in chunk_ids:
        ts, s = docs[cid], 0.0
        for w in q:
            f = ts.count(w)
            if f:
                s += math.log(1 + (n - df[w] + 0.5) / (df[w] + 0.5)) * f * (k1 + 1) / (f + k1 * (1 - b + b * len(ts) / avg))
        out[cid] = s
    return out


def validate_question(question: str, top_k) -> tuple[str, int]:
    if question is None or not question.strip():
        raise RetrievalError("пустой вопрос")
    if isinstance(top_k, bool) or not isinstance(top_k, int) or top_k < 1:
        raise RetrievalError(f"top_k должен быть положительным целым, получено {top_k!r}")
    n = M.token_count(PROFILE["query_prefix"] + question)
    if n > PROFILE["query_token_limit"]:
        raise RetrievalError(f"вопрос длиннее лимита: {n} токенов > {PROFILE['query_token_limit']} "
                             "(вместе с query: и спецтокенами); сократите вопрос")
    return question, n


def retrieve(question: str, role: str, top_k: int | None = None, output: str | None = None) -> tuple[dict, Path]:
    pol = P.load_policy()
    if top_k is None:
        top_k = pol["top_k"]
    if role not in pol["roles"]:
        raise RetrievalError(f"неизвестная роль {role!r}; допустимы {pol['roles']}")
    out_path = Path(output) if output else None
    if out_path is not None:
        out_path = out_path if out_path.is_absolute() else ROOT / out_path
        if out_path.exists():
            raise RetrievalError(f"{rel(out_path)} уже существует — выберите новое имя, прежние результаты не перезаписываются")
    man = check_index()
    question, q_tokens = validate_question(question, top_k)
    access = D.load_access()
    indexed_docs = set(man["chunks_per_document"])
    allowed = sorted(d for d in indexed_docs if role in access.get(d, []))
    denied = sorted(indexed_docs - set(allowed))
    n_allowed = sum(man["chunks_per_document"][d] for d in allowed)
    lex_extra = pol.get("lexical_extra", 0)
    pool = max(top_k, pol.get("lexical_pool", top_k)) if lex_extra else top_k
    n_results = min(pool, n_allowed)
    store = load_chunk_store()
    col = client().get_collection(COLLECTION, embedding_function=None)
    qv = M.encode_query(question).tolist()

    candidates = []
    if n_results:
        # фильтр по роли выполняется в Chroma до получения текстов
        res = col.query(query_embeddings=[qv], n_results=n_results, where={"document_id": {"$in": allowed}},
                        include=["documents", "metadatas", "distances"])
        for cid, text, meta, dist in zip(res["ids"][0], res["documents"][0], res["metadatas"][0], res["distances"][0]):
            if meta["document_id"] not in allowed:  # защитная проверка
                raise RetrievalError("фильтр доступа нарушен")
            candidates.append({"chunk_id": cid, "text": text, "metadata": meta, "distance": round(float(dist), 6)})
    thr = pol["retrieval_threshold"]
    within = [c for c in candidates if c["distance"] <= thr]
    admitted = within[:top_k]
    lexical_added = []
    if lex_extra and len(within) > top_k:
        # гибридное дополнение: среди кандидатов, прошедших порог, но не вошедших в top_k по вектору,
        # добавляются лучшие по BM25 (совпадение слов вопроса). Векторный top_k не меняется.
        scores = bm25_scores(question, [c["chunk_id"] for c in within], store, pol.get("lexical_stem", 6))
        rest = sorted((c for c in within[top_k:] if scores[c["chunk_id"]] > 0),
                      key=lambda c: -scores[c["chunk_id"]])[:lex_extra]
        lexical_added = [{"chunk_id": c["chunk_id"], "distance": c["distance"],
                          "bm25": round(scores[c["chunk_id"]], 4),
                          "dense_rank": within.index(c) + 1} for c in rest]
        admitted = admitted + rest
    admitted_ids = {c["chunk_id"] for c in admitted}
    rejected = [c for c in candidates if c["distance"] > thr]
    not_selected = [c for c in within if c["chunk_id"] not in admitted_ids]

    probe = {"checked": bool(denied), "denied_documents": len(denied), "nearest_distance": None,
             "within_probe": 0, "probe_distance": pol["authorization_probe_distance"]}
    if denied:
        n_denied = sum(man["chunks_per_document"][d] for d in denied)
        pr = col.query(query_embeddings=[qv], n_results=min(top_k, n_denied),
                       where={"document_id": {"$in": denied}}, include=["distances"])
        dists = [round(float(x), 6) for x in pr["distances"][0]]  # закрытые ID, тексты и названия не сохраняются
        probe["nearest_distance"] = min(dists) if dists else None
        probe["within_probe"] = sum(d <= pol["authorization_probe_distance"] for d in dists)
        probe["closer_than_best_admitted"] = sum(d < (admitted[0]["distance"] if admitted else 9) for d in dists)
    best_allowed = candidates[0]["distance"] if candidates else None
    rule = pol.get("forbidden_rule", "probe_only")
    probe["rule"] = rule
    if admitted:
        context_state = "available"
    elif probe["within_probe"] and (rule == "probe_only" or best_allowed is None
                                    or probe["nearest_distance"] < best_allowed):
        # probe_and_closer_than_allowed: закрытый фрагмент ближе probe_distance И ближе лучшего разрешённого
        context_state = "forbidden"
    else:
        context_state = "empty"

    hits = []
    for rank, c in enumerate(admitted, start=1):
        ch = store[c["chunk_id"]]
        if ch["text"] != c["text"]:
            raise StaleIndex(f"{c['chunk_id']}: текст в коллекции не совпадает с хранилищем фрагментов")
        hits.append({"rank": rank, "chunk_id": c["chunk_id"], "text": c["text"], "metadata": c["metadata"],
                     "distance": c["distance"], "provenance": provenance(ch)})
    context = "\n\n".join(f"[{h['chunk_id']}] {h['metadata']['title']} — {h['metadata']['source_path']}, "
                          f"{h['metadata']['locator']}\n{h['text']}" for h in hits)
    query_id = "q-" + stamp_id()
    EVIDENCE_DIR.mkdir(exist_ok=True)
    trace_path = EVIDENCE_DIR / f"retrieval-trace-{query_id}.json"
    if out_path is None:
        out_path = EVIDENCE_DIR / f"retrieval-{query_id}.json"
    result = {
        "status": "retrieval_only", "query_id": query_id, "created_at": now(), "index_id": man["index_id"],
        "question": question, "question_tokens": q_tokens, "role": role, "top_k": top_k,
        "policy": P.snapshot(pol), "collection": COLLECTION, "metric": PROFILE["metric"],
        "context_state": context_state,
        "filtering": {
            "role": role, "allowed_documents": len(allowed), "n_results": n_results,
            "candidates": len(candidates), "admitted": len(admitted),
            "rejected_by_threshold": [{"chunk_id": c["chunk_id"], "distance": c["distance"]} for c in rejected],
            "retrieval_threshold": thr, "restricted_probe": probe,
            "best_allowed_distance": best_allowed,
            "lexical_added": lexical_added,
            "within_threshold_not_selected": len(not_selected),
            "note": "available не доказывает полноту; empty не является технической ошибкой; "
                    "forbidden не раскрывает закрытый источник",
        },
        "hits": hits, "context": context, "context_chunk_ids": [h["chunk_id"] for h in hits],
        "retrieval_trace_path": rel(trace_path), "output_path": rel(out_path),
    }
    trace = {"query_id": query_id, "created_at": result["created_at"], "question": question, "role": role,
             "top_k": top_k, "policy": result["policy"], "profile": PROFILE, "index_id": man["index_id"],
             "allowed_document_ids": allowed, "denied_document_count": len(denied),
             "candidates": [{"chunk_id": c["chunk_id"], "distance": c["distance"],
                             "document_id": c["metadata"]["document_id"], "admitted": c["chunk_id"] in admitted_ids,
                             "within_threshold": c["distance"] <= thr,
                             "text": c["text"]} for c in candidates],
             "restricted_probe": probe, "context_state": context_state, "result_path": rel(out_path)}
    trace_path.write_text(json.dumps(trace, ensure_ascii=False, indent=1), encoding="utf-8")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(result, ensure_ascii=False, indent=1)
    out_path.write_text(text, encoding="utf-8")
    append_history({"event": "retrieve", "at": result["created_at"], "query_id": query_id, "question": question,
                    "role": role, "top_k": top_k, "policy_version": pol["version"], "index_id": man["index_id"],
                    "context_state": context_state,
                    "hits": [{"chunk_id": h["chunk_id"], "distance": h["distance"],
                              "source_path": h["metadata"]["source_path"], "locator": h["metadata"]["locator"]}
                             for h in hits],
                    "output": rel(out_path), "trace": rel(trace_path)})
    return result, out_path
