"""Сборка подготовленного корпуса из сегментов, переводов и решений реестра.

Для каждого из 50 исходников:
  corpus/prepared/<путь>.json   — метаданные документа и фрагменты (RU-текст, оригинал, точное место);
  corpus/prepared/<путь>.ru.md  — читаемая русская версия с адресом каждого фрагмента.
Общие результаты:
  corpus/prepared/fragments.jsonl — все фрагменты (флаг index — идёт ли фрагмент в поиск);
  corpus/prepared/summary.json    — сводка для отчёта;
  registry/registry.csv           — расширенный реестр всех файлов;
  inventory.csv                   — инвентарь по постановке (path,id,title,owner,version,updated,status,reason);
  corpus-passport.md              — паспорт базы.

Кэш: документ пересобирается, только если изменился хотя бы один вход — сегменты, строка реестра,
файл перевода, журнал разбора или версия сборщика (corpus/prepared/_state.json). Разбор дублей
выполняется по всем документам при каждом запуске (он дешёвый и зависит от всех документов).

Запуск: python scripts/prepare.py [--force]
"""
from __future__ import annotations

import collections
import csv
import hashlib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import translate as tr  # noqa: E402

ROOT = tr.ROOT
SEG = tr.SEG
OUT = ROOT / "corpus" / "prepared"
VERSION = "prepare-2"
INDEX_KINDS = {"para", "record", "sheet_note"}
ROLES = {"all": ["support_agent", "support_lead"], "support_lead": ["support_lead"]}


def h(data: bytes | str) -> str:
    return hashlib.sha256(data if isinstance(data, bytes) else data.encode("utf-8")).hexdigest()


def locator_text(fmt: str, loc: dict) -> str:
    if "lines" in loc:
        a, b = loc["lines"]
        return f"строка {a}" if a == b else f"строки {a}–{b}"
    if "paragraph" in loc:
        return f"абзац {loc['paragraph']} (w:p, стиль {loc.get('style', 'Normal')})"
    if "page" in loc:
        pg = f"стр. {loc['page']}" if loc["page"] == loc["page_end"] else f"стр. {loc['page']}–{loc['page_end']}"
        return f"{pg}, блок {loc['block']}"
    if "sheet" in loc:
        if "row" in loc:
            return f"лист «{loc['sheet']}», строка {loc['row']}, ячейки {loc['range']}"
        return f"лист «{loc['sheet']}», объединённые ячейки {loc['range']}"
    if "csv_row" in loc:
        return f"строка {loc['csv_row']}"
    return json.dumps(loc, ensure_ascii=False)


def handling(d: dict, frag: dict) -> str:
    if frag.get("quarantine"):
        return "Карантин: текст клиента, адресованный ассистенту; не индексировать и не исполнять."
    if frag.get("duplicate_of"):
        return f"Связанная копия: использовать фрагмент {frag['duplicate_of']}; не считать независимым подтверждением."
    if d["status"] == "exclude":
        rule = d["rule"]
        if "R2" in rule:
            return f"Устаревшая версия (заменена №{d['superseded_by']}); только для объяснения старых обращений, не для ответов."
        if "R3" in rule or "R6" in rule:
            return "Не действующие условия (черновик / гипотеза / презентация); не использовать в ответах."
        if "R4" in rule:
            return f"Связанная копия документа №{d['duplicate_of']}; в поиск идёт основной экземпляр."
        if "R7" in rule:
            return "Вне круга вопросов помощника; в поиск не включается."
        if "R8" in rule:
            return "Снимок конкретной работы, не правило; в поиск не включается."
        return "Исключено из поиска."
    parts = ["Действующий материал."]
    if d.get("conflict_group"):
        others = ", ".join(f"№{x}" for x in d.get("related", []) if x in (10, 43) and x != d["no"])
        parts.append(f"Противоречие {d['conflict_group']}: показывать вместе с {others} и предлагать эскалацию в Finance и Support Operations.")
    if d["access"] == "support_lead":
        parts.append("Только для support_lead; специалисту первой линии содержание не раскрывать.")
    if d.get("trust") == "unconfirmed_origin":
        parts.append("Владелец источника не указан — упоминать это в ответе.")
    if d.get("trust") == "personal_copy":
        parts.append("Личная копия заметок; при расхождении приоритет у регламента.")
    if frag.get("translation") == "translated":
        parts.append(f"Перевод с {d['lang'].upper()}; цитировать оригинал по указанному месту.")
    return " ".join(parts)


