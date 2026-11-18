"""Загрузка локальной модели E5 и кодирование текстов.

index и retrieve используют один загрузчик load_local_model(): модель читается только из
models/multilingual-e5-base (local_files_only=True, device="cpu"); другая модель
автоматически не скачивается.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
import unicodedata

from .config import MODEL_DIR, MODEL_FILES, MODEL_ID, MODEL_SOURCE, PROFILE, ROOT

_MODEL = None


class ModelError(RuntimeError):
    pass


def missing_files() -> list[str]:
    return [f for f in MODEL_FILES if not (MODEL_DIR / f).is_file()]


def file_sha256(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def model_hashes() -> dict[str, str]:
    """SHA-256 десяти файлов модели (model-source.json и .cache не входят)."""
    return {f: file_sha256(MODEL_DIR / f) for f in MODEL_FILES}


def load_local_model():
    global _MODEL
    if _MODEL is not None:
        return _MODEL
    miss = missing_files()
    if miss:
        raise ModelError(
            f"в {MODEL_DIR.relative_to(ROOT).as_posix()} нет файлов модели: {', '.join(miss)}. "
            "Скачайте их вручную со страницы модели или выполните python -m rag_demo prepare-model")
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(str(MODEL_DIR), device="cpu", local_files_only=True)
    dim = model.get_sentence_embedding_dimension()
    if dim != PROFILE["dimension"]:
        raise ModelError(f"размерность модели {dim}, ожидается {PROFILE['dimension']}")
    if str(model.device) != "cpu":
        raise ModelError(f"модель загружена на {model.device}, ожидается cpu")
    _MODEL = model
    return model


def tokenizer():
    return load_local_model().tokenizer


def token_count(text: str) -> int:
    """Число токенов вместе со спецтокенами E5 (<s>, </s>), без усечения."""
    return len(tokenizer()(text, add_special_tokens=True, truncation=False)["input_ids"])


def normalize_for_embedding(text: str) -> str:
    """NFC и одинаковая нормализация пробелов — только для текста, идущего в модель."""
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", text)).strip()


def encode_passages(texts: list[str], batch_size: int = 16):
    model = load_local_model()
    return model.encode([normalize_for_embedding(t) for t in texts], prompt=PROFILE["passage_prefix"],
                        normalize_embeddings=True, batch_size=batch_size, show_progress_bar=False,
                        convert_to_numpy=True)


def encode_query(text: str):
    model = load_local_model()
    return model.encode([normalize_for_embedding(text)], prompt=PROFILE["query_prefix"],
                        normalize_embeddings=True, show_progress_bar=False, convert_to_numpy=True)[0]


def write_model_source(hashes: dict[str, str]) -> dict:
    data = {"model_id": MODEL_ID, "local_path": MODEL_DIR.relative_to(ROOT).as_posix(),
            "dimension": PROFILE["dimension"], "device": "cpu", "files_sha256": hashes}
    MODEL_SOURCE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return data


def prepare_model() -> dict:
    """Скачать необходимые файлы модели (только если их нет) и проверить общим загрузчиком."""
    miss = missing_files()
    if miss:
        from huggingface_hub import snapshot_download

        print(f"скачиваю {len(miss)} файл(ов) модели {MODEL_ID}", file=sys.stderr)
        snapshot_download(repo_id=MODEL_ID, allow_patterns=MODEL_FILES, local_dir=str(MODEL_DIR))
    load_local_model()
    return {"status": "model_ready", "model_id": MODEL_ID, "downloaded": miss,
            "local_path": MODEL_DIR.relative_to(ROOT).as_posix(), "dimension": PROFILE["dimension"]}
