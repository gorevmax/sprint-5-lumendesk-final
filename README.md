# LumenDesk: RAG-помощник по документам компании

Создайте с помощью ИИ RAG-помощника для поддержки LumenDesk — вымышленной платформы совместной работы. Исходные данные — **50 документов в папке [documents](documents/)**: тексты, таблицы, PDF и Word на русском, английском и французском.

Работайте в отдельном приложении ИИ или в VS Code с расширением ИИ, которое имеет доступ к папке проекта и может выполнять команды. Под «чатом ИИ» понимается чат в этом приложении или расширении.

Разберите материалы, переведите английские и французские тексты на русский язык и подготовьте единую базу. Сохраните оригиналы и связь переводов с ними. Самостоятельно разберитесь с дублями, старыми версиями, черновиками и ограничениями доступа.

Постройте поиск по подготовленной базе. Помощник должен отвечать на русском языке, ссылаться на проверяемые места в оригиналах, уточнять недостающие условия и обозначать ситуации, в которых нужен человек.

**Докажите, что RAG работает:** задайте вопросы по документам через настоящий поиск, сверьте ответы с документами и сохраните результаты и скриншоты из чата ИИ. Покажите работу с таблицами, переводами, повторами, противоречиями и ограничениями доступа.

---

## Как устроен помощник

```
documents/ (50 исходников, не меняются)
  └─ scripts/extract.py → segment.py → translate.py/translations/ → prepare.py
       └─ corpus/prepared/*.json   русский текст (оригинал или проверенный перевод) + оригинал + точное место
            └─ python -m rag_demo index      E5 → Chroma .rag_store/ (коллекция lumendesk-support)
                 └─ python -m rag_demo ask   вопрос + роль → разрешённые фрагменты с происхождением (JSON)
                      └─ ИИ в чате пишет evidence/answer-{run}.raw.json по rag-policy.md
                           └─ python -m rag_demo finalize   проверка ссылок → result / trace / citation-map
```

- **Python** строит индекс и находит фрагменты. Сам ответа не пишет.
- **Модель чата ИИ** отвечает только по `text` найденных фрагментов текущего поиска ([rag-policy.md](rag-policy.md), [behavior/system-v2.md](behavior/system-v2.md)). Ни ответы, ни номера контрольных вопросов в коде не зашиты.
- **Роль** (`support_agent`, `support_lead`) передаётся в поиск. Права на документы задаёт [access.csv](access.csv). Роль подставляется в фильтр Chroma `where={"document_id": {"$in": …}}`, поэтому тексты закрытых документов из базы вообще не извлекаются. Параметр `--role` не является аутентификацией.

### Команды (`python -m rag_demo …`)

| Команда | Что делает |
|---|---|
| `prepare-model` | скачивает файлы `intfloat/multilingual-e5-base` в `models/multilingual-e5-base`, только если их нет |
| `access-sync` | записывает `access.csv` (doc_id → роли) по реестру `registry/registry.csv` |
| `validate-docs` | проверяет inventory (50 строк, уникальные id у include), подготовленный корпус, sha256 исходников, доступ и проверку переводов |
| `chunks` | нарезает корпус и сохраняет `evidence/chunks.json`, проверяя дословность |
| `index` | строит индекс: эмбеддинги на CPU, размерность 768, `model-source.json`, `.rag_store/manifest.json`, `evidence/technical-passport.json` |
| `status` | проверяет, что сохранённый индекс актуален |
| `ask` / `retrieve` | `--question "…" --role <роль> [--top-k 8] [--output evidence/retrieval-{run}.json]`: выполняет поиск и печатает JSON, идентичный сохранённому файлу |
| `finalize` | `--retrieval … --answer-file …`: проверяет ответ ИИ и сохраняет `result-`, `trace-`, `citation-map-{capture_id}.json` |
| `policy show` / `policy use --version v3` | показывает или выбирает настройки поведения (`behavior/v3.json`; `v2` сохранена для воспроизведения раунда A) |

### Одна операция поиска на вопрос (`ask`)

1. Проверяются вопрос (не пустой, не длиннее 512 токенов вместе с `query: `), `top_k` и роль.
2. Проверяется актуальность индекса. Сверяются:
   - `inventory.csv`;
   - sha256 исходников и подготовленных текстов;
   - файлы переводов и решений;
   - профиль нарезки и эмбеддингов;
   - SHA-256 десяти файлов модели;
   - коллекция.

   Если что-то не совпадает, команда возвращает `stale` и не выполняет поиск.
