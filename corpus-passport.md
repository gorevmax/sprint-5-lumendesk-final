# Паспорт базы знаний LumenDesk

Сгенерировано `scripts/prepare.py` из `inventory.csv` / `registry/registry.csv`. Не редактировать вручную.

## Назначение

База для RAG-помощника сотрудников поддержки LumenDesk (роли `support_agent`, `support_lead`). Помощник отвечает на русском по разрешённым действующим материалам: тарифы, рабочие пространства, файлы, восстановление, поддержка, API, настройки доступа. Английские и французские документы переведены на русский; каждый фрагмент ссылается на оригинал и точное место в нём.

## Состав: 50 файлов, включено 42, исключено 8

Фрагментов всего 1332, в поиск идёт 962, в карантине 2.

### Включённые файлы

| № | Путь | id | Язык | Доступ | Пометки |
|---|---|---|---|---|---|
| 2 | `documents/Выгрузки/Downloads/SAML cutover - September.md` | saml-cutover-notes | en | support_agent,support_lead | личная копия |
| 3 | `documents/Выгрузки/Downloads/Поиск - заметки 01 09.txt` | search-notes | ru | support_agent,support_lead |  |
| 4 | `documents/Выгрузки/September incident register.xlsx` | incident-register-2026-09 | en | support_agent,support_lead |  |
| 5 | `documents/Выгрузки/hosting regions export.csv` | hosting-regions | en | support_agent,support_lead | владелец не указан |
| 6 | `documents/Выгрузки/webhooks-reprises.csv` | webhook-retries | fr | support_agent,support_lead | владелец не указан |
| 7 | `documents/Выгрузки/параметры-входа.csv` | saml-parameters | ru | support_agent,support_lead |  |
| 8 | `documents/Клиентский сервис/Customer handover.docx` | onboarding-handover | en | support_agent,support_lead | карантин 2 фрагм. |
| 9 | `documents/Клиентский сервис/Privacy/Обращения о данных.pdf` | privacy-requests | ru | support_agent,support_lead |  |
| 10 | `documents/Клиентский сервис/Team service credits.docx` | team-service-credits-support | en | support_agent,support_lead | противоречие CONF-team-credit-rate |
| 11 | `documents/Клиентский сервис/response targets final.xlsx` | response-targets | en | support_agent,support_lead |  |
| 12 | `documents/Клиентский сервис/Для руководителей/Разбор злоупотреблений.md` | abuse-review | ru | support_lead |  |
| 13 | `documents/Клиентский сервис/Корзина и восстановление.md` | trash-recovery | ru | support_agent,support_lead | основной экземпляр DUP-trash |
| 14 | `documents/Клиентский сервис/Письма/Пароль, письмо не пришло.txt` | password-reset | ru | support_agent,support_lead |  |
| 15 | `documents/Клиентский сервис/Сбой сервиса - рассылка.pdf` | outage-communication | ru | support_agent,support_lead |  |
| 16 | `documents/Клиентский сервис/Смена/Как назначаем срочность — 01.09.md` | incident-priority | ru | support_agent,support_lead |  |
| 17 | `documents/Клиентский сервис/хранение - сверка сентября.csv` | retention-reconciliation | ru | support_agent,support_lead | владелец не указан |
| 21 | `documents/Планирование/Клиенты/Гости — новый порядок.md` | guest-access | ru | support_agent,support_lead |  |
| 22 | `documents/Планирование/Тарифы новый.xlsx` | plan-capabilities | ru | support_agent,support_lead |  |
| 23 | `documents/Платформа и интеграции/API/ответы api новый.csv` | api-errors | ru | support_agent,support_lead | владелец не указан |
| 24 | `documents/Платформа и интеграции/Browser notes final.txt` | browser-support | en | support_agent,support_lead |  |
| 25 | `documents/Платформа и интеграции/Marketplace/Approval and removal - копия.md` | marketplace-approval-retirement | en | support_agent,support_lead |  |
| 26 | `documents/Платформа и интеграции/SAML incident handling.docx` | saml-incident-escalation | en | support_agent,support_lead |  |
| 27 | `documents/Платформа и интеграции/marketplace capabilities.xlsx` | marketplace-catalogue | en | support_agent,support_lead |  |
| 28 | `documents/Платформа и интеграции/Выгрузка карточек.md` | card-export | ru | support_agent,support_lead |  |
| 29 | `documents/Платформа и интеграции/Лимиты файлов.xlsx` | file-limits | ru | support_agent,support_lead |  |
| 30 | `documents/Платформа и интеграции/Передача владельца копия.docx` | workspace-ownership-transfer | ru | support_agent,support_lead |  |
| 31 | `documents/Платформа и интеграции/Ротация ключей.md` | api-key-rotation | ru | support_agent,support_lead | основной экземпляр DUP-api-key |
| 32 | `documents/Рабочие копии/Downloads/Export security final.pdf` | export-security | en | support_agent,support_lead |  |
| 33 | `documents/Рабочие копии/Downloads/notification-events sept.csv` | notification-rules | en | support_agent,support_lead | владелец не указан |
| 34 | `documents/Рабочие копии/Downloads/Домен финальный.docx` | domain-verification | ru | support_agent,support_lead |  |
| 35 | `documents/Рабочие копии/Notifications final.md` | notification-explainer | en | support_agent,support_lead |  |
| 36 | `documents/Рабочие копии/Relais français 2026-09.txt` | french-handoff | fr | support_agent,support_lead |  |
| 41 | `documents/Финансы/Contrats France/Résidence Paris.pdf` | france-data-residency | fr | support_agent,support_lead |  |
| 42 | `documents/Финансы/Invoice correction - mail copy.txt` | invoice-correction | en | support_agent,support_lead |  |
| 43 | `documents/Финансы/Team service credits.pdf` | team-service-credits-finance | en | support_agent,support_lead | противоречие CONF-team-credit-rate |
| 44 | `documents/Финансы/Для руководителей/Аудит сентябрь.xlsx` | audit-log-review | ru | support_lead |  |
| 45 | `documents/Финансы/Для руководителей/Возвраты оплаты.docx` | refund-approval | ru | support_lead |  |
| 46 | `documents/Франция/Accessibilité septembre.pdf` | accessibility-fr | fr | support_agent,support_lead |  |
| 47 | `documents/Франция/Assistant abonnement.xlsx` | assistant-quota | fr | support_agent,support_lead |  |
| 48 | `documents/Франция/Atelier équipe septembre.md` | workshop-fr | fr | support_agent,support_lead |  |
| 49 | `documents/Франция/Rappels et jours fériés.pdf` | callbacks-fr | fr | support_agent,support_lead |  |
| 50 | `documents/Франция/organisation/Calendrier support 2026.docx` | support-calendar-fr | fr | support_agent,support_lead |  |

