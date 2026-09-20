from ingestor import create_collection, ingest_pdf


# CREATE COLLECTION


create_collection()


# BIS KNOWLEDGE BASE — 20 PDFs


pdfs = [

    (
        "Standards/1660-PM-oct-2024.pdf",
        "1660-PM-oct-2024",
        "BIS Product Manual - IS 1660",
        "https://www.bis.gov.in/wp-content/uploads/2024/10/1660-PM-oct-2024.pdf"
    ),

    (
        "Standards/2082-PM_V6_-approved.pdf",
        "2082-PM_V6_-approved",
        "BIS Product Manual - IS 2082",
        "https://www.bis.gov.in/wp-content/uploads/2024/09/2082-PM_V6_-approved.pdf"
    ),

    (
        "Standards/368-PM_10_July.pdf",
        "368-PM_10_July",
        "BIS Product Manual - IS 368",
        "https://www.bis.gov.in/wp-content/uploads/2024/07/368-PM_10_July.pdf"
    ),

    (
        "Standards/approved-IS-4250-PM.pdf",
        "approved-IS-4250-PM",
        "BIS Product Manual - IS 4250",
        "https://www.bis.gov.in/wp-content/uploads/2020/07/Product-Manual-4250-V3.pdf"
    ),

    (
        "Standards/compendium_2025-06-02-05-25-52.pdf",
        "compendium_2025-06-02-05-25-52",
        "BIS Compendium",
        "https://services.bis.gov.in/tmp/compendium_2025-06-02-05-25-52.pdf"
    ),

    (
        "Standards/GrantofLicence-Guidelines-25Feb2026.pdf",
        "GrantofLicence-Guidelines-25Feb2026",
        "Grant of Licence Guidelines",
        "https://www.bis.gov.in/wp-content/uploads/2026/02/GrantofLicence-Guidelines-25Feb2026.pdf"
    ),

    (
        "Standards/Group-2_23042026.pdf",
        "Group-2_23042026",
        "BIS Group 2 Document",
        "https://www.bis.gov.in/wp-content/uploads/2026/04/Group-2_23042026.pdf"
    ),

    (
        "Standards/Group_1_24062026.pdf",
        "Group_1_24062026",
        "BIS Group 1 Document",
        "https://www.bis.gov.in/wp-content/uploads/2026/06/Group_1_24062026.pdf"
    ),

    (
        "Standards/Guidance-document-on-QCOs-Revised-1.pdf",
        "Guidance-document-on-QCOs-Revised-1",
        "Guidance Document on QCOs",
        "https://www.bis.gov.in/wp-content/uploads/2021/07/Guidance-document-on-QCOs-Revised-1.pdf"
    ),

    (
        "Standards/IS-2925-Product-Manual.pdf",
        "IS-2925-Product-Manual",
        "IS 2925 Product Manual",
        "https://www.bis.gov.in/wp-content/uploads/IS-2925-Product-Manual.pdf"
    ),

    (
        "Standards/IS-4151-Product-Manual.pdf",
        "IS-4151-Product-Manual",
        "IS 4151 Product Manual",
        "https://www.bis.gov.in/wp-content/uploads/2024/12/PM_IS_4151_-Dec-24.pdf"
    ),

    (
        "Standards/PM-IS-17526-1.pdf",
        "IS 17526:2021",
        "IS 17526:2021 Product Manual",
        "https://www.bis.gov.in/wp-content/uploads/2024/12/PM-IS-17526-1.pdf"
    ),

    (
        "Standards/PM-IS-17803-1.pdf",
        "IS 17803",
        "IS 17803 Product Manual",
        "https://www.bis.gov.in/wp-content/uploads/2025/06/PM-IS-17803.pdf"
    ),

    (
        "Standards/PM-IS-2347.pdf",
        "PM-IS-2347",
        "IS 2347 Product Manual",
        "https://www.bis.gov.in/wp-content/uploads/2025/02/PM-IS-2347.pdf"
    ),

    (
        "Standards/PM-IS-4984-June-2022.pdf",
        "PM-IS-4984-June-2022",
        "IS 4984 Product Manual",
        "https://www.bis.gov.in/wp-content/uploads/2022/06/PM-IS-4984-June-2022.pdf"
    ),

    (
        "Standards/PM-IS-4985-Oct-2023.pdf",
        "PM-IS-4985-Oct-2023",
        "IS 4985 Product Manual",
        "https://www.bis.gov.in/wp-content/uploads/2023/10/PM-IS-4985-Oct-2023.pdf"
    ),

    (
        "Standards/PM_IS-694_March-2024.pdf",
        "PM_IS-694_March-2024",
        "IS 694 Product Manual",
        "https://www.bis.gov.in/wp-content/uploads/2024/03/PM_IS-694_March-2024.pdf"
    ),

    (
        "Standards/PM_1293-new-format-approved.pdf",
        "PM_1293-new-format-approved",
        "IS 1293 Product Manual",
        "https://www.bis.gov.in/wp-content/uploads/2024/05/PM_1293-new-format-approved.pdf"
    ),

    (
        "Standards/PM_3854-approved.pdf",
        "PM_3854-approved",
        "IS 3854 Product Manual",
        "https://www.bis.gov.in/wp-content/uploads/2024/01/PM_3854-approved.pdf"
    ),

    (
        "Standards/Revised-Guidelines-for-JEWELLERS-Jan-24.pdf",
        "Revised-Guidelines-for-JEWELLERS-Jan-24",
        "Revised Guidelines for Jewellers",
        "https://www.bis.gov.in/wp-content/uploads/2024/01/Revised-Guidelines-for-JEWELLERS-Jan-24.pdf"
    ),
]


# INGEST ALL DOCUMENTS


total_chunks = 0

for pdf_path, doc_id, doc_title, source_url in pdfs:

    count = ingest_pdf(
        pdf_path,
        doc_id,
        doc_title,
        source_url
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