3. По `access.csv` выбираются документы, разрешённые роли. Chroma ищет только среди них: до 8 кандидатов, метрика cosine, вектор вопроса строит та же E5.
4. Отсекаются кандидаты с `distance > 0.20` (`retrieval_threshold`). В политике v3 (активна) к 8 векторным фрагментам добавляются до 2 кандидатов из прошедших порог, лучших по совпадению слов вопроса (BM25, `filtering.lexical_added`).
5. По закрытым документам вычисляются только расстояния (`restricted_probe`). Их ID, названия и тексты никуда не записываются.
6. Определяется `context_state`:
   - `available` — допущенные фрагменты есть;
   - `forbidden` — разрешённых фрагментов нет, а закрытый фрагмент ближе 0,35 и (в v3) ближе лучшего разрешённого кандидата;
   - `empty` — в остальных случаях.
7. Каждый hit содержит `rank`, `chunk_id`, `text` (дословный русский текст), `metadata` и `distance`. Кроме того, в hit есть `provenance` — подготовленные фрагменты внутри чанка с их местом в оригинале, отрывком оригинала (`text_orig`) для переводов, ячейками таблиц и указанием, как обращаться с фрагментом.

### Ответ и цитаты

В raw-ответе ровно три поля: `answer`, `citations` (`document_id`, `chunk_id`, `quote`) и `decision`. Значение `decision` — одно из `answer`, `clarify`, `escalate`, `refuse`.

`finalize` проверяет:
- `chunk_id` есть в hits этого поиска;
- `document_id` совпадает с документом этого hit;
- `quote` — дословная подстрока `hit.text`;
- hits не изменены относительно коллекции;
- документ доступен роли;
- индекс и настройки не изменились после поиска;
- `decision` согласован с `context_state`: при `refuse` цитат нет, `answer` и `escalate` требуют цитат.

Затем `finalize` дописывает к каждой цитате место в оригинале:

| Формат | Место в оригинале |
|---|---|
| Markdown / TXT | файл, раздел, строки и номер фрагмента (`29-005`) |
| CSV | файл, строка, названия столбцов (оригинальные, рядом русские) |
| Excel | файл, лист, ячейки или диапазон (у названия листа — объединённые ячейки) |
| PDF | файл и страница |
| Word | файл, раздел и номер абзаца |

Для переводов в `result` и `citation-map` рядом с цитатой кладётся `original_excerpt` — текст оригинала. Названия и пути исходных файлов остаются как есть (EN/FR).

Проверка происхождения не заменяет проверку смысла. Каждый тезис ответа человек сверяет с оригиналом.

### Что сохраняется (история после закрытия чата)

| Файл | Содержание |
|---|---|
| `evidence/retrieval-{run}.json` | вопрос, роль, настройки (версия и хеши политики), index_id, context_state, filtering, hits с происхождением, context |
| `evidence/retrieval-trace-{query_id}.json` | все кандидаты, включая отсечённые порогом, и разрешённые документы |
| `evidence/answer-{run}.raw.json` | фактический ответ ИИ |
| `evidence/result-{capture_id}.json` | ответ, decision, проверенные цитаты с местом и отрывком оригинала |
| `evidence/trace-{capture_id}.json` | вопрос, роль, настройки, полный результат поиска, контекст, raw-ответ и итог проверки |
| `evidence/citation-map-{capture_id}.json` | цитата → hit → фрагмент → место в документе |
| `evidence/history.jsonl` | журнал всех index, retrieve, finalize и отклонённых finalize |

`evidence/`, `.rag_store/`, `models/` и `.venv*` перечислены в `.gitignore`. Это локальные результаты: они остаются на диске, но в репозиторий не попадают.

## Повторить маршрут

Требования: Python 3.13 (Windows x64 или macOS Apple Silicon), CPU. При первой установке нужен интернет. Нужно около 3 ГБ на диске под библиотеки и модель. Все команды выполняются из корня проекта.