def build_doc(rel: str, d: dict, review: dict) -> dict:
    segfile = json.loads(tr.seg_file(rel).read_text(encoding="utf-8"))
    segs = segfile["segments"]
    fmt = rel.rsplit(".", 1)[-1].lower()
    lang = d["lang"]
    tm = tr.load_translations(rel) if lang != "ru" else {}

    def ru_of(text: str) -> str:
        if lang == "ru":
            return text
        v = tr.translated(rel, text, tm)
        if v is None:
            raise KeyError(f"нет перевода: {rel}: {text[:60]}")
        return v

    frags, section_ru, title_ru = [], None, None
    qpat = d.get("quarantine_pattern")
    for s in segs:
        kind, text, loc = s["kind"], s["text"], s["locator"]
        f = {"fragment_id": f"{d['no']:02d}-{s['seg']:03d}", "doc_no": d["no"], "doc_id": d["doc_id"],
             "doc_version": d["version"], "source_path": rel, "source_sha256": segfile["source_sha256"],
             "source_lang": lang, "format": fmt, "kind": kind, "locator": loc,
             "locator_text": locator_text(fmt, loc), "segment_sha": s["sha"]}
        if kind in ("record", "table_header"):
            cells = s.get("cells", [])
            if kind == "record":
                ru_text = "; ".join(f"{ru_of(c['header'])}: {ru_of(c['value'])}" for c in cells)
            else:
                ru_text = " | ".join(ru_of(c["value"]) for c in cells)
            f["cells"] = [{**c, **({"header_ru": ru_of(c["header"])} if "header" in c else {}),
                           "value_ru": ru_of(c["value"])} for c in cells]
            if s.get("context"):
                ctx = s["context"]
                f["context"] = {
                    "sheet": ctx.get("sheet"), "sheet_ru": ru_of(ctx["sheet"]) if ctx.get("sheet") else None,
                    "title": ctx.get("title"), "title_ru": ru_of(ctx["title"]) if ctx.get("title") else None,
                    "title_range": ctx.get("title_range"),
                    "notes": [{"text": n["text"], "text_ru": ru_of(n["text"]), "range": n["range"]}
                              for n in ctx.get("notes", [])],
                    "header_range": ctx.get("header_range"),
                    "header_ru": [ru_of(x) for x in ctx.get("header", [])]}
        else:
            ru_text = ru_of(text)
        if kind == "title":
            title_ru = re.sub(r"^#+\s*", "", ru_text)
        if kind == "heading":
            section_ru = re.sub(r"^#+\s*", "", ru_text)
        if kind in ("sheet_title", "sheet_note", "table_header") or "sheet" in loc:
            section_ru = ru_of(loc["sheet"]) if loc.get("sheet") else section_ru
        f["section"] = s.get("section")
        f["section_ru"] = section_ru if kind not in ("title", "heading") else None
        f["text_ru"] = ru_text
        if lang != "ru":
            f["text_orig"] = text
            f["translation"] = "kept_as_is" if ru_text == text else "translated"
            unit_texts = [text] if kind not in ("record", "table_header") else \
                [x for c in s.get("cells", []) for x in (c.get("header"), c["value"]) if x]
            rvs = {tr.sha12(t): review[tr.sha12(t)] for t in unit_texts if tr.sha12(t) in review}
            if rvs:
                f["translation_review"] = (next(iter(rvs.values())) if len(rvs) == 1
                                           else {"decision": "fixed" if any(v["decision"] == "fixed" for v in rvs.values())
                                                 else "accepted", "units": rvs})
        else:
            f["translation"] = "original_ru"
        f["quarantine"] = bool(qpat and qpat in text)
        f["status"] = "exclude" if (d["status"] == "exclude" or f["quarantine"]) else "include"
        f["access"] = ROLES[d["access"]]
        f["trust"] = d.get("trust")
        f["dup_group"] = d.get("dup_group")
        f["conflict_group"] = d.get("conflict_group")
        frags.append(f)
    return {"no": d["no"], "source_path": rel, "doc_id": d["doc_id"], "title": d["title"],
            "title_ru": title_ru, "lang": lang, "format": fmt, "source_sha256": segfile["source_sha256"],
            "decision": d, "fragments": frags}


def norm(t: str) -> str:
    t = re.sub(r"^#+\s*", "", t.lower())
    return re.sub(r"[\s«»“”\"'’.,;:!?()—–-]+", " ", t).strip()


