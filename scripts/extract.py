"""Извлечение текста из documents/ в corpus/extracted/ с сохранением структуры.

Исходники только читаются. Для каждого файла создаётся <относительный путь>.md:
- md/txt: текст без изменений;
- docx: Title -> "#", Heading1 -> "##", абзацы дословно;
- pdf: заголовки по шрифту (крупный полужирный -> "#", полужирный 12pt -> "##"),
  абзацы собраны из строк, номера страниц убраны, абзац через границу страницы
  склеивается, маркер страницы <!-- page N --> ставится перед абзацем;
- xlsx/csv: каждая строка данных — отдельная запись «столбец: значение»
  с номером строки; название и примечание листа выводятся перед записями.

Запуск: python scripts/extract.py
"""
from __future__ import annotations

import csv
import hashlib
import html
import io
import json
import re
import sys
import zipfile
from pathlib import Path

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "documents"
OUT = ROOT / "corpus" / "extracted"
VERSION = "extract-1"


# ---------- общие ----------

def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def front_matter(rel: str, fmt: str, digest: str, extra: dict) -> str:
    meta = {"source_path": rel, "format": fmt, "source_sha256": digest,
            "extractor": VERSION, **extra}
    lines = ["---"] + [f"{k}: {json.dumps(v, ensure_ascii=False)}" for k, v in meta.items()] + ["---", ""]
    return "\n".join(lines)


def record(fields: list[tuple[str, str]]) -> str:
    """Строка таблицы как запись: пустые значения опускаются, порядок столбцов сохраняется."""
    return "; ".join(f"{k}: {v}" for k, v in fields if v.strip())


# ---------- docx ----------

def docx_paragraphs(p: Path) -> list[tuple[int, str, str]]:
    """(номер абзаца w:p с 1, стиль, текст) — пустые абзацы тоже нумеруются."""
    d = zipfile.ZipFile(p).read("word/document.xml").decode("utf-8")
    res = []
    for i, para in enumerate(re.findall(r"<w:p[ >].*?</w:p>", d, flags=re.S), 1):
        style = re.search(r'<w:pStyle w:val="([^"]+)"', para)
        text = html.unescape("".join(re.findall(r"<w:t(?:\s[^>]*)?>([^<]*)</w:t>", para)))
        res.append((i, style.group(1) if style else "", text))
    return res


def extract_docx(p: Path) -> tuple[str, dict]:
    z = zipfile.ZipFile(p)
    out, headings = [], []
    for _i, st, text in docx_paragraphs(p):
        if not text.strip():
            continue
        if st == "Title":
            out.append(f"# {text}")
        elif st.startswith("Heading"):
            level = int(re.sub(r"\D", "", st) or 1)
            out.append("#" * (level + 1) + " " + text)
            headings.append(text)
        else:
            out.append(text)
    extra_parts = []
    for n in z.namelist():
        if re.match(r"word/(header|footer|footnotes|endnotes|comments)", n):
            t = html.unescape(re.sub(r"<[^>]+>", " ", z.read(n).decode("utf-8"))).strip()
            if t:
                extra_parts.append(f"<!-- {n} -->\n{t}")
    body = "\n\n".join(out + extra_parts) + "\n"
    return body, {"headings": headings}


# ---------- pdf ----------

