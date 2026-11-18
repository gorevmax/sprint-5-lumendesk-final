"""Пути проекта и профиль построения индекса.

Профиль (PROFILE) входит в хеш индекса: изменение любого значения требует нового `index`.
Параметры поведения (порог, роли, решения) хранятся отдельно в behavior/*.json и
не требуют переиндексации.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

DOCUMENTS_DIR = ROOT / "documents"
INVENTORY = ROOT / "inventory.csv"
ACCESS = ROOT / "access.csv"
REGISTRY = ROOT / "registry" / "registry.csv"
PREPARED_DIR = ROOT / "corpus" / "prepared"

MODEL_ID = "intfloat/multilingual-e5-base"
MODEL_DIR = ROOT / "models" / "multilingual-e5-base"
MODEL_SOURCE = MODEL_DIR / "model-source.json"
MODEL_FILES = [
    "config.json",
    "model.safetensors",
    "modules.json",
    "sentence_bert_config.json",
    "1_Pooling/config.json",
    "tokenizer.json",
    "tokenizer_config.json",
    "special_tokens_map.json",
    "sentencepiece.bpe.model",
    "README.md",
]

STORE_DIR = ROOT / ".rag_store"
MANIFEST = STORE_DIR / "manifest.json"
CHUNK_STORE = STORE_DIR / "chunks.json"
COLLECTION = "lumendesk-support"

EVIDENCE_DIR = ROOT / "evidence"
HISTORY = EVIDENCE_DIR / "history.jsonl"

BEHAVIOR_DIR = ROOT / "behavior"
ACTIVE_POLICY = BEHAVIOR_DIR / "active.json"

PROFILE = {
    "model_id": MODEL_ID,
    "dimension": 768,
    "device": "cpu",
    "normalize_embeddings": True,
    "passage_prefix": "passage: ",
    "query_prefix": "query: ",
    "embedding_text": "title_ru + '\\n' + chunk text (NFC, пробелы схлопнуты); префикс добавляется один раз при encode",
    "text_normalization": "NFC + whitespace collapse, только для эмбеддингов",
    "chunker": "structural-v1",
    "chunk_rule": "введение и разделы H2 (лист для xlsx), по границам подготовленных фрагментов; строка таблицы — отдельный чанк с названием листа",
    "chunk_token_limit": 384,
    "chunk_overlap": 0,
    "query_token_limit": 512,
    "metric": "cosine",
    "collection": COLLECTION,
    "corpus_text": "text_ru из corpus/prepared (русский оригинал или проверенный перевод)",
}

DEFAULT_TOP_K = 8