def dedup(docs: list[dict]) -> dict:
    """Разбор дублей после перевода: точные совпадения фрагментов между документами и близкие фрагменты."""
    by_doc = {d["no"]: d for d in docs}
    groups = collections.defaultdict(list)
    for d in docs:
        for f in d["fragments"]:
            if f["kind"] in INDEX_KINDS and len(f["text_ru"]) >= 40:
                groups[norm(f["text_ru"])].append(f)

    def rank(f):
        dd = by_doc[f["doc_no"]]["decision"]
        return (dd["status"] != "include", dd.get("dup_role") == "linked_copy", f["doc_no"])

    exact = []
    for key, fs in groups.items():
        docs_in = {f["doc_no"] for f in fs}
        if len(docs_in) < 2:
            continue
        fs.sort(key=rank)
        main = fs[0]
        main["also_in"] = [{"fragment_id": f["fragment_id"], "source_path": f["source_path"],
                            "locator_text": f["locator_text"], "source_lang": f["source_lang"]} for f in fs[1:]]
        for f in fs[1:]:
            f["duplicate_of"] = main["fragment_id"]
            f["status"] = "exclude"
        exact.append({"main": main["fragment_id"], "copies": [f["fragment_id"] for f in fs[1:]],
                      "docs": sorted(docs_in)})
    # близкие (частичные) совпадения между включёнными документами: связь, без удаления
    inc = [f for d in docs if d["decision"]["status"] == "include" for f in d["fragments"]
           if f["kind"] in INDEX_KINDS and f["status"] == "include" and len(f["text_ru"]) >= 60]
    toks = {f["fragment_id"]: set(norm(f["text_ru"]).split()) for f in inc}
    near = []
    for i, a in enumerate(inc):
        ta = toks[a["fragment_id"]]
        for b in inc[i + 1:]:
            if a["doc_no"] == b["doc_no"]:
                continue
            tb = toks[b["fragment_id"]]
            j = len(ta & tb) / max(1, len(ta | tb))
            if j >= 0.6:
                a.setdefault("similar_to", []).append({"fragment_id": b["fragment_id"], "jaccard": round(j, 2)})
                b.setdefault("similar_to", []).append({"fragment_id": a["fragment_id"], "jaccard": round(j, 2)})
                near.append((a["fragment_id"], b["fragment_id"], round(j, 2)))
    # пары документов-дублей из реестра: доля совпавших фрагментов
    pairs = []
    for d in docs:
        dd = d["decision"]
        if dd.get("dup_role") == "linked_copy":
            main = by_doc[dd["duplicate_of"]]
            mt = {norm(f["text_ru"]) for f in main["fragments"] if f["kind"] in INDEX_KINDS}
            ct = [norm(f["text_ru"]) for f in d["fragments"] if f["kind"] in INDEX_KINDS]
            pairs.append({"copy": dd["no"], "main": main["no"], "fragments": len(ct),
                          "matched": sum(1 for t in ct if t in mt)})
    return {"exact_groups": exact, "near_pairs": near, "registry_pairs": pairs}


