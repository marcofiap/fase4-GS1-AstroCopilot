"""OCR de paineis com Tesseract."""

from pathlib import Path
from typing import List, Tuple

import cv2
import numpy as np
import pytesseract
from PIL import Image

# ✅ CAMINHO DO TESSERACT NO SEU PC
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


class PanelOCR:
    def __init__(self, lang: str = "eng", psm: int = 6):
        self.lang = lang
        self.psm = psm

    def preprocess(self, image: np.ndarray) -> np.ndarray:
        """Melhora contraste e binariza para OCR."""
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()

        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        binary = cv2.adaptiveThreshold(
            enhanced, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 11, 2
        )
        return cv2.medianBlur(binary, 3)

    def extract(self, image, region: Tuple[int, int, int, int] | None = None) -> str:
        """Extrai texto de imagem ou regiao especifica."""
        if isinstance(image, (str, Path)):
            img = cv2.imread(str(image))
        elif isinstance(image, Image.Image):
            img = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        else:
            img = image.copy()

        if region:
            x1, y1, x2, y2 = region
            img = img[y1:y2, x1:x2]

        processed = self.preprocess(img)
        config = f"--psm {self.psm} -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz .:%°µ/\\-"
        text = pytesseract.image_to_string(processed, lang=self.lang, config=config)
        return " ".join(text.split())

    # ✅ ADICIONAR ESTE MÉTODO:
    def extract_regions(self, image, regions: List[Tuple[str, Tuple]]) -> List[dict]:
        """Extrai texto de multiplas regioes."""
        results = []
        for name, bbox in regions:
            text = self.extract(image, region=bbox)
            if text:
                results.append({"region": name, "text": text})
        return results