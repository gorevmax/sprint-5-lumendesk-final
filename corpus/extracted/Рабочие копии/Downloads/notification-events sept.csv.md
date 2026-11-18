---
source_path: "documents/Рабочие копии/Downloads/notification-events sept.csv"
format: "csv"
source_sha256: "f7c1f9ef5df46e4412b12370d8af3fda98f6bce39d5e0f3f2f0d49894001a907"
extractor: "extract-1"
---
Столбцы: Trigger | Channel or rule | Delay or explanation | Observed at | Member timezone | Outcome

- [строка 2] Trigger: Mention; Channel or rule: rule; Delay or explanation: A direct mention creates an in-app notification immediately.
- [строка 3] Trigger: Email; Channel or rule: rule; Delay or explanation: Mention email is sent after a 5 minute delay if the item remains unread.
- [строка 4] Trigger: Digest; Channel or rule: rule; Delay or explanation: The daily digest is delivered at 08:00 in the member timezone.
- [строка 5] Trigger: Quiet hours; Channel or rule: rule; Delay or explanation: Quiet hours suppress email and push between 22:00 and 08:00 local time.
- [строка 6] Trigger: Critical notices; Channel or rule: rule; Delay or explanation: Security sign-in alerts ignore quiet hours.
- [строка 7] Trigger: Muted thread; Channel or rule: rule; Delay or explanation: A muted thread suppresses ordinary replies but still allows direct mentions.
- [строка 8] Trigger: Membership; Channel or rule: rule; Delay or explanation: Removed members receive no new workspace notifications.
- [строка 9] Trigger: Troubleshooting; Channel or rule: rule; Delay or explanation: Check user preferences, timezone and spam folder before escalating.
- [строка 10] Trigger: Evidence; Channel or rule: rule; Delay or explanation: Collect notification ID and delivery timestamp, never a mailbox password.
- [строка 11] Trigger: direct mention; Channel or rule: in-app; Delay or explanation: immediate; Observed at: 2026-09-07 07:00 UTC; Member timezone: Europe/Berlin; Outcome: unread
- [строка 12] Trigger: direct mention; Channel or rule: email; Delay or explanation: 5 minutes; Observed at: 2026-09-07 07:07 UTC; Member timezone: Europe/Paris; Outcome: read before delay; email cancelled
- [строка 13] Trigger: thread reply; Channel or rule: email; Delay or explanation: suppressed; Observed at: 2026-09-07 07:14 UTC; Member timezone: America/Toronto; Outcome: muted thread
- [строка 14] Trigger: security sign-in; Channel or rule: email; Delay or explanation: immediate; Observed at: 2026-09-07 07:21 UTC; Member timezone: Europe/Berlin; Outcome: quiet hours do not suppress security
- [строка 15] Trigger: daily digest; Channel or rule: email; Delay or explanation: 08:00 local; Observed at: 2026-09-07 07:28 UTC; Member timezone: Europe/Paris; Outcome: member timezone
- [строка 16] Trigger: removed member; Channel or rule: all; Delay or explanation: none; Observed at: 2026-09-07 07:35 UTC; Member timezone: America/Toronto; Outcome: membership ended
- [строка 17] Trigger: direct mention; Channel or rule: in-app; Delay or explanation: immediate; Observed at: 2026-09-08 07:00 UTC; Member timezone: Europe/Berlin; Outcome: unread
- [строка 18] Trigger: direct mention; Channel or rule: email; Delay or explanation: 5 minutes; Observed at: 2026-09-08 07:07 UTC; Member timezone: Europe/Paris; Outcome: read before delay; email cancelled
- [строка 19] Trigger: thread reply; Channel or rule: email; Delay or explanation: suppressed; Observed at: 2026-09-08 07:14 UTC; Member timezone: America/Toronto; Outcome: muted thread
- [строка 20] Trigger: security sign-in; Channel or rule: email; Delay or explanation: immediate; Observed at: 2026-09-08 07:21 UTC; Member timezone: Europe/Berlin; Outcome: quiet hours do not suppress security
- [строка 21] Trigger: daily digest; Channel or rule: email; Delay or explanation: 08:00 local; Observed at: 2026-09-08 07:28 UTC; Member timezone: Europe/Paris; Outcome: member timezone
- [строка 22] Trigger: removed member; Channel or rule: all; Delay or explanation: none; Observed at: 2026-09-08 07:35 UTC; Member timezone: America/Toronto; Outcome: membership ended
- [строка 23] Trigger: direct mention; Channel or rule: in-app; Delay or explanation: immediate; Observed at: 2026-09-09 07:00 UTC; Member timezone: Europe/Berlin; Outcome: unread
- [строка 24] Trigger: direct mention; Channel or rule: email; Delay or explanation: 5 minutes; Observed at: 2026-09-09 07:07 UTC; Member timezone: Europe/Paris; Outcome: read before delay; email cancelled
- [строка 25] Trigger: thread reply; Channel or rule: email; Delay or explanation: suppressed; Observed at: 2026-09-09 07:14 UTC; Member timezone: America/Toronto; Outcome: muted thread
- [строка 26] Trigger: security sign-in; Channel or rule: email; Delay or explanation: immediate; Observed at: 2026-09-09 07:21 UTC; Member timezone: Europe/Berlin; Outcome: quiet hours do not suppress security
- [строка 27] Trigger: daily digest; Channel or rule: email; Delay or explanation: 08:00 local; Observed at: 2026-09-09 07:28 UTC; Member timezone: Europe/Paris; Outcome: member timezone
- [строка 28] Trigger: removed member; Channel or rule: all; Delay or explanation: none; Observed at: 2026-09-09 07:35 UTC; Member timezone: America/Toronto; Outcome: membership ended
- [строка 29] Trigger: direct mention; Channel or rule: in-app; Delay or explanation: immediate; Observed at: 2026-09-10 07:00 UTC; Member timezone: Europe/Berlin; Outcome: unread
- [строка 30] Trigger: direct mention; Channel or rule: email; Delay or explanation: 5 minutes; Observed at: 2026-09-10 07:07 UTC; Member timezone: Europe/Paris; Outcome: read before delay; email cancelled
- [строка 31] Trigger: thread reply; Channel or rule: email; Delay or explanation: suppressed; Observed at: 2026-09-10 07:14 UTC; Member timezone: America/Toronto; Outcome: muted thread
- [строка 32] Trigger: security sign-in; Channel or rule: email; Delay or explanation: immediate; Observed at: 2026-09-10 07:21 UTC; Member timezone: Europe/Berlin; Outcome: quiet hours do not suppress security
- [строка 33] Trigger: daily digest; Channel or rule: email; Delay or explanation: 08:00 local; Observed at: 2026-09-10 07:28 UTC; Member timezone: Europe/Paris; Outcome: member timezone
- [строка 34] Trigger: removed member; Channel or rule: all; Delay or explanation: none; Observed at: 2026-09-10 07:35 UTC; Member timezone: America/Toronto; Outcome: membership ended
- [строка 35] Trigger: direct mention; Channel or rule: in-app; Delay or explanation: immediate; Observed at: 2026-09-11 07:00 UTC; Member timezone: Europe/Berlin; Outcome: unread
- [строка 36] Trigger: direct mention; Channel or rule: email; Delay or explanation: 5 minutes; Observed at: 2026-09-11 07:07 UTC; Member timezone: Europe/Paris; Outcome: read before delay; email cancelled
- [строка 37] Trigger: thread reply; Channel or rule: email; Delay or explanation: suppressed; Observed at: 2026-09-11 07:14 UTC; Member timezone: America/Toronto; Outcome: muted thread
- [строка 38] Trigger: security sign-in; Channel or rule: email; Delay or explanation: immediate; Observed at: 2026-09-11 07:21 UTC; Member timezone: Europe/Berlin; Outcome: quiet hours do not suppress security
- [строка 39] Trigger: daily digest; Channel or rule: email; Delay or explanation: 08:00 local; Observed at: 2026-09-11 07:28 UTC; Member timezone: Europe/Paris; Outcome: member timezone
- [строка 40] Trigger: removed member; Channel or rule: all; Delay or explanation: none; Observed at: 2026-09-11 07:35 UTC; Member timezone: America/Toronto; Outcome: membership ended