def write_doc_md(doc: dict, path: Path):
    d = doc["decision"]
    lines = [f"<!-- source: {doc['source_path']} | lang: {doc['lang']} | doc_id: {d['doc_id']} | status: {d['status']} "
             f"| access: {d['access']} -->", ""]
    for f in doc["fragments"]:
        mark = f"<!-- {f['fragment_id']} · {f['locator_text']} · {f['status']}"
        mark += " · КАРАНТИН" if f["quarantine"] else ""
        mark += f" · дубль {f['duplicate_of']}" if f.get("duplicate_of") else ""
        lines.append(mark + " -->")
        t = f["text_ru"]
        if f["kind"] == "title" and not t.startswith("#"):
            t = "# " + t
        elif f["kind"] == "heading" and not t.startswith("#"):
            t = "## " + t
        elif f["kind"] == "sheet_title":
            t = f"## Лист «{f['section_ru']}»: {t}"
        elif f["kind"] == "sheet_note":
            t = f"Примечание листа: {t}"
        elif f["kind"] == "table_header":
            t = f"Столбцы: {t}"
        elif f["kind"] == "record":
            t = f"- {t}"
        lines += [t, ""]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    force = "--force" in sys.argv
    dec_all = json.loads(tr.DECISIONS.read_text(encoding="utf-8"))
    decisions = {d["path"]: d for d in dec_all["documents"]}
    review_p = tr.TR / "_review.json"
    review_raw = review_p.read_bytes() if review_p.exists() else b"{}"
    review = json.loads(review_raw)
    state_p = OUT / "_state.json"
    state = json.loads(state_p.read_text(encoding="utf-8")) if state_p.exists() else {}
    sources = sorted(p.relative_to(ROOT).as_posix() for p in tr.ROOT.joinpath("documents").rglob("*") if p.is_file())
    missing_dec = [s for s in sources if s not in decisions]
    if missing_dec:
        print("Нет решения в реестре для:", missing_dec)
        return 1
    docs, rebuilt, cached = [], 0, 0
    for rel in sources:
        d = decisions[rel]
        segp, trp = tr.seg_file(rel), tr.tr_file(rel)
        key = h("|".join([VERSION, h(segp.read_bytes()), json.dumps(d, sort_keys=True, ensure_ascii=False),
                          h(trp.read_bytes()) if trp.exists() else "-", h(review_raw) if d["lang"] != "ru" else "-"]))
        dst = OUT / (rel[len("documents/"):] + ".json")
        if not force and state.get(rel) == key and dst.exists():
            doc = json.loads(dst.read_text(encoding="utf-8"))["_base"]
            cached += 1
        else:
            doc = build_doc(rel, d, review)
            rebuilt += 1
        doc["_key"] = key
        docs.append(doc)
    dd = dedup(docs)
    # запись
    all_frags = []
    for doc in docs:
        d = doc["decision"]
        for f in doc["fragments"]:
            f["index"] = f["status"] == "include" and f["kind"] in INDEX_KINDS
            f["handling"] = handling(d, f)
            all_frags.append(f)
        dst = OUT / (doc["source_path"][len("documents/"):] + ".json")
        dst.parent.mkdir(parents=True, exist_ok=True)
        base = {k: v for k, v in doc.items() if k != "_key"}
        base_clean = json.loads(json.dumps(base))
        for f in base_clean["fragments"]:          # в кэш — без результатов глобального разбора дублей
            for k in ("also_in", "duplicate_of", "similar_to", "index", "handling"):
                f.pop(k, None)
            if doc["decision"]["status"] == "include" and not f["quarantine"]:
                f["status"] = "include"
        dst.write_text(json.dumps({**base, "_base": base_clean}, ensure_ascii=False, indent=1), encoding="utf-8")
        write_doc_md(doc, OUT / (doc["source_path"][len("documents/"):] + ".ru.md"))
        state[doc["source_path"]] = doc["_key"]
    state_p.write_text(json.dumps(state, ensure_ascii=False, indent=1), encoding="utf-8")
    with (OUT / "fragments.jsonl").open("w", encoding="utf-8") as fh:
        for f in all_frags:
            fh.write(json.dumps(f, ensure_ascii=False) + "\n")
    # реестр
    chk_p = OUT / "translation_checks.json"
    chk = json.loads(chk_p.read_text(encoding="utf-8"))["documents"] if chk_p.exists() else {}
    seg_err = json.loads((SEG / "_errors.json").read_text(encoding="utf-8")) if (SEG / "_errors.json").exists() else []
    err_paths = {e["source_path"]: e["error"] for e in seg_err}
    reg_rows = []
    for doc in docs:
        d = doc["decision"]
        fr = doc["fragments"]
        c = chk.get(doc["source_path"], {})
        fixed = sum(1 for f in fr if (f.get("translation_review") or {}).get("decision") == "fixed")
        reg_rows.append({
            "no": d["no"], "path": d["path"], "id": d["doc_id"], "title": d["title"], "title_ru": doc["title_ru"] or "",
            "lang": d["lang"], "format": doc["format"], "owner": d["owner"], "version": d["version"],
            "updated": d["updated"], "doc_type": d["doc_type"], "status": d["status"], "rule": d["rule"],
            "reason": d["reason"], "access": ",".join(ROLES[d["access"]]), "trust": d.get("trust", ""),
            "dup_group": d.get("dup_group", ""), "dup_role": d.get("dup_role", ""),
            "duplicate_of": d.get("duplicate_of", ""), "supersedes": d.get("supersedes", ""),
            "superseded_by": d.get("superseded_by", ""), "conflict_group": d.get("conflict_group", ""),
            "related": " ".join(str(x) for x in d.get("related", [])),
            "translation": "не требуется (RU)" if d["lang"] == "ru" else
                           ("проверен" if c and not c.get("missing") and c.get("flagged", 0) == c.get("reviewed", 0) else "НЕ проверен"),
            "translation_units": c.get("units", ""), "flags_reviewed": c.get("reviewed", ""),
            "translation_fixed": fixed if d["lang"] != "ru" else "",
            "fragments": len(fr), "fragments_indexed": sum(f["index"] for f in fr),
            "quarantined": sum(f["quarantine"] for f in fr),
            "read_error": err_paths.get(d["path"], ""), "source_sha256": doc["source_sha256"],
            "prepared": "corpus/prepared/" + d["path"][len("documents/"):] + ".json"})
    reg_p = ROOT / "registry" / "registry.csv"
    with reg_p.open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(reg_rows[0]))
        w.writeheader()
        w.writerows(reg_rows)
    with (ROOT / "inventory.csv").open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["path", "id", "title", "owner", "version", "updated", "status", "reason"])
        for r in reg_rows:
            reason = f"{r['rule']}: {r['reason']}"
            if not r["title"]:
                reason += " Заголовок в документе отсутствует."
            if not r["owner"]:
                reason += " Владелец в документе не указан."
            w.writerow([r["path"], r["id"], r["title"], r["owner"], r["version"], r["updated"], r["status"], reason])
    summary = {
        "documents": len(docs), "rebuilt": rebuilt, "cached": cached,
        "by_lang": collections.Counter(d["lang"] for d in decisions.values()),
        "by_status": collections.Counter(d["status"] for d in decisions.values()),
        "fragments": len(all_frags), "indexed": sum(f["index"] for f in all_frags),
        "quarantined": sum(f["quarantine"] for f in all_frags),
        "dedup": {"exact_groups": len(dd["exact_groups"]), "exact_copies": sum(len(g["copies"]) for g in dd["exact_groups"]),
                  "near_pairs": len(dd["near_pairs"]), "registry_pairs": dd["registry_pairs"]},
        "exact_groups": dd["exact_groups"], "near_pairs": dd["near_pairs"],
        "read_errors": seg_err, "rules": dec_all["rules"]}
    (OUT / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1, default=dict), encoding="utf-8")
    write_passport(reg_rows, dec_all["rules"], summary)
    print(f"documents {len(docs)} (rebuilt {rebuilt}, cached {cached}); fragments {len(all_frags)}, "
          f"indexed {summary['indexed']}, quarantined {summary['quarantined']}; "
          f"exact dup groups {len(dd['exact_groups'])}, near pairs {len(dd['near_pairs'])}")
    for p in dd["registry_pairs"]:
        print(f"  registry dup №{p['copy']} → №{p['main']}: {p['matched']}/{p['fragments']} фрагментов совпали после перевода")
    return 0


