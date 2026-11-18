"""Проверка извлечения corpus/extracted/ против исходников documents/.

Проверки:
  1. coverage   — каждое слово исходника есть в извлечении (с учётом кратности);
  2. integrity  — sha256 исходника совпадает с front matter, исходник не изменён;
  3. tables     — число записей равно числу строк данных; в каждой записи значение
                  стоит рядом с названием своего столбца; есть название и примечание листа;
  4. facts      — контрольные связки «показатель — тариф — значение — единица» лежат
                  в одной записи;
  5. structure  — заголовки docx/pdf/md сохранены и идут в исходном порядке;
  6. pdf        — нет номеров страниц в тексте, абзацы не разорваны, нет переносов;
  7. passages   — важные примечания, исключения и перекрёстные ссылки лежат целиком
                  в одном абзаце/записи;
  8. injection  — найдены тексты, адресованные ассистенту.

Запуск: python scripts/check_extraction.py   (код возврата 1 при ошибках)
"""
from __future__ import annotations

import collections
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

errors: list[str] = []
warnings: list[str] = []
passed: collections.Counter = collections.Counter()


def ok(check: str):
    passed[check] += 1


def err(check: str, msg: str):
    errors.append(f"[{check}] {msg}")


def warn(check: str, msg: str):
    warnings.append(f"[{check}] {msg}")


def words(s: str) -> collections.Counter:
    return collections.Counter(re.findall(r"\w+", s.lower()))


def out_path(src: Path) -> Path:
    return OUT / (src.relative_to(SRC).as_posix() + ".md")


def body(p: Path) -> str:
    t = p.read_text(encoding="utf-8")
    return t.split("\n---\n", 1)[1] if t.startswith("---\n") else t


def units(text: str) -> list[str]:
    """Абзацы и записи таблиц — единицы, внутри которых должен лежать связный фрагмент."""
    parts = []
    for block in re.split(r"\n\s*\n", text):
        if block.lstrip().startswith("- [строка"):
            parts.extend(block.splitlines())
        else:
            parts.append(" ".join(block.split()))
    cleaned = (re.sub(r"<!--.*?-->", "", p).strip() for p in parts)
    return [c for c in cleaned if c]


# ---------- сырой текст исходника для сравнения ----------

def raw_text(p: Path) -> str:
    ext = p.suffix.lower()
    if ext in (".md", ".txt", ".csv"):
        return p.read_bytes().decode("utf-8-sig")
    if ext == ".docx":
        d = zipfile.ZipFile(p).read("word/document.xml").decode("utf-8")
        return html.unescape(" ".join(re.findall(r"<w:t(?:\s[^>]*)?>([^<]*)</w:t>", d)))
    if ext == ".xlsx":
        z = zipfile.ZipFile(p)
        ss = z.read("xl/sharedStrings.xml").decode("utf-8") if "xl/sharedStrings.xml" in z.namelist() else ""
        vals = [html.unescape(t) for t in re.findall(r"<(?:x:)?t(?:\s[^>]*)?>([^<]*)</(?:x:)?t>", ss)]
        for n in z.namelist():
            if re.match(r"xl/worksheets/sheet\d+\.xml", n):
                sx = z.read(n).decode("utf-8")
                for attrs, v in re.findall(r"<(?:x:)?c\b([^>]*)>(?:<(?:x:)?f>[^<]*</(?:x:)?f>)?<(?:x:)?v>([^<]*)</(?:x:)?v>", sx):
                    if 't="s"' not in attrs:
                        vals.append(v)
        return " ".join(vals)
    if ext == ".pdf":
        r = PdfReader(str(p))
        return " ".join(pg.extract_text() for pg in r.pages)
    return ""


# ---------- проверки ----------

def check_coverage(src: Path, text: str):
    raw = words(raw_text(src))
    got = words(text)
    missing = {w: c - got[w] for w, c in raw.items() if got[w] < c}
    if src.suffix.lower() == ".pdf":       # номера страниц убраны намеренно
        for n in range(1, 20):
            missing.pop(str(n), None) if missing.get(str(n), 0) <= len(PdfReader(str(src)).pages) else None
    if missing:
        err("coverage", f"{src.relative_to(ROOT).as_posix()}: потеряны слова {dict(list(missing.items())[:10])}")
    else:
        ok("coverage")


