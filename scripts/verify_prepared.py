"""Итоговая проверка подготовленного корпуса.

  1. Учтены все файлы: documents/ = реестр решений = registry.csv = inventory.csv = подготовленные документы.
  2. Исходники не изменены: sha256 совпадает с зафиксированным при сегментации.
  3. Ошибок чтения нет (или они перечислены в реестре).
  4. У всех EN/FR материалов перевод полный и проверенный (check_translation: missing=0, unreviewed=0).
  5. Каждый фрагмент: путь к существующему оригиналу, точное место (страница для PDF, лист и диапазон для
     xlsx, строка для csv/md/txt, абзац для docx), статус, доступ, указание по обращению.
  6. Переведённые фрагменты хранят оригинальный текст; в поиск идёт русский текст.
  7. У включённых документов уникальные id; копии и старые версии исключены и связаны с основным.

Запуск: python scripts/verify_prepared.py   (код 1 при ошибке)
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
errors, ok = [], []


def check(cond: bool, msg: str):
    (ok if cond else errors).append(msg)


def main() -> int:
    sources = sorted(p.relative_to(ROOT).as_posix() for p in (ROOT / "documents").rglob("*") if p.is_file())
    dec = json.loads((ROOT / "registry" / "decisions.json").read_text(encoding="utf-8"))["documents"]
    reg = list(csv.DictReader((ROOT / "registry" / "registry.csv").open(encoding="utf-8-sig")))
    inv = list(csv.DictReader((ROOT / "inventory.csv").open(encoding="utf-8-sig")))
    check(len(sources) == 50, f"в documents/ {len(sources)} файлов (ожидается 50)")
    for name, rows, key in (("decisions.json", dec, "path"), ("registry.csv", reg, "path"), ("inventory.csv", inv, "path")):
        check(sorted(r[key] for r in rows) == sources, f"{name}: учтены все {len(sources)} файлов, без лишних")
    check(list(inv[0].keys()) == ["path", "id", "title", "owner", "version", "updated", "status", "reason"],
          "inventory.csv: столбцы по постановке")
    check(all(r["status"] in ("include", "exclude") and r["reason"] for r in inv), "inventory.csv: у каждой строки статус и причина")
    inc_ids = [r["id"] for r in inv if r["status"] == "include"]
    check(len(inc_ids) == len(set(inc_ids)), f"уникальные id у {len(inc_ids)} включённых документов")
    langs = {r["path"]: r["lang"] for r in reg}
    check(all(langs[s] in ("ru", "en", "fr") for s in sources), "язык оригинала указан в реестре для всех файлов")

    seg_err = json.loads((ROOT / "corpus" / "segments" / "_errors.json").read_text(encoding="utf-8"))
    check(not seg_err, f"ошибок чтения: {len(seg_err)}")

    rc = subprocess.run([sys.executable, str(ROOT / "scripts" / "check_translation.py")], capture_output=True, text=True,
                        encoding="utf-8", env={**__import__("os").environ, "PYTHONIOENCODING": "utf-8"})
    check(rc.returncode == 0, "check_translation.py: все EN/FR единицы переведены, все срабатывания разобраны")
    check(all(r["translation"] == "проверен" for r in reg if r["lang"] != "ru"),
          f"registry.csv: перевод «проверен» у всех {sum(r['lang'] != 'ru' for r in reg)} EN/FR файлов")

    n_frag = 0
    for s in sources:
        p = ROOT / "corpus" / "prepared" / (s[len("documents/"):] + ".json")
        if not p.exists():
            errors.append(f"нет подготовленного документа {s}")
            continue
        doc = json.loads(p.read_text(encoding="utf-8"))
        digest = hashlib.sha256((ROOT / s).read_bytes()).hexdigest()
        check(doc["source_sha256"] == digest, f"{s}: исходник не изменён")
        fmt = s.rsplit(".", 1)[-1].lower()
        bad = []
        for f in doc["fragments"]:
            n_frag += 1
            loc = f["locator"]
            need = {"pdf": "page", "xlsx": "sheet", "csv": "csv_row", "docx": "paragraph", "md": "lines", "txt": "lines"}[fmt]
            if f["source_path"] != s or need not in loc or not f.get("locator_text"):
                bad.append(f"{f['fragment_id']}: нет точного места")
            if fmt == "xlsx" and f["kind"] == "record" and not (loc.get("range") and f.get("cells") and f.get("context")):
                bad.append(f"{f['fragment_id']}: нет диапазона/ячеек/контекста листа")
            if fmt == "pdf" and not loc.get("page_end"):
                bad.append(f"{f['fragment_id']}: нет страницы конца")
            if not (f.get("status") and f.get("access") and f.get("handling")):
                bad.append(f"{f['fragment_id']}: нет статуса/доступа/указания по обращению")
            if f["source_lang"] != "ru":
                if not f.get("text_orig"):
                    bad.append(f"{f['fragment_id']}: нет оригинального текста")
                if f["translation"] == "translated" and not re.search(r"[А-Яа-яЁё]", f["text_ru"]):
                    bad.append(f"{f['fragment_id']}: перевод без кириллицы")
            if f.get("index") and not f["text_ru"].strip():
                bad.append(f"{f['fragment_id']}: пустой текст в поиске")
            if f.get("duplicate_of") and f.get("index"):
                bad.append(f"{f['fragment_id']}: копия попала в поиск")
        check(not bad, f"{s}: {len(doc['fragments'])} фрагментов с местом и обращением" + (f" — {bad[:3]}" if bad else ""))
    # копии и старые версии
    for r in reg:
        if r["dup_role"] == "linked_copy" or r["superseded_by"]:
            check(r["status"] == "exclude" and r["fragments_indexed"] == "0",
                  f"№{r['no']}: копия/старая версия исключена из поиска и остаётся в реестре")
    print(f"OK: {len(ok)} проверок; ошибок: {len(errors)}; фрагментов проверено: {n_frag}")
    for e in errors:
        print("ERROR", e)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