def write_passport(rows: list[dict], rules: dict, summary: dict):
    inc = [r for r in rows if r["status"] == "include"]
    exc = [r for r in rows if r["status"] == "exclude"]
    L = ["# Паспорт базы знаний LumenDesk", "",
         "Сгенерировано `scripts/prepare.py` из `inventory.csv` / `registry/registry.csv`. Не редактировать вручную.", "",
         "## Назначение", "",
         "База для RAG-помощника сотрудников поддержки LumenDesk (роли `support_agent`, `support_lead`). "
         "Помощник отвечает на русском по разрешённым действующим материалам: тарифы, рабочие пространства, файлы, "
         "восстановление, поддержка, API, настройки доступа. Английские и французские документы переведены на русский; "
         "каждый фрагмент ссылается на оригинал и точное место в нём.", "",
         f"## Состав: {len(rows)} файлов, включено {len(inc)}, исключено {len(exc)}", "",
         f"Фрагментов всего {summary['fragments']}, в поиск идёт {summary['indexed']}, в карантине {summary['quarantined']}.", "",
         "### Включённые файлы", "", "| № | Путь | id | Язык | Доступ | Пометки |", "|---|---|---|---|---|---|"]
    for r in inc:
        notes = []
        if r["conflict_group"]:
            notes.append(f"противоречие {r['conflict_group']}")
        if r["trust"] == "unconfirmed_origin":
            notes.append("владелец не указан")
        if r["trust"] == "personal_copy":
            notes.append("личная копия")
        if r["dup_role"] == "main":
            notes.append(f"основной экземпляр {r['dup_group']}")
        if r["quarantined"]:
            notes.append(f"карантин {r['quarantined']} фрагм.")
        L.append(f"| {r['no']} | `{r['path']}` | {r['id']} | {r['lang']} | {r['access']} | {'; '.join(notes)} |")
    L += ["", "### Исключённые файлы и причины", "", "| № | Путь | Правило | Причина |", "|---|---|---|---|"]
    for r in exc:
        L.append(f"| {r['no']} | `{r['path']}` | {r['rule']} | {r['reason']} |")
    L += ["", "## Правила отбора", ""] + [f"- **{k}.** {v}" for k, v in rules.items()]
    (ROOT / "corpus-passport.md").write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
