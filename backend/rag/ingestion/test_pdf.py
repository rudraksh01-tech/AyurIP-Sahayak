from pathlib import Path
from pypdf import PdfReader


# PDF file  location
PDF_PATH = Path("backend/data/raw/ayurveda.pdf.pdf")


def read_pdf(pdf_path):
    # PDF ko read karna
    reader = PdfReader(pdf_path)

    # Total pages print karna
    print(f"Total pages: {len(reader.pages)}")

    # Har page ka text read karna
    for page_number, page in enumerate(reader.pages, start=1):

        text = page.extract_text() or ""

        print(f"\n--- Page {page_number} ---")

        # Har page ke maximum 1000 characters print karenge
        print(text[:1000])


if __name__ == "__main__":
    read_pdf(PDF_PATH)