### Исключённые файлы и причины

| № | Путь | Правило | Причина |
|---|---|---|---|
| 1 | `documents/Архив 2025/экспорт-карточек.txt` | R2 | Старая версия: в тексте «С сентября 2026 года порядок ниже заменён», заменена №28 (card-export 2026-09-01). |
| 18 | `documents/Планирование/Procédures - publication copie.docx` | R7 | Внутренний порядок публикации справочных карточек; вне круга вопросов помощника. Оригинал «copie» в корпусе не найден. |
| 19 | `documents/Планирование/Team Flex — новый вариант.txt` | R3 | Гипотеза: «не опубликован как предложение клиентам… не образуют действующие условия договора». Имя «новый вариант» не делает его действующей версией. |
| 20 | `documents/Планирование/assistant-hypotheses.csv` | R3 | Гипотезы: «Aucun avenant client ne reprend ces valeurs», «Le comité produit doit encore décider». Действующие квоты — №47. |
| 37 | `documents/Рабочие копии/recovery-notes.txt` | R4 | Полный дубль №13 на английском (абзац в абзац, проверено после перевода); связанная копия в группе DUP-trash. |
| 38 | `documents/Рабочие копии/Миграция/Приёмка - 18 сентября.xlsx` | R8 | Снимок сверки конкретной миграции 18.09.2026 без владельца; общими правилами не является. |
| 39 | `documents/Рабочие копии/Памятка ротации API.pdf` | R4 | Полный дубль №31 (текст совпадает на 99,9 %), PDF-копия в «Рабочих копиях»; связанная копия в группе DUP-api-key. |
| 40 | `documents/Рабочие копии/квоты для презентации.csv` | R6 | Материал для презентации без владельца и даты; лимиты вложений совпадают с №29, а квоты активных карточек и правило о публичных ссылках другими документами не подтверждены. |

## Правила отбора

- **R1.** Действующий материал: в тексте указаны команда-владелец и дата вступления или сверки не ранее 2026-09-01, нет пометок о замене, черновике или гипотезе.
- **R2.** Заменённая версия исключается, если в тексте одного из документов прямо сказано о замене.
- **R3.** Черновики, гипотезы и неутверждённые предложения исключаются из поиска по текущим правилам: в тексте прямо указано, что условия не действуют.
- **R4.** Полный дубль (совпадение текста или перевода по абзацам): основной экземпляр включается, копия хранится как связанная (exclude), её места указываются в фрагментах основного. Одинаковые сведения не считаются независимыми подтверждениями.
- **R5.** Материал без указанного владельца включается с пометкой trust=unconfirmed_origin, если он лежит в рабочих папках компании, датирован сентябрём 2026 по данным внутри и не противоречит материалам с установленным владельцем. Ответ по такому фрагменту должен упоминать, что владелец источника не указан.
- **R6.** Материалы, подготовленные для презентации, без владельца и даты исключаются: их уникальные условия не подтверждены другими документами.
- **R7.** Материал вне круга вопросов помощника (внутренний процесс оформления справочных карточек) исключается из поиска.
- **R8.** Снимок конкретной работы без общих правил и без владельца исключается из поиска по правилам.
- **R9.** Фрагменты с текстом, адресованным ассистенту (prompt injection), помещаются в карантин: не индексируются, документ включается.
- **R10.** Пометка «Только руководителям поддержки» или прямой запрет выдачи первой линии → доступ только support_lead. Остальное — support_agent и support_lead.
- **R11.** Противоречащие действующие документы включаются оба с общей conflict_group; ответ показывает оба источника и предлагает эскалацию (по указанию №15).
- **R12.** Частичное совпадение не является дублем: оба документа включаются, связь фиксируется в related.
