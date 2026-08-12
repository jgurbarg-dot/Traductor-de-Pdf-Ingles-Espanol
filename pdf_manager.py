# pdf_manager.py
import os
import fitz  # PyMuPDF
from pypdf import PdfWriter
from translator_engine import PDFTranslatorEngine

def process_large_pdf(
    input_pdf_path: str,
    output_pdf_path: str,
    translator_engine: PDFTranslatorEngine,
    chunk_size: int = 15,
    progress_callback=None
):
    doc = fitz.open(input_pdf_path)
    total_doc_pages = len(doc)
    temp_dir = "temp_chunks"
    os.makedirs(temp_dir, exist_ok=True)

    chunk_files = []
    processed_count = 0

    for i in range(0, total_doc_pages, chunk_size):
        chunk_start = i
        chunk_end = min(i + chunk_size, total_doc_pages)

        chunk_doc = fitz.open()
        chunk_doc.insert_pdf(doc, from_page=chunk_start, to_page=chunk_end - 1)

        for page_idx in range(len(chunk_doc)):
            page = chunk_doc[page_idx]
            translator_engine.translate_page(page)
            processed_count += 1
            if progress_callback:
                progress = min(processed_count / total_doc_pages, 1.0)
                progress_callback(progress, processed_count, total_doc_pages)

        chunk_path = os.path.join(temp_dir, f"chunk_{chunk_start}_{chunk_end}.pdf")
        chunk_doc.save(chunk_path)
        chunk_doc.close()
        chunk_files.append(chunk_path)

    doc.close()

    merger = PdfWriter()
    for cf in chunk_files:
        merger.append(cf)

    merger.write(output_pdf_path)
    merger.close()

    for cf in chunk_files:
        if os.path.exists(cf):
            os.remove(cf)

    return output_pdf_path
