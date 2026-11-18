---
source_path: "documents/Рабочие копии/Downloads/Export security final.pdf"
format: "pdf"
source_sha256: "fe510a9819443c2c597b87c00d9cd893431b018eb6418596782173a1dc4ba0e0"
extractor: "extract-1"
---
<!-- page 1 -->

# Administrative export security checks

This copy was downloaded for the September operations review. Data Portability confirmed the export behaviour described here on 1 September 2026. The operations meeting focused on failed large exports and questions about the delivery channel. Use this reference when an administrator asks Support to help prepare an administrative export of LumenDesk cards.

An export can bring together material that is normally separated by spaces and access controls. A technical ability to create an archive does not establish that the requested recipient is entitled to receive it. Identify the workspace, the administrator requesting the work and the requested date or space boundaries before starting. Keep the request in the authenticated channel so the approval and the delivery remain connected.

## Preparation

Only the workspace owner or an administrator may start an administrative export.

Choose spaces and dates that match the approved request.

A Team CSV export job contains at most 100000 data rows.

A workspace may run at most 2 export jobs concurrently.

## Delivery

A download link expires 24 hours after archive creation.

Send the link through the authenticated request channel.

Do not upload an export archive into an ordinary support ticket.

Record job ID, approving administrator and creation time in UTC.

If a job exceeds its limit, narrow the date filter before retrying.

## Scoping before generation

Ask what business purpose the archive serves and which spaces and dates are required. A customer may say everything when only one project is under review. Clarify the actual scope with the authorised administrator rather than assuming the widest export is safest. Record the chosen filter in the request. If a colleague must reproduce the export later, the colleague should be able to understand the selection without needing access to the contents of the resulting archive.

For Team, the current limit is 100000 data rows per export job; the header row is not a data row. Splitting a completed file after downloading it does not increase the permitted size of the job that produced it. Where a selection is too large, narrow the date range or create separate appropriately scoped jobs. At most two export jobs may run concurrently for the workspace. Check the queue before interpreting a waiting job as a failure.

<!-- page 2 -->

## Handling the delivered archive

Deliver the download link through the same authenticated request channel. Explain that it expires 24 hours after archive creation. The expiry concerns the link issued by LumenDesk, and is not a statement about any copy already downloaded by the customer's administrator. Do not attach the export archive to an ordinary support ticket merely to make it easier for a colleague to inspect it. Use job identifiers and selected filters when diagnosing generation issues.

An administrator who forwards a link to another person remains responsible for choosing an appropriate recipient. Support should not broaden a link's intended distribution by copying it into unrelated conversations or meeting notes. If the original contact changes during a handover, verify the new contact through the account process before resending anything. A message that quotes a workspace name is context, not proof of administrator authority.

## Notes from the operations review

In the first review example, an agent tried a full-year selection, saw a limit error, and retried the same selection several times. The useful next step was to compare the intended scope with the row allowance and split by dates. The retries did not change the number of selected rows. The request history should show why the filter changed so the customer can check that the separate jobs together cover the intended period without overlap or gaps.

In the second example, the archive had finished but the customer returned after the link lifetime had passed. The team verified the requester and the need before generating a replacement. They did not restore a stale link by copying an old archive into the ticket. The audit note recorded the new job, approving administrator and UTC creation time. These details make it possible to distinguish a delivery problem from a generation problem when the customer follows up.

Before closing, confirm that the administrator can use the delivered result and understands the selected scope. Keep evidence small: job identifier, request identifier, timestamps and the exact non-sensitive error text are usually more useful than screenshots of exported rows. A credit or privacy request discovered during this conversation should follow its own review process; exporting data does not settle either question. Send unclear permissions or disclosure concerns to the appropriate account owner before delivery.
