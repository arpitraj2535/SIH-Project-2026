from ingestor import create_collection, ingest_pdf


# CREATE COLLECTION


create_collection()


# BIS KNOWLEDGE BASE — 20 PDFs


pdfs = [

    (
        "Standards/1660-PM-oct-2024.pdf",
        "1660-PM-oct-2024",
        "BIS Product Manual - IS 1660"
    ),

    (
        "Standards/2082-PM_V6_-approved.pdf",
        "2082-PM_V6_-approved",
        "BIS Product Manual - IS 2082"
    ),

    (
        "Standards/368-PM_10_July.pdf",
        "368-PM_10_July",
        "BIS Product Manual - IS 368"
    ),

    (
        "Standards/approved-IS-4250-PM.pdf",
        "approved-IS-4250-PM",
        "BIS Product Manual - IS 4250"
    ),

    (
        "Standards/compendium_2025-06-02-05-25-52.pdf",
        "compendium_2025-06-02-05-25-52",
        "BIS Compendium"
    ),

    (
        "Standards/GrantofLicence-Guidelines-25Feb2026.pdf",
        "GrantofLicence-Guidelines-25Feb2026",
        "Grant of Licence Guidelines"
    ),

    (
        "Standards/Group-2_23042026.pdf",
        "Group-2_23042026",
        "BIS Group 2 Document"
    ),

    (
        "Standards/Group_1_24062026.pdf",
        "Group_1_24062026",
        "BIS Group 1 Document"
    ),

    (
        "Standards/Guidance-document-on-QCOs-Revised-1.pdf",
        "Guidance-document-on-QCOs-Revised-1",
        "Guidance Document on QCOs"
    ),

    (
        "Standards/IS-2925-Product-Manual.pdf",
        "IS-2925-Product-Manual",
        "IS 2925 Product Manual"
    ),

    (
        "Standards/IS-4151-Product-Manual.pdf",
        "IS-4151-Product-Manual",
        "IS 4151 Product Manual"
    ),

    (
        "Standards/PM-IS-17526-1.pdf",
        "IS 17526:2021",
        "IS 17526:2021 Product Manual"
    ),

    (
        "Standards/PM-IS-17803-1.pdf",
        "IS 17803",
        "IS 17803 Product Manual"
    ),

    (
        "Standards/PM-IS-2347.pdf",
        "PM-IS-2347",
        "IS 2347 Product Manual"
    ),

    (
        "Standards/PM-IS-4984-June-2022.pdf",
        "PM-IS-4984-June-2022",
        "IS 4984 Product Manual"
    ),

    (
        "Standards/PM-IS-4985-Oct-2023.pdf",
        "PM-IS-4985-Oct-2023",
        "IS 4985 Product Manual"
    ),

    (
        "Standards/PM_IS-694_March-2024.pdf",
        "PM_IS-694_March-2024",
        "IS 694 Product Manual"
    ),

    (
        "Standards/PM_1293-new-format-approved.pdf",
        "PM_1293-new-format-approved",
        "IS 1293 Product Manual"
    ),

    (
        "Standards/PM_3854-approved.pdf",
        "PM_3854-approved",
        "IS 3854 Product Manual"
    ),

    (
        "Standards/Revised-Guidelines-for-JEWELLERS-Jan-24.pdf",
        "Revised-Guidelines-for-JEWELLERS-Jan-24",
        "Revised Guidelines for Jewellers"
    ),
]


# INGEST ALL DOCUMENTS


total_chunks = 0

for pdf_path, doc_id, doc_title in pdfs:

    count = ingest_pdf(
        pdf_path,
        doc_id,
        doc_title
    )

    total_chunks += count


# SUMMARY
print("\n========================================")
print("🎉 INGESTION COMPLETE")
print("========================================")
print(f"Total documents: {len(pdfs)}")
print(f"Total chunks: {total_chunks}")
print("Collection: bis_docs_voyage_final")
print("Database: Qdrant Cloud")