def pdf_blocks(p: Path) -> tuple[list[tuple[int, str, str, int]], dict]:
    """Блоки PDF: (страница начала, вид title|h2|p, текст, страница конца) и метаданные."""
    r = PdfReader(str(p))
    lines = []  # (page, y, size, bold, text) — одна запись на строку
    for pno, page in enumerate(r.pages, 1):
        def visit(text, cm, tm, fd, fs, _p=pno):
            if not text.strip():
                return
            y = cm[5] + tm[5] * cm[3]
            size = round(fs * tm[0], 1)
            font = (fd or {}).get("/BaseFont", "") if fd else ""
            if lines and lines[-1][0] == _p and abs(lines[-1][1] - y) < 0.5:
                pp, py, ps, pb, pt = lines[-1]          # продолжение той же строки
                lines[-1] = (pp, py, ps, pb, pt + text)
            else:
                lines.append((_p, y, size, "Bold" in str(font), text))
        page.extract_text(visitor_text=visit)

    body_size = max({l[2] for l in lines}, key=lambda s: sum(len(l[4]) for l in lines if l[2] == s))
    body_ys = [l[1] for l in lines if l[2] == body_size]
    gaps = sorted(round(a - b, 1) for a, b in zip(body_ys, body_ys[1:]) if 0 < a - b < 40)
    pitch = gaps[len(gaps) // 4] if gaps else body_size * 1.4      # межстрочный шаг внутри абзаца
    blocks, cur, cur_page, cur_kind, prev = [], [], None, None, None
    last_line_page = None
    dropped = []

    def flush():
        nonlocal cur, cur_page, cur_kind
        if cur:
            blocks.append((cur_page, cur_kind, " ".join(s.strip() for s in cur), last_line_page))
        cur, cur_page, cur_kind = [], None, None

    for pno, y, size, bold, text in lines:
        if size < body_size - 1 and text.strip().isdigit():   # колонтитул с номером страницы
            dropped.append(text.strip())
            continue
        kind = "title" if bold and size > body_size + 4 else "h2" if bold and size > body_size else "p"
        new_par = True
        if kind == "p" and cur_kind == "p" and prev is not None:
            ppage, py = prev
            if ppage == pno:
                new_par = (py - y) > pitch * 1.3
            else:  # граница страницы: продолжаем, если предыдущая строка не закончила предложение
                new_par = cur[-1].rstrip()[-1:] in ".!?:»\")"
        if new_par:
            flush()
            cur_page, cur_kind = pno, kind
        cur.append(text)
        prev = (pno, y)
        last_line_page = pno
    flush()
    meta = {"pages": len(r.pages), "dropped_page_numbers": dropped,
            "pdf_title": (r.metadata or {}).get("/Title", "")}
    return blocks, meta


def extract_pdf(p: Path) -> tuple[str, dict]:
    blocks, meta = pdf_blocks(p)
    headings = []
    out, last_page = [], None
    for pno, kind, text, end_page in blocks:
        if pno != last_page:
            out.append(f"<!-- page {pno} -->")
            last_page = pno
        if end_page != pno:
            text += f" <!-- абзац продолжается на page {end_page} -->"
            last_page = end_page
        if kind == "title":
            out.append(f"# {text}")
        elif kind == "h2":
            out.append(f"## {text}")
            headings.append(text)
        else:
            out.append(text)
    meta = {**meta, "headings": headings}
    return "\n\n".join(out) + "\n", meta


# ---------- xlsx ----------

def _xml(z, n):
    return re.sub(r"<(/?)x:", lambda m: "<" + m.group(1), z.read(n).decode("utf-8-sig"))


def _t(s):
    return html.unescape("".join(re.findall(r"<t(?:\s[^>]*)?>([^<]*)</t>", s, flags=re.S)))


def _col(ref):
    n = 0
    for ch in re.match(r"[A-Z]+", ref).group(0):
        n = n * 26 + ord(ch) - 64
    return n - 1


def xlsx_sheets(p: Path) -> list[dict]:
    """Листы: название и примечания с диапазонами объединений, шапка, строки данных."""
    z = zipfile.ZipFile(p)
    names = z.namelist()
    ss = [_t(si) for si in re.findall(r"<si>(.*?)</si>", _xml(z, "xl/sharedStrings.xml"), flags=re.S)] \
        if "xl/sharedStrings.xml" in names else []
    wb, rels = _xml(z, "xl/workbook.xml"), _xml(z, "xl/_rels/workbook.xml.rels")
    rmap = {re.search(r'Id="([^"]+)"', r).group(1): re.search(r'Target="([^"]+)"', r).group(1)
            for r in re.findall(r"<Relationship\b[^>]*>", rels)}
    sheets = []
    for sh in re.findall(r"<sheet\b[^>]*>", wb):
        name = html.unescape(re.search(r'name="([^"]+)"', sh).group(1))
        state = re.search(r'state="([^"]+)"', sh)
        target = rmap[re.search(r'r:id="([^"]+)"', sh).group(1)].lstrip("/")
        target = target if target.startswith("xl/") else "xl/" + target
        sx = _xml(z, target)
        merges = re.findall(r'mergeCell ref="([A-Z]+)(\d+):([A-Z]+)(\d+)"', sx)
        rows: dict[int, dict[int, str]] = {}
        formulas = 0
        for rn, body in re.findall(r'<row\b[^>]*\br="(\d+)"[^>]*>(.*?)</row>', sx, flags=re.S):
            cells = {}
            for attrs, cb in re.findall(r"<c\b([^>]*?)(?:/>|>(.*?)</c>)", body, flags=re.S):
                ref = re.search(r'\br="([A-Z]+\d+)"', attrs).group(1)
                typ = re.search(r'\bt="(\w+)"', attrs)
                v = re.search(r"<v>(.*?)</v>", cb or "", flags=re.S)
                f = re.search(r"<f>(.*?)</f>", cb or "", flags=re.S)
                if typ and typ.group(1) == "s" and v:
                    val = ss[int(v.group(1))]
                elif typ and typ.group(1) == "inlineStr":
                    val = _t(cb)
                elif v:
                    val = html.unescape(v.group(1))
                else:
                    val = ""
                if f:
                    formulas += 1
                    val = f"{val} (формула ={html.unescape(f.group(1))})" if val else f"(формула ={html.unescape(f.group(1))}, значение не сохранено)"
                if val != "":
                    cells[_col(ref)] = val
            if cells:
                rows[int(rn)] = cells
        # служебные строки: левые верхние ячейки объединений над шапкой
        merged_tops = sorted(int(r1) for c1, r1, c2, r2 in merges)
        title = rows.get(merged_tops[0], {}).get(0, "") if merged_tops else ""
        notes = [rows[r][0] for r in merged_tops[1:] if r in rows and 0 in rows[r]]
        merged_rows = set()
        for c1, r1, c2, r2 in merges:
            merged_rows.update(range(int(r1), int(r2) + 1))
        data_rows = [r for r in sorted(rows) if r not in merged_rows]
        header_row = data_rows[0]
        header = rows[header_row]
        ncol = max(max(c) for c in rows.values()) + 1
        hdr = [header.get(i, f"Столбец {i+1}") for i in range(ncol)]
        ranges = {int(r1): f"{c1}{r1}:{c2}{r2}" for c1, r1, c2, r2 in merges}
        sheets.append({"name": name, "state": state.group(1) if state else None,
                       "title": title, "title_range": ranges.get(merged_tops[0]) if merged_tops else None,
                       "notes": [(rows[r][0], ranges[r]) for r in merged_tops[1:] if r in rows and 0 in rows[r]],
                       "header_row": header_row, "header": hdr, "ncol": ncol,
                       "rows": rows, "data_rows": data_rows[1:], "formulas": formulas})
    return sheets


def col_letter(i: int) -> str:
    s, i = "", i + 1
    while i:
        i, r = divmod(i - 1, 26)
        s = chr(65 + r) + s
    return s


def extract_xlsx(p: Path) -> tuple[str, dict]:
    out, sheets_meta = [], []
    for sh in xlsx_sheets(p):
        name, hdr, ncol, rows = sh["name"], sh["header"], sh["ncol"], sh["rows"]
        notes = [n for n, _ in sh["notes"]]
        out.append(f"## Лист: {name}" + (f" (state={sh['state']})" if sh["state"] else ""))
        if sh["title"]:
            out.append(f"Название листа: {sh['title']}")
        for n_ in notes:
            out.append(f"Примечание листа: {n_}")
        out.append("Столбцы: " + " | ".join(h for h in hdr if h))
        recs = []
        for r in sh["data_rows"]:
            fields = [(hdr[i], rows[r].get(i, "")) for i in range(ncol)]
            recs.append(f"- [строка {r}] " + record(fields))
        out.append("\n".join(recs))
        sheets_meta.append({"sheet": name, "title": sh["title"], "notes": notes, "header_row": sh["header_row"],
                            "header": hdr, "records": len(recs), "formulas": sh["formulas"],
                            "hidden": bool(sh["state"])})
    return "\n\n".join(out) + "\n", {"sheets": sheets_meta}


# ---------- csv ----------

def csv_rows(p: Path) -> tuple[str, list[str], list[tuple[int, list[str]]]]:
    """Разделитель, шапка и непустые строки данных с номером строки файла (шапка — строка 1)."""
    text = p.read_bytes().decode("utf-8-sig")
    first = text.splitlines()[0]
    delim = ";" if first.count(";") > first.count(",") else ","
    rows = list(csv.reader(io.StringIO(text), delimiter=delim))
    data = [(i, r) for i, r in enumerate(rows[1:], start=2) if any(c.strip() for c in r)]
    return delim, rows[0], data


def extract_csv(p: Path) -> tuple[str, dict]:
    delim, hdr, data = csv_rows(p)
    recs = []
    for i, row in data:
        row = row + [""] * (len(hdr) - len(row))
        extra = row[len(hdr):]
        fields = list(zip(hdr, row[:len(hdr)])) + [(f"Лишний столбец {j+1}", v) for j, v in enumerate(extra)]
        recs.append(f"- [строка {i}] " + record(fields))
    body = "Столбцы: " + " | ".join(hdr) + "\n\n" + "\n".join(recs) + "\n"
    return body, {"delimiter": delim, "header": hdr, "records": len(recs)}


# ---------- main ----------

def main() -> int:
    files = sorted(p for p in SRC.rglob("*") if p.is_file())
    manifest = []
    for p in files:
        rel = p.relative_to(ROOT).as_posix()
        ext = p.suffix.lower().lstrip(".")
        if ext in ("md", "txt"):
            raw = p.read_bytes().decode("utf-8-sig")
            body, meta = raw.replace("\r\n", "\n"), {"crlf_normalized": "\r\n" in raw}
        elif ext == "docx":
            body, meta = extract_docx(p)
        elif ext == "pdf":
            body, meta = extract_pdf(p)
        elif ext == "xlsx":
            body, meta = extract_xlsx(p)
        elif ext == "csv":
            body, meta = extract_csv(p)
        else:
            print("SKIP", rel, file=sys.stderr)
            continue
        digest = sha256(p)
        dst = OUT / (p.relative_to(SRC).as_posix() + ".md")
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(front_matter(rel, ext, digest, {}) + body, encoding="utf-8", newline="\n")
        manifest.append({"source_path": rel, "output": dst.relative_to(ROOT).as_posix(),
                         "format": ext, "source_sha256": digest, **meta})
    (OUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"extracted {len(manifest)} files -> {OUT.relative_to(ROOT).as_posix()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
