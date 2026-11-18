"""Сверка переводов с оригиналами по каждой единице перевода.

Проверки (для каждой пары «оригинал EN/FR — перевод RU»):
  numbers     — мультимножество чисел совпадает (цифры + числительные словами: forty-eight, sept, сорок восемь…);
  exact       — точные обозначения оригинала (UTC, SAML, P1, EU-2, dead_letter, Retry-After, Europe/Paris,
                названия тарифов и команд) присутствуют в переводе без изменений;
  negation    — отрицание в оригинале ↔ отрицание в переводе (и наоборот);
  conditions  — маркеры ограничений и условий: только / не менее / не более / в течение / до / после /
                обязательность / немедленно / условие «если/когда»;
  roles       — роли и полномочия (руководитель поддержки, администратор, владелец, billing owner);
  length      — соотношение длины перевода и оригинала (защита от пересказа и дописывания).

Сработавшие проверки требуют ручного разбора: решение записывается в translations/_review.json
({sha: {"checks": [...], "decision": "accepted"|"fixed", "note": "..."}}). Перевод считается проверенным,
если ни одна проверка не сработала либо все срабатывания разобраны.

Результат: corpus/prepared/translation_checks.json. Запуск: python scripts/check_translation.py
"""
from __future__ import annotations

import collections
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import translate as tr  # noqa: E402

ROOT = tr.ROOT
OUT = ROOT / "corpus" / "prepared" / "translation_checks.json"
REVIEW = tr.TR / "_review.json"

NUM_WORDS = {
    # en
    "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "ten": 10, "twelve": 12,
    "fifteen": 15, "fifteen-minute": 15, "twenty": 20, "thirty": 30, "forty-eight": 48, "ninety": 90,
    "half": 0.5, "both": 2,
    # fr
    "deux": 2, "trois": 3, "cinq": 5, "sept": 7, "dix": 10, "douze": 12, "quatorze": 14, "quinze": 15,
    "vingt": 20, "trente": 30, "quarante-cinq": 45, "sixième": 6, "six": 6,
    # ru
    "два": 2, "две": 2, "двух": 2, "двум": 2, "двумя": 2, "три": 3, "трёх": 3, "тремя": 3, "трём": 3,
    "пять": 5, "пяти": 5, "шесть": 6, "шести": 6, "шестью": 6, "шестой": 6, "семь": 7, "семи": 7,
    "десять": 10, "десяти": 10, "двенадцать": 12, "пятнадцать": 15, "пятнадцати": 15,
    "пятнадцатиминутного": 15, "четырнадцать": 14, "четырнадцати": 14, "двадцать": 20, "двадцати": 20,
    "тридцать": 30, "тридцати": 30, "тридцатиминутн": 30, "половины": 0.5, "половину": 0.5,
    "оба": 2, "обе": 2, "обоих": 2, "обеих": 2, "обеим": 2, "двое": 2,
}
PHRASES = {"les deux": 2, "cent quatre-vingts": 180, "сто восемьдесят": 180, "сорок восемь": 48, "сорока восьми": 48}

EXACT_RE = re.compile(
    r"\b(?:[A-Z]{2,}[A-Z0-9]*(?:-[A-Z0-9]+)*|[A-Za-z]+-\d+[A-Za-z0-9-]*|[a-z]+_[a-z_]+|[a-z]+\.[a-z]+"
    r"|Retry-After|Europe/[A-Z][a-z]+|America/[A-Z][a-z]+|Starter|Team|Enterprise|LumenDesk"
    r"|Support Operations|Identity Platform|Data Portability|Customer Success(?: and Support)?|Finance"
    r"|Billing Support|Billing Operations|Integrations|Infrastructure|Messaging Platform|Client Platform"
    r"|Knowledge Operations|Support France|Customer Enablement France|Assistant Product|Workspace Platform"
    r"|Chrome|Edge|Firefox|Safari|macOS|WebSocket|GitHub|Slack|Jira|OAuth|\d+xx)\b")

NEG = {
    "en": re.compile(r"\b(?:not|no|never|none|nothing|without|nor|cannot|neither|missing|excluding|outside|"
                     r"absent|unless|optional|instead of|rather than)\b|n't\b|\bun(?:paid|read|available|"
                     r"proven|related|reviewed|answered|resolved|ambiguous|certain|clear)\b|\bnon-|\binvalid\b", re.I),
    "fr": re.compile(r"\b(?:ne|pas|jamais|aucun|aucune|sans|ni|rien|non|hors|sauf|facultatif|plutôt que|au lieu)\b"
                     r"|\bn['’]|\bin(?:disponible|utilisable)", re.I),
    "ru": re.compile(r"(?<![\w])(?:не|нет|ни|никогда|никакой|никакого|ничего|без|нельзя|кроме|вместо)(?![\w])|(?<![\w])не(?:до|воз|опл|при|"
                     r"про|обя|пол|точ|ясн|под|вер|дос|сог|пон|зав|отв|сво|час|кон|изм|акт|реа|обх|сущ|нуж)\w*|"
                     r"(?<![\w])недейств\w*|(?<![\w])отсутств\w*|(?<![\w])а не(?![\w])", re.I),
}
# устойчивые обороты-ограничения: «не менее/не более/не позднее» не считаются отрицанием
RU_BOUND = re.compile(r"(?<![\w])не (?:менее|более|позднее|реже|больше|меньше)(?![\w])", re.I)
ORIG_BOUND = re.compile(r"\b(?:no more than|no later than|not later than|not less than)\b", re.I)

