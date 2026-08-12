# translator_engine.py
import fitz  # PyMuPDF
from deep_translator import GoogleTranslator

class PDFTranslatorEngine:
    def __init__(self, target_lang: str = "es"):
        self.translator = GoogleTranslator(source="en", target=target_lang)

    def translate_text_batch(self, text_list: list[str]) -> list[str]:
        if not text_list:
            return []
        
        translated_results = []
        for text in text_list:
            if not text.strip():
                translated_results.append("")
                continue
            try:
                # Traduce texto respetando el límite de caracteres por bloque
                res = self.translator.translate(text[:4500])
                translated_results.append(res if res else text)
            except Exception:
                # Si falla un bloque individual, devuelve el texto original para no romper el PDF
                translated_results.append(text)
        return translated_results

    def translate_page(self, page: fitz.Page) -> None:
        blocks = page.get_text("blocks")
        text_blocks = [b for b in blocks if b[6] == 0 and b[4].strip()]

        if not text_blocks:
            return

        original_texts = [b[4] for b in text_blocks]
        translated_texts = self.translate_text_batch(original_texts)

        for b in text_blocks:
            rect = fitz.Rect(b[0], b[1], b[2], b[3])
            page.add_redact_annot(rect, fill=(1, 1, 1))

        page.apply_redactions()

        for b, trans_text in zip(text_blocks, translated_texts):
            rect = fitz.Rect(b[0], b[1], b[2], b[3])
            line_count = max(1, trans_text.count('\n') + 1)
            block_height = rect.height
            fontsize = max(6.0, min(10.5, (block_height / line_count) * 0.75))

            try:
                page.insert_textbox(
                    rect,
                    trans_text,
                    fontsize=fontsize,
                    fontname="helv",
                    color=(0, 0, 0),
                    align=0
                )
            except Exception:
                page.insert_text(rect.tl, trans_text[:120], fontsize=7.0, fontname="helv")
