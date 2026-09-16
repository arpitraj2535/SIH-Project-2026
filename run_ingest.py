

from ingestor import create_collection, ingest_pdf


create_collection()


# PDFs and their verified Standard IDs
pdfs = [
    (
        "Standards/GrantofLicence-Guidelines-25Feb2026.pdf",
        "Grant of Licence Guidelines"
    ),
    (
        "Standards/Guidance-document-on-QCOs-Revised-1.pdf",
        "Guidance Document on QCOs"
    ),
    (
        "Standards/PM-IS-17526-1.pdf",
        "IS 17526:2021"
    ),
    (
        "Standards/PM-IS-17803-1.pdf",
        "IS 17803"
    ),
]


for path, standard_id in pdfs:
    ingest_pdf(path, standard_id)


print("\nIngestion complete.")
