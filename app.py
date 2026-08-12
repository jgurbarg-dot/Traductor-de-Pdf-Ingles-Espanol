# app.py
import streamlit as st
import os
import fitz
from config import APP_TITLE, APP_SUBTITLE, DEFAULT_CHUNK_SIZE
from translator_engine import PDFTranslatorEngine
from pdf_manager import process_large_pdf

st.set_page_config(page_title="Traductor PDF Gratis", page_icon="🧪", layout="wide")

st.title(f"🧪 {APP_TITLE}")
st.write(APP_SUBTITLE)

st.sidebar.header("⚙️ Configuración")
chunk_size = st.sidebar.slider("Páginas por lote", 5, 30, DEFAULT_CHUNK_SIZE)
st.sidebar.info("Esta aplicación es 100% gratuita y no requiere ninguna API Key.")

uploaded_file = st.file_uploader("📂 Sube tu archivo PDF en Inglés", type=["pdf"])

if uploaded_file is not None:
    os.makedirs("uploads", exist_ok=True)
    temp_input = os.path.join("uploads", uploaded_file.name)
    with open(temp_input, "wb") as f:
        f.write(uploaded_file.getbuffer())

    doc = fitz.open(temp_input)
    total_pages = len(doc)
    doc.close()

    st.info(f"El documento tiene **{total_pages} páginas**.")

    if st.button("🚀 Iniciar Traducción Gratuita", type="primary"):
        progress_bar = st.progress(0.0)
        status_text = st.empty()

        def update_progress(progress, current_p, total_p):
            progress_bar.progress(progress)
            status_text.markdown(f"**Procesando página {current_p} de {total_p}...**")

        try:
            engine = PDFTranslatorEngine()
            output_filename = f"Traducido_{uploaded_file.name}"
            os.makedirs("outputs", exist_ok=True)
            output_pdf = os.path.join("outputs", output_filename)

            process_large_pdf(
                input_pdf_path=temp_input,
                output_pdf_path=output_pdf,
                translator_engine=engine,
                chunk_size=chunk_size,
                progress_callback=update_progress
            )

            st.success("🎉 ¡Traducción completada con éxito y sin costo!")

            with open(output_pdf, "rb") as pdf_file:
                st.download_button(
                    label="📥 Descargar PDF en Español",
                    data=pdf_file,
                    file_name=output_filename,
                    mime="application/pdf",
                    type="primary"
                )
        except Exception as e:
            st.error(f"Ocurrió un error durante el proceso: {str(e)}")
