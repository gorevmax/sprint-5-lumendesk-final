---
source_path: "documents/Клиентский сервис/response targets final.xlsx"
format: "xlsx"
source_sha256: "1e944f5e57f0ff463bd9ad37560fb4f7da6f2db7f39314b1047d467e0110ac77"
extractor: "extract-1"
---
## Лист: Targets

Название листа: First human response

Примечание листа: Support Operations, September 2026. The target starts after a complete incident report arrives. A first response target does not promise repair time.

Столбцы: Case | Target | Unit | When it applies

- [строка 8] Case: Enterprise P1; Target: 15; Unit: minutes; When it applies: 24 hours every day
- [строка 9] Case: Enterprise P2; Target: 60; Unit: minutes; When it applies: 24 hours every day
- [строка 10] Case: Team P1; Target: 60; Unit: minutes; When it applies: Business support hours
- [строка 11] Case: Team P2; Target: 240; Unit: minutes; When it applies: Business support hours
- [строка 12] Case: Starter; Target: 2; Unit: business days; When it applies: All supported priorities
- [строка 13] Case: Business support hours; Target: 09:00 to 18:00; Unit: Europe/Berlin; When it applies: Monday through Friday excluding contract holidays
- [строка 14] Case: Required context; Target: Workspace ID and impact; Unit: evidence; When it applies: Also include UTC start time and contact
- [строка 15] Case: Clock start; Target: Complete report received; Unit: event; When it applies: Missing required context pauses target measurement
- [строка 16] Case: Update frequency P1; Target: 30; Unit: minutes; When it applies: During active investigation
- [строка 17] Case: Resolution; Target: No fixed time; Unit: rule; When it applies: Do not present first response as a repair guarantee

## Лист: Queue review

Название листа: September queue samples

Столбцы: Received UTC | Plan | Priority | Complete context | Owner action | Observation

- [строка 6] Received UTC: 2026-09-07 07:12; Plan: Enterprise; Priority: P1; Complete context: Workspace and UTC start supplied; Owner action: Response team paged; Observation: All participants unable to open cards; no workaround
- [строка 7] Received UTC: 2026-09-07 09:38; Plan: Team; Priority: P2; Complete context: Complete; Owner action: Reproduce attachment delay; Observation: Uploads work after retry; customer can continue by link
- [строка 8] Received UTC: 2026-09-07 13:04; Plan: Starter; Priority: P3; Complete context: Browser version missing; Owner action: Request client version; Observation: Only one participant sees a stale preview
- [строка 9] Received UTC: 2026-09-08 00:47; Plan: Enterprise; Priority: P1; Complete context: Complete; Owner action: Acknowledge and coordinate; Observation: Emergency administrator remains available; impact confirmed
- [строка 10] Received UTC: 2026-09-08 10:16; Plan: Team; Priority: P2; Complete context: Impact not yet stated; Owner action: Ask what work is blocked; Observation: Report names an error but omits affected workflow
- [строка 11] Received UTC: 2026-09-08 15:51; Plan: Enterprise; Priority: P2; Complete context: Complete; Owner action: Check integration consent; Observation: Connector disabled after vendor scope change
- [строка 12] Received UTC: 2026-09-09 08:13; Plan: Starter; Priority: P4; Complete context: Complete; Owner action: Answer configuration question; Observation: Customer asks how to change their own timezone
- [строка 13] Received UTC: 2026-09-09 11:29; Plan: Team; Priority: P1; Complete context: Complete; Owner action: Link confirmed incident; Observation: Workspace unavailable; status update posted separately
- [строка 14] Received UTC: 2026-09-10 16:42; Plan: Team; Priority: P2; Complete context: UTC start missing; Owner action: Clarify original local time; Observation: Customer supplied Paris time without date
- [строка 15] Received UTC: 2026-09-11 06:03; Plan: Enterprise; Priority: P2; Complete context: Complete; Owner action: Inspect safe request evidence; Observation: Sign-in succeeds for pilots; one account still needs review
- [строка 16] Received UTC: 2026-09-11 14:37; Plan: Team; Priority: P3; Complete context: Complete; Owner action: Verify search visibility; Observation: Missing result belongs to a space the user cannot access
- [строка 17] Received UTC: 2026-09-12 09:22; Plan: Starter; Priority: P4; Complete context: Invoice reference missing; Owner action: Ask for invoice reference; Observation: Correction request must remain with Billing Support
- [строка 18] Received UTC: 2026-09-14 09:06; Plan: Team; Priority: P2; Complete context: Complete; Owner action: Check export filter; Observation: Selection exceeds current per-job allowance
- [строка 19] Received UTC: 2026-09-14 11:48; Plan: Enterprise; Priority: P1; Complete context: Complete; Owner action: Start response coordination; Observation: Report covers one affected region, not every workspace
- [строка 20] Received UTC: 2026-09-15 10:31; Plan: Team; Priority: P3; Complete context: Complete; Owner action: Review notification preference; Observation: Read event arrived before the email delay ended
- [строка 21] Received UTC: 2026-09-16 12:17; Plan: Enterprise; Priority: P2; Complete context: Contact missing; Owner action: Confirm available administrator; Observation: Technical context is complete, recovery contact still needed

## Лист: Shift discussion

Название листа: Questions from the rota meeting

Столбцы: Topic | Agreed interpretation

- [строка 6] Topic: Working hours; Agreed interpretation: 09:00 to 18:00 Europe/Berlin, Monday to Friday, excluding contract holidays
- [строка 7] Topic: Enterprise P1; Agreed interpretation: 15 minutes, every day around the clock
- [строка 8] Topic: Team P1; Agreed interpretation: 60 minutes during business support hours
- [строка 9] Topic: Missing evidence; Agreed interpretation: Request workspace, impact, UTC start time and contact
- [строка 10] Topic: P1 communication; Agreed interpretation: Updates every 30 minutes during investigation
- [строка 11] Topic: Resolution; Agreed interpretation: No fixed repair time is implied by first response
