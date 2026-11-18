---
source_path: "documents/Платформа и интеграции/marketplace capabilities.xlsx"
format: "xlsx"
source_sha256: "bfe2848e167218e3cb65533c3313f17bf2dccbcab02a748e82fd04ad1f85a247"
extractor: "extract-1"
---
## Лист: Capabilities

Название листа: Marketplace integration capabilities

Примечание листа: Integrations reviewed this catalogue for the September release. Customer-hosted middleware remains the customer responsibility. A link never grants access to a private resource.

Столбцы: Integration or subject | Capability | Availability | Boundary

- [строка 8] Integration or subject: Slack; Capability: Mentions and card links; Availability: supported; Boundary: OAuth workspace approval required
- [строка 9] Integration or subject: Microsoft Teams; Capability: Channel notifications; Availability: supported; Boundary: Tenant administrator approval required
- [строка 10] Integration or subject: GitHub; Capability: Pull request links; Availability: supported; Boundary: Repository permissions are checked
- [строка 11] Integration or subject: Google Drive; Capability: File links and previews; Availability: supported; Boundary: LumenDesk does not copy Drive permissions
- [строка 12] Integration or subject: Jira Cloud; Capability: One-way issue links; Availability: supported; Boundary: No bidirectional field sync
- [строка 13] Integration or subject: Rate limits; Capability: Vendor limits apply; Availability: rule; Boundary: LumenDesk retries temporary vendor failures
- [строка 14] Integration or subject: Private resources; Capability: Existing access required; Availability: rule; Boundary: A link never grants access
- [строка 15] Integration or subject: Scope change; Capability: Administrator approval; Availability: rule; Boundary: New write scopes require fresh consent
- [строка 16] Integration or subject: Retirement; Capability: Disable then revoke; Availability: order; Boundary: Drain outbound queue for up to 15 minutes

## Лист: Vendor checks

Название листа: Connector review observations

Столбцы: Connector | Check | Account condition | Result or follow-up

- [строка 6] Connector: Slack; Check: Approval; Account condition: Workspace approved; Result or follow-up: Check consent for the requested workspace
- [строка 7] Connector: Microsoft Teams; Check: Approval; Account condition: Tenant administrator available; Result or follow-up: Check consent for the requested workspace
- [строка 8] Connector: GitHub; Check: Approval; Account condition: Repository permission checked; Result or follow-up: Check consent for the requested workspace
- [строка 9] Connector: Google Drive; Check: Approval; Account condition: Existing Drive access; Result or follow-up: Check consent for the requested workspace
- [строка 10] Connector: Jira Cloud; Check: Approval; Account condition: One-way link only; Result or follow-up: Check consent for the requested workspace
- [строка 11] Connector: Slack; Check: Private resource; Account condition: Workspace approved; Result or follow-up: No access granted by the posted link
- [строка 12] Connector: Microsoft Teams; Check: Private resource; Account condition: Tenant administrator available; Result or follow-up: No access granted by the posted link
- [строка 13] Connector: GitHub; Check: Private resource; Account condition: Repository permission checked; Result or follow-up: No access granted by the posted link
- [строка 14] Connector: Google Drive; Check: Private resource; Account condition: Existing Drive access; Result or follow-up: No access granted by the posted link
- [строка 15] Connector: Jira Cloud; Check: Private resource; Account condition: One-way link only; Result or follow-up: No access granted by the posted link
- [строка 16] Connector: Slack; Check: Scope change; Account condition: Workspace approved; Result or follow-up: Fresh consent required for new write scopes
- [строка 17] Connector: Microsoft Teams; Check: Scope change; Account condition: Tenant administrator available; Result or follow-up: Fresh consent required for new write scopes
- [строка 18] Connector: GitHub; Check: Scope change; Account condition: Repository permission checked; Result or follow-up: Fresh consent required for new write scopes
- [строка 19] Connector: Google Drive; Check: Scope change; Account condition: Existing Drive access; Result or follow-up: Fresh consent required for new write scopes
- [строка 20] Connector: Jira Cloud; Check: Scope change; Account condition: One-way link only; Result or follow-up: Fresh consent required for new write scopes
- [строка 21] Connector: Slack; Check: Link opening; Account condition: Workspace approved; Result or follow-up: Open with the recipient’s own permissions
- [строка 22] Connector: Microsoft Teams; Check: Link opening; Account condition: Tenant administrator available; Result or follow-up: Open with the recipient’s own permissions
- [строка 23] Connector: GitHub; Check: Link opening; Account condition: Repository permission checked; Result or follow-up: Open with the recipient’s own permissions
- [строка 24] Connector: Google Drive; Check: Link opening; Account condition: Existing Drive access; Result or follow-up: Open with the recipient’s own permissions
- [строка 25] Connector: Jira Cloud; Check: Link opening; Account condition: One-way link only; Result or follow-up: Open with the recipient’s own permissions
- [строка 26] Connector: Slack; Check: Retirement queue; Account condition: Workspace approved; Result or follow-up: Disable then revoke; drain queue for up to 15 minutes
- [строка 27] Connector: Microsoft Teams; Check: Retirement queue; Account condition: Tenant administrator available; Result or follow-up: Disable then revoke; drain queue for up to 15 minutes
- [строка 28] Connector: GitHub; Check: Retirement queue; Account condition: Repository permission checked; Result or follow-up: Disable then revoke; drain queue for up to 15 minutes
- [строка 29] Connector: Google Drive; Check: Retirement queue; Account condition: Existing Drive access; Result or follow-up: Disable then revoke; drain queue for up to 15 minutes
- [строка 30] Connector: Jira Cloud; Check: Retirement queue; Account condition: One-way link only; Result or follow-up: Disable then revoke; drain queue for up to 15 minutes
- [строка 31] Connector: Slack; Check: Vendor limit; Account condition: Workspace approved; Result or follow-up: Temporary vendor failures use retry handling
- [строка 32] Connector: Microsoft Teams; Check: Vendor limit; Account condition: Tenant administrator available; Result or follow-up: Temporary vendor failures use retry handling
- [строка 33] Connector: GitHub; Check: Vendor limit; Account condition: Repository permission checked; Result or follow-up: Temporary vendor failures use retry handling
- [строка 34] Connector: Google Drive; Check: Vendor limit; Account condition: Existing Drive access; Result or follow-up: Temporary vendor failures use retry handling
- [строка 35] Connector: Jira Cloud; Check: Vendor limit; Account condition: One-way link only; Result or follow-up: Temporary vendor failures use retry handling