def check_integrity(src: Path, full: str):
    m = re.search(r'source_sha256: "([0-9a-f]+)"', full)
    digest = hashlib.sha256(src.read_bytes()).hexdigest()
    if not m or m.group(1) != digest:
        err("integrity", f"{src.relative_to(ROOT).as_posix()}: sha256 не совпадает")
    else:
        ok("integrity")


def check_csv(src: Path, text: str):
    raw = src.read_bytes().decode("utf-8-sig")
    first = raw.splitlines()[0]
    delim = ";" if first.count(";") > first.count(",") else ","
    rows = list(csv.reader(io.StringIO(raw), delimiter=delim))
    hdr, data = rows[0], [r for r in rows[1:] if any(c.strip() for c in r)]
    recs = [l for l in text.splitlines() if l.startswith("- [строка")]
    rel = src.relative_to(ROOT).as_posix()
    if len(recs) != len(data):
        err("tables", f"{rel}: записей {len(recs)}, строк данных {len(data)}")
        return
    bad = 0
    for row, rec in zip(data, recs):
        if len(row) != len(hdr):
            err("tables", f"{rel}: строка с {len(row)} полями при {len(hdr)} столбцах: {row[:3]}")
        for h, v in zip(hdr, row):
            if v.strip() and f"{h}: {v}" not in rec:
                bad += 1
    if bad:
        err("tables", f"{rel}: {bad} значений не привязаны к своему столбцу")
    else:
        ok("tables")


def raw_sheet_cells(src: Path, sheet: str) -> dict[int, dict[int, str]]:
    """Независимое чтение ячеек листа: {строка: {столбец: значение}}; формулы — кэшированное значение."""
    z = zipfile.ZipFile(src)
    rd = lambda n: re.sub(r"<(/?)x:", lambda m: "<" + m.group(1), z.read(n).decode("utf-8-sig"))
    ss = [html.unescape("".join(re.findall(r"<t(?:\s[^>]*)?>([^<]*)</t>", si, flags=re.S)))
          for si in re.findall(r"<si>(.*?)</si>", rd("xl/sharedStrings.xml"), flags=re.S)]
    wb, rels = rd("xl/workbook.xml"), rd("xl/_rels/workbook.xml.rels")
    rid = re.search(r'<sheet\b[^>]*name="' + re.escape(html.escape(sheet, quote=True)) + r'"[^>]*r:id="([^"]+)"', wb) \
        or re.search(r'<sheet\b[^>]*name="' + re.escape(sheet) + r'"[^>]*r:id="([^"]+)"', wb)
    target = re.search(r'<Relationship\b[^>]*Target="([^"]+)"[^>]*Id="' + rid.group(1) + '"', rels) \
        or re.search(r'<Relationship\b[^>]*Id="' + rid.group(1) + r'"[^>]*Target="([^"]+)"', rels)
    t = target.group(1).lstrip("/")
    sx = rd(t if t.startswith("xl/") else "xl/" + t)
    out: dict[int, dict[int, str]] = {}
    for ref_col, ref_row, attrs, cb in re.findall(r'<c\b[^>]*?r="([A-Z]+)(\d+)"([^>]*?)(?:/>|>(.*?)</c>)', sx, flags=re.S):
        v = re.search(r"<v>(.*?)</v>", cb or "", flags=re.S)
        if not v:
            continue
        val = ss[int(v.group(1))] if 't="s"' in attrs else html.unescape(v.group(1))
        if val == "":
            continue
        col = 0
        for ch in ref_col:
            col = col * 26 + ord(ch) - 64
        out.setdefault(int(ref_row), {})[col - 1] = val
    return out