COND = {
    "only": (r"\bonly\b|\bexclusively\b|\bseulement\b|\buniquement\b|\bexclusivement\b|\bne\b[^.]{0,40}\bque\b",
             r"только|исключительно|лишь|единственн|всего"),
    "at_least": (r"\bat least\b|\bau moins\b|\bminimum\b", r"не менее|не реже|как минимум|не меньше|по меньшей мере|минимум"),
    "at_most": (r"\bat most\b|\bup to\b|\bmaximum\b|\bmaximal\b|\bau plus\b|\bjusqu|\bcannot exceed\b|\bno more than\b",
                r"не более|не больше|не позднее|максимальн|максимум|до \d|не может превышать|не превыша|— до"),
    "within": (r"\bwithin\b|\bdans les\b", r"в течение|в пределах|не позднее|за \d|срок"),
    "must": (r"\bmust\b|\brequire[sd]?\b|\bdoit\b|\bdoivent\b|\bexige\b|\bnécessite\b|\brequis\b|\bobligatoire\b",
             r"долж|нуж|необходим|требу|требова|обязател|следует|нельзя|только"),
    "immediately": (r"\bimmediately\b|\bimmédiatement\b", r"немедленно|сразу"),
    "before": (r"\bbefore\b|\bavant\b", r"\bдо\b|прежде|перед|раньше|заранее|предварительн|не позднее чем за|за \d"),
    "after": (r"\bafter\b|\baprès\b", r"после|по окончании|через|по истечении|по завершении"),
}

ROLES = {
    "support_lead": (r"support lead|responsable de permanence", r"руководител|ответственн"),
    "administrator": (r"\badministrat", r"администрат"),
    "owner": (r"\bowner\b|\bpropriétaire\b", r"владел|ответствен|billing owner"),
}


def numbers(text: str) -> collections.Counter:
    t = text.lower()
    c = collections.Counter()
    for ph, v in PHRASES.items():
        n = t.count(ph)
        if n:
            c[v] += n
            t = t.replace(ph, " ")
    for m in re.findall(r"\d+(?:[.,]\d+)?", t):
        v = float(m.replace(",", "."))
        c[int(v) if v.is_integer() else v] += 1
    for w in re.findall(r"[a-zà-ÿа-яё-]+", t):
        hit = False
        for key, v in NUM_WORDS.items():
            if w == key or (key.endswith("минутн") and w.startswith(key)):
                c[v] += 1
                hit = True
        head = w.split("-")[0]
        if not hit and "-" in w and head in NUM_WORDS:          # three-failure, fifteen-minute
            c[NUM_WORDS[head]] += 1
    return c


def check_pair(orig: str, ru: str, lang: str) -> dict:
    issues = {}
    no, nr = numbers(orig), numbers(ru)
    if no != nr:
        issues["numbers"] = {"orig": dict(no), "ru": dict(nr)}
    ex = sorted({m.group(0) for m in EXACT_RE.finditer(orig)})
    miss = [e for e in ex if e not in ru]
    if miss:
        issues["exact"] = miss
    orig_plain = EXACT_RE.sub(" ", orig)            # Retry-After и т. п. не должны давать «after»
    a = len(NEG[lang].findall(ORIG_BOUND.sub(" ", orig_plain)))
    b = len(NEG["ru"].findall(RU_BOUND.sub(" ", ru)))
    if (a > 0) != (b > 0):
        issues["negation"] = {"orig": a, "ru": b}
    for name, (po, pr) in COND.items():
        if re.search(po, orig_plain, re.I) and not re.search(pr, ru, re.I):
            issues.setdefault("conditions", []).append(name)
    for name, (po, pr) in ROLES.items():
        if re.search(po, orig, re.I) and not re.search(pr, ru, re.I):
            issues.setdefault("roles", []).append(name)
    if len(orig) >= 60:
        ratio = len(ru) / len(orig)
        if not 0.75 <= ratio <= 1.8:
            issues["length"] = round(ratio, 2)
    return issues


def main() -> int:
    dec = tr.load_decisions()
    review = json.loads(REVIEW.read_text(encoding="utf-8")) if REVIEW.exists() else {}
    report, totals = {}, collections.Counter()
    unreviewed = []
    for rel, d in dec.items():
        if d["lang"] == "ru":
            continue
        tm = tr.load_translations(rel)
        units = tr.units_for(rel)
        doc = {"lang": d["lang"], "units": len(units), "missing": 0, "flagged": 0, "reviewed": 0, "items": []}
        for h, text, where in units:
            ru = tm.get(h)
            if not ru:
                doc["missing"] += 1
                continue
            if ru == "=":
                totals["kept_as_is"] += 1
                continue
            iss = check_pair(text, ru, d["lang"])
            totals["checked"] += 1
            for k in iss:
                totals[f"flag_{k}"] += 1
            if iss:
                doc["flagged"] += 1
                rv = review.get(h)
                ok = bool(rv) and set(iss) <= set(rv.get("checks", []))
                doc["reviewed"] += ok
                if not ok:
                    unreviewed.append((rel, h))
                doc["items"].append({"sha": h, "where": where, "issues": iss, "orig": text, "ru": ru,
                                     "review": rv})
        report[rel] = doc
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"totals": totals, "documents": report}, ensure_ascii=False, indent=1),
                   encoding="utf-8")
    print(dict(totals))
    print(f"documents: {len(report)}, missing: {sum(d['missing'] for d in report.values())}, "
          f"flagged: {sum(d['flagged'] for d in report.values())}, unreviewed: {len(unreviewed)}")
    for rel, h in unreviewed[:200]:
        print("UNREVIEWED", h, rel)
    return 1 if unreviewed or any(d["missing"] for d in report.values()) else 0


if __name__ == "__main__":
    sys.exit(main())
