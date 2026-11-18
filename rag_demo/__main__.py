"""CLI RAG-помощника LumenDesk: python -m rag_demo <команда>."""
from __future__ import annotations

import argparse
import json
import sys

# Windows-консоль: JSON выводится в UTF-8 независимо от кодовой страницы
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except AttributeError:
        pass


def _print(obj):
    print(json.dumps(obj, ensure_ascii=False, indent=1))


def _top_k(v: str) -> int:
    try:
        n = int(v)
    except ValueError:
        raise argparse.ArgumentTypeError(f"top_k должен быть целым, получено {v!r}")
    if n < 1 or str(n) != v.strip():
        raise argparse.ArgumentTypeError(f"top_k должен быть положительным целым, получено {v!r}")
    return n


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="python -m rag_demo", description="RAG-помощник поддержки LumenDesk")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("prepare-model", help="скачать файлы E5, если их нет, и проверить загрузчиком")
    sub.add_parser("access-sync", help="записать access.csv из реестра")
    sub.add_parser("validate-docs", help="проверить inventory, подготовленный корпус и доступ")
    sub.add_parser("chunks", help="нарезать корпус и сохранить evidence/chunks.json")
    sub.add_parser("index", help="построить индекс Chroma по include-документам")
    sub.add_parser("status", help="проверить актуальность сохранённого индекса")
    for name in ("retrieve", "ask"):
        p = sub.add_parser(name, help="поиск фрагментов с учётом роли (ответ не генерирует)")
        p.add_argument("--question", required=True)
        p.add_argument("--role", required=True)
        p.add_argument("--top-k", type=_top_k, default=None)
        p.add_argument("--output", default=None)
    f = sub.add_parser("finalize", help="проверить raw-ответ ИИ по результату поиска и сохранить историю")
    f.add_argument("--retrieval", required=True)
    f.add_argument("--answer-file", required=True)
    pol = sub.add_parser("policy", help="настройки поведения")
    psub = pol.add_subparsers(dest="pcmd", required=True)
    psub.add_parser("show")
    pu = psub.add_parser("use")
    pu.add_argument("--version", required=True)
    args = ap.parse_args(argv)

    from . import documents as D, evidence as E, model as M, policy as P, storage as S

    try:
        if args.cmd == "prepare-model":
            _print(M.prepare_model())
        elif args.cmd == "access-sync":
            _print(D.access_sync())
        elif args.cmd == "validate-docs":
            r = D.validate_docs()
            _print(r)
            return 0 if r["status"] == "documents_valid" else 1
        elif args.cmd == "chunks":
            r = S.write_chunks_evidence()
            _print(r)
            return 0 if not r["verbatim_errors"] else 1
        elif args.cmd == "index":
            _print(S.build_index())
        elif args.cmd == "status":
            man = S.check_index()
            _print({"status": "index_current", "index_id": man["index_id"], "document_count": man["document_count"],
                    "chunk_count": man["chunk_count"], "collection": man["collection"]})
        elif args.cmd in ("retrieve", "ask"):
            result, path = S.retrieve(args.question, args.role, args.top_k, args.output)
            print(path.read_text(encoding="utf-8"))
            print(f"saved {S.rel(path)}; trace {result['retrieval_trace_path']}; context_state={result['context_state']}; "
                  f"hits={len(result['hits'])}", file=sys.stderr)
        elif args.cmd == "finalize":
            r = E.finalize(args.retrieval, args.answer_file)
            _print(r)
            print(f"result {S.rel(S.ROOT / 'evidence' / ('result-' + r['capture_id'] + '.json'))}; "
                  f"trace {r['trace_path']}; citation-map {r['citation_map_path']}", file=sys.stderr)
        elif args.cmd == "policy":
            _print(P.use(args.version) if args.pcmd == "use" else P.show())
    except E.FinalizeError as e:
        print("finalize: ответ отклонён, result не создан:", file=sys.stderr)
        for err in e.errors:
            print("  - " + err, file=sys.stderr)
        return 2
    except (S.StaleIndex, S.RetrievalError, D.CorpusError, M.ModelError, P.PolicyError) as e:
        print(f"ошибка: {e}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
