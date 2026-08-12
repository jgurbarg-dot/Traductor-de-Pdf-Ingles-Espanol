# translator_engine.py
import fitz  # PyMuPDF
from openai import OpenAI
from config import SYSTEM_PROMPT_CHEMENG

class PDFTranslatorEngine:
    def __init__(self, api_key: str, model_name: str = "gpt-4o-mini"):
        self.client = OpenAI(api_key=api_key)
        self.model = model_name

    def translate_text_batch(self, text_list: list[str]) -> list[str]:
        if not text_list:
            return []

        delimiter = "\n---BLOCK_DELIMITER---\n"
        joined_text = delimiter.join(text_list)

        user_prompt = (
            "Traduce los siguientes bloques de texto pertenecientes a un libro/documento de ingeniería química. "
            "Respeta el delimitador '---BLOCK_DELIMITER---' exactamente entre cada bloque traducido.\n\n"
            f"TEXTO A TRADUCIR:\n{joined_text}"
        )

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                temperature=0.2,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT_CHEMENG},
                    {"role": "user", "content": user_prompt}
                ]
            )

            translated_raw = response.choices[0].message.content
            translated_blocks = translated_raw.split("---BLOCK_DELIMITER---")
            translated_blocks = [b.strip() for b in translated_blocks]
            
            if len(translated_blocks) != len(text_list):
                return self._translate_individual_fallback(text_list)

            return translated_blocks
        except Exception as e:
            return self._translate_individual_fallback(text_list)

    def _translate_individual_fallback(self, text_list: list[str]) -> list[str]:
        results = []
        for text in text_list:
            if not text.strip():
                results.append("")
                continue
            try:
                res = self.client.chat.completions.create(
                    model=self.model,
                    temperature=0.2,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT_CHEMENG},
                        {"role": "user", "content": f"Traduce este texto al español manteniendo unidades y formato:\n{text}"}
                    ]
                )
                results.append(res.choices[0].message.content.strip())
            except Exception:
                results.append(text)
        return results

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
