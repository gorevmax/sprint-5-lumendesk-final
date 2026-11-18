"""Единицы перевода и хранилище переводов.

Единица перевода:
  - проза (md, txt, docx, pdf): текст сегмента title/heading/para;
  - таблицы (xlsx, csv): уникальная строка — название листа, название и примечание листа,
    заголовок столбца, значение ячейки.
Ключ единицы — sha256(текст)[:12]. Изменение исходного абзаца или ячейки даёт новый ключ,
поэтому переводить заново нужно только изменённые единицы; прежние переводы не трогаются.

Хранилище: translations/<путь внутри documents>.ru.txt
    @@ <sha>
    <перевод, одна или несколько строк>
Значение «=» означает «оставить как в оригинале» (точное обозначение).

Строки, целиком состоящие из точных обозначений (тарифы, коды, ID, даты, числа, названия
продуктов), не переводятся и в хранилище не попадают — см. is_exact().

Команды:
  python scripts/translate.py todo [подстрока пути]   — непереведённые единицы EN/FR
  python scripts/translate.py status                  — сводка по документам
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SEG = ROOT / "corpus" / "segments"
TR = ROOT / "translations"
DECISIONS = ROOT / "registry" / "decisions.json"

PROSE_KINDS = {"title", "heading", "para"}

EXACT_WORDS = {
    "starter", "team", "enterprise", "utc", "slack", "microsoft", "teams", "github", "google", "drive",
    "jira", "cloud", "saml", "sso", "mfa", "api", "http", "https", "mib", "id", "url", "csv", "zip",
    "exe", "scr", "pdf", "docx", "xlsx", "oauth", "issuer", "lumendesk", "eur", "esr", "chrome", "edge",
    "firefox", "safari", "macos", "workspace",
}


def sha12(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


def is_exact(s: str) -> bool:
    """Строка состоит только из точных обозначений и переводу не подлежит."""
    toks = s.replace(",", " ").split()
    if not toks:
        return True
    for t in toks:
        t2 = t.strip("();:")
        if not re.search(r"[A-Za-zÀ-ÿА-Яа-яЁё]", t2):           # числа, даты, время, знаки
            continue
        if re.fullmatch(r"[A-Za-z]+[-_.][A-Za-z0-9_.\-]*\d[A-Za-z0-9_.\-]*", t2):  # INC-260903, req-3100, EU-1
            continue
        if re.fullmatch(r"[a-z]+[._][a-z_.]+", t2):              # cartes.cree, dead_letter
            continue
        if re.fullmatch(r"P\d|\d+xx|[A-Z]{2,}(-\d+)?", t2):      # P1, 2xx, CA-1, HTTP
            continue
        if re.fullmatch(r"[A-Z][a-z]+/[A-Z][a-z_]+", t2):        # Europe/Paris
            continue
        if t2.lower() in EXACT_WORDS:
            continue
        return False
    return True


def load_decisions() -> dict[str, dict]:
    d = json.loads(DECISIONS.read_text(encoding="utf-8"))
    return {x["path"]: x for x in d["documents"]}


def seg_file(rel: str) -> Path:
    return SEG / (rel[len("documents/"):] + ".json")


def tr_file(rel: str) -> Path:
    return TR / (rel[len("documents/"):] + ".ru.txt")


def units_for(rel: str) -> list[tuple[str, str, str]]:
    """[(sha, текст, где встречается)] — уникальные единицы перевода документа в порядке появления."""
    segs = json.loads(seg_file(rel).read_text(encoding="utf-8"))["segments"]
    seen, out = set(), []

    def add(text, where):
        if not text or not text.strip() or is_exact(text):
            return
        h = sha12(text)
        if h not in seen:
            seen.add(h)
            out.append((h, text, where))

    for s in segs:
        loc = s["locator"]
        if s["kind"] in PROSE_KINDS:
            add(s["text"], json.dumps(loc, ensure_ascii=False))
            continue
        sheet = loc.get("sheet")
        if sheet:
            add(sheet, f"лист {sheet}: название листа")
        if s["kind"] in ("sheet_title", "sheet_note"):
            add(s["text"], f"{sheet}!{loc['range']}")
        else:
            for c in s.get("cells", []):
                add(c["value"], f"{sheet + '!' if sheet else 'строка ' + str(loc.get('csv_row')) + ', столбец '}"
                                f"{c.get('ref') or c.get('col')}")
    return out


def load_translations(rel: str) -> dict[str, str]:
    p = tr_file(rel)
    if not p.exists():
        return {}
    res, cur, buf = {}, None, []
    for line in p.read_text(encoding="utf-8").replace("\r\n", "\n").split("\n"):
        m = re.match(r"^@@ ([0-9a-f]{12})\s*$", line)
        if m:
            if cur:
                res[cur] = "\n".join(buf).strip()
            cur, buf = m.group(1), []
        elif cur is not None:
            buf.append(line)
    if cur:
        res[cur] = "\n".join(buf).strip()
    return res


def translated(rel: str, text: str, tm: dict[str, str]) -> str | None:
    """Перевод строки: точные обозначения — как есть; '=' — как в оригинале; None — нет перевода."""
    if is_exact(text):
        return text
    v = tm.get(sha12(text))
    if v is None or v == "":
        return None
    return text if v == "=" else v


def main() -> int:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    flt = sys.argv[2] if len(sys.argv) > 2 else ""
    dec = load_decisions()
    for rel, d in dec.items():
        if d["lang"] == "ru" or flt not in rel:
            continue
        units = units_for(rel)
        tm = load_translations(rel)
        missing = [u for u in units if not tm.get(u[0])]
        orphans = set(tm) - {u[0] for u in units}
        if cmd == "status":
            print(f"{d['no']:02d} {d['lang']} units={len(units):4d} missing={len(missing):4d} "
                  f"orphans={len(orphans):3d} {rel}")
        elif cmd == "todo" and missing:
            print(f"### {d['no']:02d} {rel}")
            for h, text, where in missing:
                print(f"@@ {h}   <!-- {where} -->")
                print(text)
                print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
