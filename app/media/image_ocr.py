"""
OCR de imagens. Extração local de texto com pytesseract, Pillow e opencv (opcional).
"""

import logging
import pytesseract

pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Users\Maikon\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"
)

from pathlib import Path

logger = logging.getLogger(__name__)


def extract_text_from_image(path: str) -> str:
    """
    Extrai texto da imagem via OCR (Tesseract).
    Usa Pillow para leitura e, se disponível, opencv para pré-processamento opcional.

    Args:
        path: Caminho absoluto do arquivo de imagem.

    Returns:
        Texto extraído ou string vazia em caso de falha. Nunca levanta exceção.
    """
    p = Path(path).resolve()
    if not p.exists():
        logger.warning("OCR: arquivo não encontrado %s", path)
        return ""

    try:
        import pytesseract
        from PIL import Image

        img = Image.open(p)
        img.load()
        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")

        try:
            import cv2
            import numpy as np

            arr = np.array(img)
            if len(arr.shape) == 3:
                gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
            else:
                gray = arr
            gray = cv2.medianBlur(gray, 3)
            _, gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            img = Image.fromarray(gray)
        except ImportError:
            pass

        text = pytesseract.image_to_string(img, lang="por+eng")
        return (text or "").strip()
    except Exception as e:
        logger.warning("OCR falhou para %s: %s", path, e)
        return ""