### Windows (PowerShell)

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements-windows.txt
.\.venv\Scripts\python.exe -m pip check
# только если в models\multilingual-e5-base нет файлов модели (~1,1 ГБ):
.\.venv\Scripts\python.exe -m rag_demo prepare-model
.\.venv\Scripts\python.exe -m rag_demo access-sync
.\.venv\Scripts\python.exe -m rag_demo validate-docs
.\.venv\Scripts\python.exe -m rag_demo policy use --version v3
.\.venv\Scripts\python.exe -m rag_demo index
# поиск — отдельным процессом по сохранённому индексу:
.\.venv\Scripts\python.exe -m rag_demo ask --question 'Какой предел одного вложения на Team?' --role support_agent --top-k 8 --output evidence\retrieval-q01-agent.json
# ИИ читает JSON, пишет evidence\answer-q01-agent.raw.json по rag-policy.md, затем:
.\.venv\Scripts\python.exe -m rag_demo finalize --retrieval evidence\retrieval-q01-agent.json --answer-file evidence\answer-q01-agent.raw.json
.\.venv\Scripts\python.exe -m pytest -q
```

### macOS Apple Silicon (bash/zsh)

```bash
python3.13 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements-macos.txt
.venv/bin/python -m pip check
# только если в models/multilingual-e5-base нет файлов модели (~1,1 ГБ):
.venv/bin/python -m rag_demo prepare-model
.venv/bin/python -m rag_demo access-sync
.venv/bin/python -m rag_demo validate-docs
.venv/bin/python -m rag_demo policy use --version v3
.venv/bin/python -m rag_demo index
.venv/bin/python -m rag_demo ask --question 'Какой предел одного вложения на Team?' --role support_agent --top-k 8 --output evidence/retrieval-q01-agent.json
.venv/bin/python -m rag_demo finalize --retrieval evidence/retrieval-q01-agent.json --answer-file evidence/answer-q01-agent.raw.json
.venv/bin/python -m pytest -q
```

Если файл `--output` уже существует, `ask` откажется его перезаписывать. В этом случае выберите новое имя `{run}`. Маршрут macOS описан по тем же командам, но фактически проверен только на Windows (см. ниже).

Подготовка корпуса (`scripts/extract.py` → `segment.py` → `prepare.py`, проверки `check_extraction.py`, `check_translation.py`, `verify_prepared.py`) уже выполнена, её результат лежит в `corpus/prepared/`. Повторять её нужно только после изменения документов, переводов или решений. После этого обязательно выполнить `index`.

## Результаты проверки

Полный прогон 12 контрольных вопросов (ожидания, оценки, ошибки, правки v2 → v3, повторные проверки) — в [results.md](results.md).

## Фактический результат первой сессии (Windows 11, x64, Python 3.13.16, CPU)

- `pip check`: No broken requirements found.
- `validate-docs`: `documents_valid`, 50 файлов, 42 include, 8 exclude. Шесть CSV не имеют названия в самом документе (предупреждение), поэтому в индексе их название — имя файла.
- `index`: `indexed`, 42 документа, 692 чанка (175 текстовых и 517 строк таблиц), максимум 379 из 384 токенов, размерность 768, CPU, cosine, около 133 с.
- **Вопрос 1** (`support_agent`): «Какой предел одного вложения на Team?»
  - `ask` отдельным процессом: `available`, 8 hits, лучший — `file-limits::chunk-03` (distance 0,121).
  - Ответ: **100 MiB на один файл** — «Лимиты файлов.xlsx», лист «Тарифы», ячейки A9:D9.
  - `finalize`: `finalized`. Смысл сверен с ячейками xlsx, прочитанными напрямую.
  - Первая версия ответа содержала тезис без цитаты. Он исправлен в `answer-q01-agent-v2.raw.json`, обе проверки сохранены в истории.
- Отрицательные проверки на копиях raw-ответа (`evidence/negative/`): неизвестный `chunk_id`, выдуманная `quote`, чужой `document_id`, `refuse` с цитатами. Во всех четырёх случаях код 2, новых result нет.
- Устаревание: после изменения подготовленного текста команда `status` вернула `stale`; после восстановления файла байт в байт — `index_current`.
- `pytest`: 7 passed (после правок v3 — 9 passed).

Ограничения:
- Роль — локальный параметр, а не проверка личности.
- Порог 0,20 — исходная настройка, нужна дальнейшая оценка на остальных контрольных вопросах.
- `authorization_probe_distance = 0.35` для E5 широк: для первого вопроса все 8 ближайших закрытых фрагментов были ближе 0,35. Поэтому `forbidden` выбирается только когда разрешённого контекста нет совсем.
- Внешняя эскалация человеку не выполняется.
