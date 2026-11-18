"""Сегментация исходников на единицы с точным адресом в оригинале.

Выход: corpus/segments/<путь внутри documents>.json — список сегментов:
  seg     — порядковый номер в документе;
  kind    — title | heading | para | sheet_title | sheet_note | table_header | record;
  text    — исходный текст сегмента (дословно);
  sha     — sha256(text)[:12] — ключ перевода и кэша;
  section — ближайший заголовок раздела (исходный язык);
  locator — точное место: lines | paragraph | page/page_end/block | sheet/range/row | csv_row;
  cells   — для записей таблиц: [{ref|col, header, value}] — связь значения со столбцом и ячейкой;
  context — для записей таблиц: лист, название и примечание листа с диапазонами.

Кэш: сегменты файла пересобираются, только если изменился sha256 исходника
или версия сегментатора (corpus/segments/_state.json).

Запуск: python scripts/segment.py [--force]
"""
from __future__ import annotations

import hashlib
import re
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import extract as ex  # noqa: E402

ROOT = ex.ROOT
SRC = ex.SRC
OUT = ROOT / "corpus" / "segments"
VERSION = "segment-2"


def sha12(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


def seg(kind, text, locator, section=None, **extra):
    d = {"kind": kind, "text": text, "sha": sha12(text), "section": section, "locator": locator}
    d.update(extra)
    return d


def txt_heading(text: str) -> bool:
    """Подзаголовок в txt: одна короткая строка без завершающей точки, не реплика и не подпись с датой."""
    if "\n" in text or len(text) > 80:
        return False
    if re.search(r"\d{4}", text) or re.search(r":\s*[«“\"]", text):
        return False
    return text.endswith("?") or text[-1:] not in ".!:;»”\")"


def seg_text_file(p: Path, is_md: bool) -> list[dict]:
    lines = p.read_bytes().decode("utf-8-sig").replace("\r\n", "\n").split("\n")
    out, section, buf, start = [], None, [], None

    def flush(end):
        nonlocal buf, start, section
        if not buf:
            return
        text = "\n".join(buf).strip()
        if is_md and text.startswith("# "):
            kind = "title"
        elif is_md and text.startswith("#"):
            kind, section = "heading", text.lstrip("#").strip()
        elif not is_md and not out:
            kind = "title"
        elif not is_md and txt_heading(text):
            kind, section = "heading", text
        else:
            kind = "para"
        out.append(seg(kind, text, {"lines": [start, end]}, section if kind == "para" else None))
        buf, start = [], None

    for i, line in enumerate(lines, 1):
        if line.strip():
            if start is None:
                start = i
            buf.append(line)
        else:
            flush(i - 1)
    flush(len(lines))
    return out


def seg_docx(p: Path) -> list[dict]:
    out, section = [], None
    for i, st, text in ex.docx_paragraphs(p):
        if not text.strip():
            continue
        if st == "Title":
            out.append(seg("title", text, {"paragraph": i, "style": st}))
        elif st.startswith("Heading"):
            section = text
            out.append(seg("heading", text, {"paragraph": i, "style": st}))
        else:
            out.append(seg("para", text, {"paragraph": i, "style": st or "Normal"}, section))
    return out


def seg_pdf(p: Path) -> list[dict]:
    blocks, _meta = ex.pdf_blocks(p)
    out, section, per_page = [], None, {}
    for page, kind, text, end_page in blocks:
        per_page[page] = per_page.get(page, 0) + 1
        loc = {"page": page, "page_end": end_page, "block": per_page[page]}
        if kind == "title":
            out.append(seg("title", text, loc))
        elif kind == "h2":
            section = text
            out.append(seg("heading", text, loc))
        else:
            out.append(seg("para", text, loc, section))
    return out


def seg_xlsx(p: Path) -> list[dict]:
    out = []
    for sh in ex.xlsx_sheets(p):
        name, hdr, ncol, rows, hr = sh["name"], sh["header"], sh["ncol"], sh["rows"], sh["header_row"]
        last = ex.col_letter(ncol - 1)
        ctx = {"sheet": name, "title": sh["title"], "title_range": sh["title_range"],
               "notes": [{"text": t, "range": r} for t, r in sh["notes"]],
               "header_range": f"A{hr}:{last}{hr}", "header": hdr}
        if sh["title"]:
            out.append(seg("sheet_title", sh["title"], {"sheet": name, "range": sh["title_range"]}, name))
        for t, r in sh["notes"]:
            out.append(seg("sheet_note", t, {"sheet": name, "range": r}, name))
        out.append(seg("table_header", " | ".join(hdr), {"sheet": name, "row": hr, "range": f"A{hr}:{last}{hr}"},
                       name, cells=[{"ref": f"{ex.col_letter(i)}{hr}", "value": h} for i, h in enumerate(hdr)]))
        for r in sh["data_rows"]:
            cells = [{"ref": f"{ex.col_letter(i)}{r}", "header": hdr[i], "value": rows[r][i]}
                     for i in range(ncol) if rows[r].get(i, "").strip()]
            text = ex.record([(hdr[i], rows[r].get(i, "")) for i in range(ncol)])
            out.append(seg("record", text, {"sheet": name, "row": r, "range": f"A{r}:{last}{r}"},
                           name, cells=cells, context=ctx))
    return out


def seg_csv(p: Path) -> list[dict]:
    delim, hdr, data = ex.csv_rows(p)
    out = [seg("table_header", " | ".join(hdr), {"csv_row": 1}, None,
               cells=[{"col": i + 1, "value": h} for i, h in enumerate(hdr)])]
    ctx = {"header": hdr, "delimiter": delim}
    for i, row in data:
        row = row + [""] * (len(hdr) - len(row))
        cells = [{"col": j + 1, "header": hdr[j] if j < len(hdr) else f"Лишний столбец {j+1}", "value": v}
                 for j, v in enumerate(row) if v.strip()]
        text = ex.record([(c["header"], c["value"]) for c in cells])
        out.append(seg("record", text, {"csv_row": i}, None, cells=cells, context=ctx))
    return out


def segment_file(p: Path) -> list[dict]:
    ext = p.suffix.lower()
    segs = {".md": lambda: seg_text_file(p, True), ".txt": lambda: seg_text_file(p, False),
            ".docx": lambda: seg_docx(p), ".pdf": lambda: seg_pdf(p),
            ".xlsx": lambda: seg_xlsx(p), ".csv": lambda: seg_csv(p)}[ext]()
    for n, s in enumerate(segs, 1):
        s["seg"] = n
    return segs


def main() -> int:
    force = "--force" in sys.argv
    state_p = OUT / "_state.json"
    state = json.loads(state_p.read_text(encoding="utf-8")) if state_p.exists() else {}
    done = skipped = 0
    errors = []
    for p in sorted(x for x in SRC.rglob("*") if x.is_file()):
        rel = p.relative_to(ROOT).as_posix()
        digest = ex.sha256(p)
        dst = OUT / (p.relative_to(SRC).as_posix() + ".json")
        key = f"{digest}:{VERSION}"
        if not force and state.get(rel) == key and dst.exists():
            skipped += 1
            continue
        try:
            segs = segment_file(p)
        except Exception as e:  # ошибка чтения фиксируется, остальные файлы обрабатываются
            errors.append({"source_path": rel, "error": repr(e)})
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(json.dumps({"source_path": rel, "source_sha256": digest, "segmenter": VERSION,
                                   "segments": segs}, ensure_ascii=False, indent=1), encoding="utf-8")
        state[rel] = key
        done += 1
    state_p.parent.mkdir(parents=True, exist_ok=True)
    state_p.write_text(json.dumps(state, ensure_ascii=False, indent=1), encoding="utf-8")
    (OUT / "_errors.json").write_text(json.dumps(errors, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"segmented {done}, cached {skipped}, errors {len(errors)}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