def check_xlsx(src: Path, text: str, meta: dict):
    rel = src.relative_to(ROOT).as_posix()
    for sh in meta["sheets"]:
        sec = text.split(f"## Лист: {sh['sheet']}", 1)[1].split("\n## Лист:", 1)[0]
        recs = [l for l in sec.splitlines() if l.startswith("- [строка")]
        if len(recs) != sh["records"] or not recs:
            err("tables", f"{rel} / {sh['sheet']}: записей {len(recs)}")
            continue
        if not sh["title"]:
            warn("tables", f"{rel} / {sh['sheet']}: нет названия листа")
        for n in sh["notes"]:
            if f"Примечание листа: {n}" not in sec:
                err("tables", f"{rel} / {sh['sheet']}: примечание листа потеряно")
        # сверка каждой ячейки исходника: «заголовок столбца: значение» в записи своей строки
        cells = raw_sheet_cells(src, sh["sheet"])
        hrow = cells.get(sh["header_row"], {})
        by_row = {int(re.match(r"- \[строка (\d+)\]", r).group(1)): r for r in recs}
        bad = []
        for rn, row in cells.items():
            if rn <= sh["header_row"]:
                continue
            rec = by_row.get(rn)
            for col, val in row.items():
                if rec is None or f"{hrow.get(col)}: {val}" not in rec:
                    bad.append((rn, hrow.get(col), val))
        if bad:
            err("tables", f"{rel} / {sh['sheet']}: {len(bad)} ячеек не привязаны к столбцу и строке, напр. {bad[:2]}")
        hdr = [h for h in sh["header"] if h]
        # каждая запись начинается с первого столбца и содержит только известные столбцы
        unknown = [r for r in recs if not all(k in hdr for k in re.findall(r"(?:\] |; )([^:;]+): ", r))]
        if unknown:
            err("tables", f"{rel} / {sh['sheet']}: записи с неизвестными столбцами: {unknown[:2]}")
        else:
            ok("tables")


# Контрольные связки: (файл, [фрагменты, которые должны быть в одной записи])
FACTS = [
    ("Клиентский сервис/response targets final.xlsx", ["Case: Enterprise P1", "Target: 15", "Unit: minutes", "24 hours every day"]),
    ("Клиентский сервис/response targets final.xlsx", ["Case: Team P1", "Target: 60", "Unit: minutes", "Business support hours"]),
    ("Клиентский сервис/response targets final.xlsx", ["Case: Starter", "Target: 2", "Unit: business days"]),
    ("Клиентский сервис/response targets final.xlsx", ["Business support hours", "09:00 to 18:00", "Europe/Berlin", "excluding contract holidays"]),
    ("Платформа и интеграции/Лимиты файлов.xlsx", ["Тариф: Team", "Предел файла: 100", "Единица: MiB", "Один файл"]),
    ("Платформа и интеграции/Лимиты файлов.xlsx", ["Тариф: Enterprise", "Предел файла: 250", "Единица: MiB"]),
    ("Платформа и интеграции/Лимиты файлов.xlsx", ["Тариф: Имя файла", "Предел файла: 180", "Единица: символов"]),
    ("Платформа и интеграции/Лимиты файлов.xlsx", ["макет 17.docx", "Тариф: Starter", "Размер MiB: 26", "Размер байт: 27262976", "Отклонён по размеру одного файла"]),
    ("Планирование/Тарифы новый.xlsx", ["История Team", "Возможность: 90", "Единица: дней", "Журнал активности"]),
    ("Планирование/Тарифы новый.xlsx", ["Тариф или предмет: Повышение", "После подтверждения оплаты", "в течение 15 минут"]),
    ("Франция/Assistant abonnement.xlsx", ["Offre ou sujet: Team", "Valeur: 1200", "Unité: messages", "Par workspace et par mois"]),
    ("Франция/Assistant abonnement.xlsx", ["Remise à zéro", "Valeur: 1", "jour du mois", "00:00 UTC"]),
    ("Финансы/Для руководителей/Аудит сентябрь.xlsx", ["Предмет: Хранение", "Описание: 365", "Вид: дней", "Календарные дни"]),
    ("Рабочие копии/Миграция/Приёмка - 18 сентября.xlsx", ["Проверка: Вложения", "Критерий: Не менее 99.5", "Единица: процента"]),
    ("Выгрузки/September incident register.xlsx", ["Subject: Updates", "Value: 30", "Unit: minutes", "during P1"]),
    ("Выгрузки/September incident register.xlsx", ["Incident: INC-260919", "EU-1 webhook queue", "2026-09-19 17:30 UTC", "2026-09-19 18:12 UTC"]),
    ("Клиентский сервис/хранение - сверка сентября.csv", ["Область: Журналы и выгрузки", "Активность Team", "90 дней"]),
    ("Клиентский сервис/хранение - сверка сентября.csv", ["Тариф или объект: Enterprise", "90 календарных дней", "2026-08-01 10:00 UTC", "администратор может восстановить"]),
    ("Рабочие копии/квоты для презентации.csv", ["Тариф или предмет: Карточки Team", "До 100000 активных карточек"]),
    ("Рабочие копии/квоты для презентации.csv", ["Тариф или предмет: Team", "Размер: 101", "Единица: MiB", "отклонён по размеру одного файла"]),
    ("Выгрузки/параметры-входа.csv", ["Перекрытие сертификатов", "7 календарных дней", "Применение: Enterprise", "Параметры Identity Platform от 1 сентября 2026"]),
    ("Выгрузки/webhooks-reprises.csv", ["Tentative 5", "Minutes depuis envoi initial: 60"]),
    ("Выгрузки/hosting regions export.csv", ["Region or subject: EU-2", "Paris, France"]),
    ("Выгрузки/hosting regions export.csv", ["Region or subject: Team", "EU-1 or US-1"]),
    ("Платформа и интеграции/API/ответы api новый.csv", ["429 rate_limited", "Retry-After в секундах"]),
]

