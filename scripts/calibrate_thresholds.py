"""Калибровка retrieval_threshold и authorization_probe_distance по размеченным вопросам.

Использует тот же индекс, модель и фильтр роли, что и `ask` (access.csv → where в Chroma). Ответов не создаёт.
Разметка: eval/relevance-labels.json. Результат: eval/calibration.json и таблица в stdout.

Запуск: python scripts/calibrate_thresholds.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8")

from rag_demo import documents as D, model as M, storage as S  # noqa: E402

POOL = 60


def main():
    labels = json.loads((ROOT / "eval" / "relevance-labels.json").read_text(encoding="utf-8"))["questions"]
    man = S.check_index()
    acc = D.load_access()
    col = S.client().get_collection(S.COLLECTION, embedding_function=None)
    rows = []
    for q in labels:
        allowed = [d for d in man["chunks_per_document"] if q["role"] in acc[d]]
        denied = [d for d in man["chunks_per_document"] if d not in allowed]
        v = M.encode_query(q["question"]).tolist()
        r = col.query(query_embeddings=[v], n_results=POOL, where={"document_id": {"$in": allowed}}, include=["distances"])
        dist = dict(zip(r["ids"][0], r["distances"][0]))
        ranked = r["ids"][0]
        rel = {c: (dist.get(c), ranked.index(c) + 1 if c in dist else None) for c in q["relevant"]}
        restricted = None
        if denied:
            pr = col.query(query_embeddings=[v], n_results=1, where={"document_id": {"$in": denied}}, include=["distances"])
            restricted = pr["distances"][0][0]
        nonrel = [dist[c] for c in ranked if c not in q["relevant"]]
        rows.append({"id": q["id"], "role": q["role"], "kind": q["kind"],
                     "best_allowed": r["distances"][0][0], "best_nonrelevant": nonrel[0] if nonrel else None,
                     "restricted_nearest": restricted,
                     "key": {c: rel[c] for c in q["key"]}, "relevant": rel,
                     "key_max": max((rel[c][0] for c in q["key"] if rel[c][0] is not None), default=None),
                     "relevant_max": max((d for d, _ in rel.values() if d is not None), default=None)})

    def state(row, thr, probe, rule):
        if row["best_allowed"] <= thr:
            return "available"
        rn = row["restricted_nearest"]
        if rn is not None and rn <= probe and (rule == "probe_only" or rn < row["best_allowed"]):
            return "forbidden"
        return "empty"

    expected = {"answerable": "available", "restricted": "forbidden", "out_of_base": "empty"}
    sweep = []
    for t in [x / 1000 for x in range(180, 236, 5)]:
        for probe in sorted({t, 0.25, 0.35}):
            for rule in ("probe_only", "probe_and_closer_than_allowed"):
                ok_state = [row["id"] for row in rows
                            if row["id"] != "x03" and state(row, t, probe, rule) == expected[row["kind"]]]
                key_ok = [row["id"] for row in rows if row["kind"] == "answerable" and row["key_max"] is not None
                          and row["key_max"] <= t]
                sweep.append({"retrieval_threshold": t, "probe": probe, "rule": rule,
                              "state_correct": len(ok_state), "of": len(rows) - 1,
                              "key_within_threshold": len(key_ok),
                              "of_answerable": sum(r["kind"] == "answerable" for r in rows),
                              "wrong": [row["id"] for row in rows if row["id"] != "x03"
                                        and state(row, t, probe, rule) != expected[row["kind"]]]})
    out = {"index_id": man["index_id"], "pool": POOL, "rows": rows, "sweep": sweep}
    (ROOT / "eval" / "calibration.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"{'id':9} {'роль':13} {'вид':11} {'лучш.разр':>9} {'лучш.нерел':>10} {'ключ.max':>8} {'рел.max':>8} {'закр.ближ':>9}")
    for r in rows:
        f = lambda x: f"{x:.4f}" if x is not None else "—"
        print(f"{r['id']:9} {r['role']:13} {r['kind']:11} {f(r['best_allowed']):>9} {f(r['best_nonrelevant']):>10} "
              f"{f(r['key_max']):>8} {f(r['relevant_max']):>8} {f(r['restricted_nearest']):>9}")
        for c, (d, rk) in r["key"].items():
            print(f"{'':9} ключевой {c}: d={f(d)} ранг={rk}")
    print("\nсвип (state_correct из 15 без x03; key_within_threshold из 13 answerable):")
    for s in sweep:
        if s["probe"] == s["retrieval_threshold"] or s["probe"] == 0.35:
            print(f" t={s['retrieval_threshold']:.3f} probe={s['probe']:.3f} {s['rule']:30} состояние {s['state_correct']}/{s['of']} "
                  f"ключ≤t {s['key_within_threshold']}/{s['of_answerable']} ошибки {s['wrong']}")


if __name__ == "__main__":
    main()
