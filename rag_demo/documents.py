"""Инвентарь, политика доступа и структурная нарезка подготовленного корпуса.

Источник текста — corpus/prepared/<path>.json (результат scripts/prepare.py): русский
оригинал или проверенный перевод каждого фрагмента вместе с оригиналом и точным местом.
В индекс попадают только документы со статусом include в inventory.csv и только
фрагменты с index=true (копии дублей, карантин и служебные заголовки отсеяны до эмбеддингов).
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
from pathlib import Path

from .config import ACCESS, DOCUMENTS_DIR, INVENTORY, PREPARED_DIR, PROFILE, REGISTRY, ROOT

INVENTORY_COLUMNS = ["path", "id", "title", "owner", "version", "updated", "status", "reason"]


class CorpusError(RuntimeError):
    pass


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def read_csv(path: Path) -> list[dict]:
    # utf-8-sig: допустимый BOM
    with path.open(encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def load_inventory() -> list[dict]:
    rows = read_csv(INVENTORY)
    if not rows or list(rows[0].keys()) != INVENTORY_COLUMNS:
        raise CorpusError(f"inventory.csv: столбцы должны быть {INVENTORY_COLUMNS}")
    return rows


def load_registry() -> dict[str, dict]:
    return {r["path"]: r for r in read_csv(REGISTRY)}


def load_access() -> dict[str, list[str]]:
    """doc_id -> роли. Политика хранится вне индекса и применяется при каждом запросе."""
    if not ACCESS.exists():
        raise CorpusError("нет access.csv — выполните python -m rag_demo access-sync")
    out = {}
    for r in read_csv(ACCESS):
        roles = [x for x in r["roles"].split(";") if x]
        if not roles:
            raise CorpusError(f"access.csv: у {r['document_id']} нет ролей")
        out[r["document_id"]] = roles
    return out


def access_sync() -> dict:
    """Создать access.csv из реестра (поле access) для включённых документов."""
    reg = load_registry()
    rows = []
    for inv in load_inventory():
        if inv["status"] != "include":
            continue
        roles = reg[inv["path"]]["access"].split(",")
        rows.append({"document_id": inv["id"], "path": inv["path"], "roles": ";".join(roles),
                     "basis": "registry/registry.csv: access (по правилам доступа реестра)"})
    with ACCESS.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["document_id", "path", "roles", "basis"])
        w.writeheader()
        w.writerows(rows)
    return {"status": "access_written", "path": "access.csv", "documents": len(rows),
            "lead_only": [r["document_id"] for r in rows if r["roles"] == "support_lead"]}


def prepared_path(source_path: str) -> Path:
    return PREPARED_DIR / (source_path[len("documents/"):] + ".json")


def included_documents() -> list[dict]:
    """Проверенный список include: inventory + реестр + подготовленный документ."""
    reg = load_registry()
    docs = []
    for inv in load_inventory():
        if inv["status"] != "include":
            continue
        p = prepared_path(inv["path"])
        r = reg[inv["path"]]
        docs.append({"inventory": inv, "registry": r, "prepared_path": p})
    return docs


def validate_docs() -> dict:
    inv = load_inventory()
    sources = sorted(p.relative_to(ROOT).as_posix() for p in DOCUMENTS_DIR.rglob("*") if p.is_file())
    errors = []
    if sorted(r["path"] for r in inv) != sources:
        errors.append("inventory.csv не совпадает со списком файлов documents/")
    for r in inv:
        if not r["path"].startswith("documents/"):
            errors.append(f"{r['path']}: путь вне documents/")
        if r["status"] not in ("include", "exclude") or not r["reason"]:
            errors.append(f"{r['path']}: нет статуса или причины")
    inc = [r for r in inv if r["status"] == "include"]
    ids = [r["id"] for r in inc]
    dup = sorted({i for i in ids if ids.count(i) > 1})
    if dup:
        errors.append(f"повторяющиеся id у include: {dup}")
    warnings = []
    for r in inc:
        if not r["id"]:
            errors.append(f"{r['path']}: пустое поле id")
        if not r["title"]:
            warnings.append(f"{r['path']}: в документе нет названия — в индексе используется имя файла")
    reg = load_registry()
    try:
        access = load_access()
    except CorpusError as e:
        access = {}
        errors.append(str(e))
    for r in inc:
        p = prepared_path(r["path"])
        if not p.exists():
            errors.append(f"{r['path']}: нет подготовленного документа {p.relative_to(ROOT).as_posix()}")
            continue
        doc = json.loads(p.read_text(encoding="utf-8"))
        if doc["source_sha256"] != sha256_file(ROOT / r["path"]):
            errors.append(f"{r['path']}: исходник изменился после подготовки — повторите scripts/prepare.py")
        if r["id"] not in access:
            errors.append(f"{r['path']}: нет строки в access.csv")
        if reg[r["path"]]["lang"] != "ru" and reg[r["path"]]["translation"] != "проверен":
            errors.append(f"{r['path']}: перевод не проверен")
    excluded = [{"path": r["path"], "reason": r["reason"]} for r in inv if r["status"] == "exclude"]
    return {"status": "documents_valid" if not errors else "documents_invalid",
            "documents_total": len(inv), "included": len(inc), "excluded": len(excluded),
            "excluded_list": excluded, "warnings": warnings, "errors": errors}


# ---------------------------------------------------------------- нарезка

def _sentences(text: str) -> list[str]:
    """Разбить по границам предложений, сохраняя текст дословно (части склеиваются обратно в text)."""
    parts = re.split(r"(?<=[.!?…;])(\s+)", text)
    out, cur = [], ""
    for i, p in enumerate(parts):
        cur += p
        if i % 2 == 1:  # разделитель
            out.append(cur)
            cur = ""
    if cur:
        out.append(cur)
    return out


def _section_of(f: dict) -> str:
    return f.get("section_ru") or ""


def build_chunks(count_tokens) -> tuple[list[dict], list[dict]]:
    """Вернуть (chunks, documents). count_tokens(text) учитывает спецтокены E5."""
    limit = PROFILE["chunk_token_limit"]
    prefix = PROFILE["passage_prefix"]
    chunks, docs_meta = [], []
    for d in included_documents():
        inv, reg = d["inventory"], d["registry"]
        doc = json.loads(d["prepared_path"].read_text(encoding="utf-8"))
        frags = doc["fragments"]
        title = reg["title_ru"] or inv["title"] or Path(inv["path"]).stem
        title_source = "registry.title_ru" if reg["title_ru"] else ("inventory.title" if inv["title"] else "имя файла")
        doc_id = inv["id"]
        head = prefix + title + "\n"

        def tokens(text: str) -> int:
            return count_tokens(head + text)

        # единицы: (section, [piece]) где piece = {fragment, text}
        units: list[tuple[str, list[dict], str]] = []  # (section, pieces, kind: prose|record)
        by_id = {f["fragment_id"]: f for f in frags}
        sheet_title = {}
        for f in frags:
            if f["kind"] == "sheet_title":
                sheet_title[f["locator"].get("sheet")] = f
        cur_sec, cur = None, []
        heading_for, last_heading = {}, None
        for f in frags:  # заголовок раздела — ближайший предшествующий heading-фрагмент
            if f["kind"] == "heading":
                last_heading = f
            elif f.get("section_ru") and f["section_ru"] not in heading_for and last_heading:
                heading_for[f["section_ru"]] = last_heading
        for f in frags:
            if not f.get("index"):
                continue
            if f["kind"] == "record":
                if cur:
                    units.append((cur_sec, cur, "prose"))
                    cur, cur_sec = [], None
                pieces = []
                st = sheet_title.get(f["locator"].get("sheet")) if f["format"] == "xlsx" else None
                if st:
                    pieces.append({"fragment": st, "text": f"Лист «{f['context'].get('sheet_ru') or f['locator']['sheet']}»: {st['text_ru']}", "role": "context"})
                pieces.append({"fragment": f, "text": f["text_ru"], "role": "content"})
                units.append((_section_of(f), pieces, "record"))
                continue
            sec = _section_of(f)
            if cur and sec != cur_sec:
                units.append((cur_sec, cur, "prose"))
                cur = []
            if not cur:
                cur_sec = sec
                h = heading_for.get(sec) if sec else None
                if h and f["kind"] != "sheet_note":
                    cur.append({"fragment": h, "text": h["text_ru"], "role": "heading"})
            cur.append({"fragment": f, "text": f["text_ru"], "role": "content"})
        if cur:
            units.append((cur_sec, cur, "prose"))

        # упаковка в чанки ≤ limit токенов без перекрытия
        doc_chunks = []
        for sec, pieces, kind in units:
            heading = [p for p in pieces if p["role"] == "heading"]
            body = [p for p in pieces if p["role"] != "heading"]
            # слишком длинный фрагмент делится по предложениям
            split_body = []
            for p in body:
                if tokens(p["text"]) <= limit:
                    split_body.append(p)
                    continue
                sents, buf, part = _sentences(p["text"]), "", 1
                for s in sents:
                    if buf and tokens(buf + s) > limit:
                        split_body.append({**p, "text": buf.rstrip(), "part": part})
                        buf, part = "", part + 1
                    buf += s
                if buf.strip():
                    split_body.append({**p, "text": buf.rstrip(), "part": part})
            groups, g = [], list(heading)
            for p in split_body:
                trial = "\n\n".join(x["text"] for x in g + [p])
                if [x for x in g if x["role"] != "heading"] and tokens(trial) > limit:
                    groups.append(g)
                    g = list(heading)
                g.append(p)
            if g:
                groups.append(g)
            for gi, g in enumerate(groups):
                doc_chunks.append((sec, kind, g, gi + 1, len(groups)))

        for n, (sec, kind, g, part, parts) in enumerate(doc_chunks, start=1):
            text, spans, pos = "", [], 0
            for i, p in enumerate(g):
                if i:
                    text += "\n\n"
                start = len(text)
                text += p["text"]
                f = p["fragment"]
                spans.append({
                    "fragment_id": f["fragment_id"], "start": start, "end": len(text), "role": p["role"],
                    "part": p.get("part"), "kind": f["kind"], "locator": f["locator"],
                    "locator_text": f["locator_text"], "section": f.get("section"), "section_ru": f.get("section_ru"),
                    "text_ru": p["text"], "text_orig": f.get("text_orig"), "translation": f.get("translation"),
                    "cells": f.get("cells"), "context": f.get("context"), "also_in": f.get("also_in"),
                    "similar_to": f.get("similar_to"), "handling": f.get("handling"),
                })
            content = [s for s in spans if s["role"] == "content"]
            lines = [s["locator"]["lines"] for s in content if "lines" in s["locator"]]
            rows = [s["locator"]["csv_row"] for s in content if "csv_row" in s["locator"]]
            pages = [s["locator"]["page"] for s in content if "page" in s["locator"]] + \
                    [s["locator"]["page_end"] for s in content if "page_end" in s["locator"]]
            line_start = min(l[0] for l in lines) if lines else (min(rows) if rows else 0)
            line_end = max(l[1] for l in lines) if lines else (max(rows) if rows else 0)
            cid = f"{doc_id}::chunk-{n:02d}"
            chunks.append({
                "chunk_id": cid, "document_id": doc_id, "title": title, "title_orig": inv["title"],
                "text": text, "embedding_text": title + "\n" + text,
                "token_count": tokens(text), "kind": kind, "part": part, "parts": parts,
                "section": sec or "(введение)", "spans": spans,
                "metadata": {
                    "document_id": doc_id, "title": title, "title_orig": inv["title"],
                    "title_source": title_source,
                    "source_path": inv["path"], "section": sec or "(введение)",
                    "version": inv["version"], "updated": inv["updated"], "owner": inv["owner"],
                    "line_start": line_start, "line_end": line_end,
                    "page_start": min(pages) if pages else 0, "page_end": max(pages) if pages else 0,
                    "locator": "; ".join(dict.fromkeys(s["locator_text"] for s in content)),
                    "format": doc["format"] if "format" in doc else inv["path"].rsplit(".", 1)[-1],
                    "source_lang": reg["lang"], "is_translation": reg["lang"] != "ru",
                    "document_sha256": doc["source_sha256"],
                    "chunk_sha256": sha256_bytes(text.encode("utf-8")),
                    "token_count": tokens(text),
                    "fragment_ids": ",".join(s["fragment_id"] for s in spans),
                    "trust": reg["trust"], "conflict_group": reg["conflict_group"] or "",
                    "related": reg["related"] or "",
                },
            })
        docs_meta.append({"document_id": doc_id, "source_path": inv["path"],
                          "document_sha256": doc["source_sha256"],
                          "prepared_sha256": sha256_file(d["prepared_path"]),
                          "chunks": len(doc_chunks)})
    for c in chunks:
        if c["token_count"] > limit:
            raise CorpusError(f"{c['chunk_id']}: {c['token_count']} токенов > {limit}")
    return chunks, docs_meta