# Важные примечания, исключения и связи между документами/разделами: каждая фраза
# должна целиком лежать в одной единице (абзаце или записи).
PASSAGES = [
    ("Архив 2025/экспорт-карточек.txt", "С сентября 2026 года порядок ниже заменён"),
    ("Платформа и интеграции/Выгрузка карточек.md", "В старой сохранённой инструкции из 2025 года были другие значения объёма, параллельности и срока ссылки"),
    ("Платформа и интеграции/Выгрузка карточек.md", "Строка с названиями столбцов в этот лимит не входит"),
    ("Франция/Rappels et jours fériés.pdf", "Un incident P1 sur un contrat Enterprise reste éligible au rappel le 14 juillet"),
    ("Франция/Rappels et jours fériés.pdf", "Ne pas étendre cette exception à une simple question de configuration ou à un autre tarif"),
    ("Франция/organisation/Calendrier support 2026.docx", "Le détail du délai exceptionnel se trouve dans la procédure de rappels France"),
    ("Финансы/Team service credits.pdf", "the service credit is 15 percent of the monthly subscription fee"),
    ("Финансы/Team service credits.pdf", "including an outage lasting exactly 120 consecutive minutes"),
    ("Клиентский сервис/Team service credits.docx", "the service credit is 20 percent of the monthly subscription fee"),
    ("Клиентский сервис/Сбой сервиса - рассылка.pdf", "Если обнаружены разные действующие правила компенсации, сохраните оба источника и передайте вопрос Finance и Support Operations"),
    ("Финансы/Для руководителей/Возвраты оплаты.docx", "Граница относится к самой заявке: ровно пятьсот EUR не переводят в маршрут большей суммы"),
    ("Финансы/Для руководителей/Возвраты оплаты.docx", "Только руководителям поддержки"),
    ("Финансы/Для руководителей/Аудит сентябрь.xlsx", "Журнал Enterprise не выдают специалистам первой линии"),
    ("Клиентский сервис/Для руководителей/Разбор злоупотреблений.md", "Карточку проверки открывает только руководитель поддержки"),
    ("Платформа и интеграции/SAML incident handling.docx", "Do not substitute the ordinary API-key rotation window for a SAML certificate window"),
    ("Платформа и интеграции/SAML incident handling.docx", "do not wait for three failures or for a full fifteen-minute interval in that case"),
    ("Выгрузки/параметры-входа.csv", "Критерии передачи инцидента руководителю приведены в регламенте SAML incident escalation"),
    ("Выгрузки/Downloads/SAML cutover - September.md", "This notebook deliberately does not supply a number for that window"),
    ("Планирование/Team Flex — новый вариант.txt", "приведённые значения нужны продуктовой команде для разговора и не образуют действующие условия договора"),
    ("Планирование/assistant-hypotheses.csv", "Aucun avenant client ne reprend ces valeurs"),
    ("Планирование/Клиенты/Гости — новый порядок.md", "На Starter гостевой доступ недоступен"),
    ("Клиентский сервис/Корзина и восстановление.md", "конкретных значений здесь нет"),
    ("Рабочие копии/Памятка ротации API.pdf", "Если клиент копирует большой фрагмент сетевого журнала, попросите оставить только нужные сведения и убрать Authorization"),
    ("Рабочие копии/Памятка ротации API.pdf", "По ней нельзя выводить дополнительные сроки хранения журналов, иные виды ключей или новые полномочия поддержки"),
    ("Финансы/Contrats France/Résidence Paris.pdf", "Une assistance en français ne garantit pas à elle seule un stockage à Paris"),
    ("Клиентский сервис/Privacy/Обращения о данных.pdf", "Получение полного запроса подтверждают в течение 2 рабочих дней"),
    ("Клиентский сервис/response targets final.xlsx", "Missing required context pauses target measurement"),
    ("Франция/Accessibilité septembre.pdf", "Le besoin d’un aménagement ne réduit jamais la priorité d’un incident"),
    ("Рабочие копии/Downloads/Export security final.pdf", "Splitting a completed file after downloading it does not increase the permitted size of the job that produced it"),
]


def check_units(rel: str, frags: list[str], check: str):
    p = OUT / (rel + ".md")
    if not p.exists():
        err(check, f"нет файла {rel}")
        return
    us = units(body(p))
    if any(all(f in u for f in frags) for u in us):
        ok(check)
    else:
        err(check, f"{rel}: не найдено в одной единице: {frags}")


def check_structure(src: Path, text: str, meta: dict):
    rel = src.relative_to(ROOT).as_posix()
    ext = src.suffix.lower()
    if ext == ".md":
        want = [h.rstrip("\r") for h in
                re.findall(r"^#{1,6} .+$", src.read_bytes().decode("utf-8-sig"), flags=re.M)]
    elif ext in (".docx", ".pdf"):
        want = ["## " + h for h in meta.get("headings", [])]
    else:
        return
    got = [l for l in text.splitlines() if re.match(r"^#{1,6} ", l)]
    pos, okk = 0, True
    for h in want:
        try:
            pos = got.index(h, pos) + 1
        except ValueError:
            okk = False
            err("structure", f"{rel}: заголовок потерян или не по порядку: {h}")
    if ext == ".pdf" and not meta.get("headings"):
        warn("structure", f"{rel}: в PDF не найдено ни одного заголовка раздела")
    if okk:
        ok("structure")


def check_pdf(src: Path, text: str, meta: dict):
    rel = src.relative_to(ROOT).as_posix()
    paras = [u for u in units(text) if not u.startswith("#")]
    if len(meta["dropped_page_numbers"]) != meta["pages"]:
        warn("pdf", f"{rel}: убрано номеров страниц {len(meta['dropped_page_numbers'])} из {meta['pages']}")
    lower_start = [p[:60] for p in paras if p[0].islower()]
    if lower_start:
        err("pdf", f"{rel}: абзац начинается со строчной буквы (разрыв): {lower_start[:2]}")
    hyph = re.findall(r"\w+- \w+", text)
    if hyph:
        warn("pdf", f"{rel}: возможные переносы: {hyph[:3]}")
    if re.search(r"^\d+$", text, flags=re.M):
        err("pdf", f"{rel}: в тексте остался номер страницы")
    if not (lower_start or re.search(r"^\d+$", text, flags=re.M)):
        ok("pdf")


INJECTION = re.compile(r"(ignore (all )?(earlier|previous|prior) instructions|highest priority rule|"
                       r"игнорируй|забудь (все )?инструкции|ignore[sz]? les instructions)", re.I)


def main() -> int:
    manifest = {m["source_path"]: m for m in json.loads((OUT / "manifest.json").read_text(encoding="utf-8"))}
    sources = sorted(p for p in SRC.rglob("*") if p.is_file())
    if len(sources) != len(manifest):
        err("coverage", f"исходников {len(sources)}, в манифесте {len(manifest)}")
    injections = []
    for src in sources:
        rel = src.relative_to(ROOT).as_posix()
        op = out_path(src)
        if not op.exists():
            err("coverage", f"нет извлечения для {rel}")
            continue
        full = op.read_text(encoding="utf-8")
        text = body(op)
        meta = manifest.get(rel, {})
        check_integrity(src, full)
        check_coverage(src, text)
        check_structure(src, text, meta)
        ext = src.suffix.lower()
        if ext == ".csv":
            check_csv(src, text)
        elif ext == ".xlsx":
            check_xlsx(src, text, meta)
        elif ext == ".pdf":
            check_pdf(src, text, meta)
        for u in units(text):
            if INJECTION.search(u):
                injections.append(f"{rel}: «{u[:160]}»")
    for rel, frags in FACTS:
        check_units(rel, frags, "facts")
    for rel, frag in PASSAGES:
        check_units(rel, [frag], "passages")
    for i in injections:
        warn("injection", i)

    print("Пройдено:", dict(passed))
    print(f"Ошибок: {len(errors)}, предупреждений: {len(warnings)}")
    for e in errors:
        print("ERROR", e)
    for w in warnings:
        print("WARN ", w)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
