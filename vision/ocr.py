"""
ocr.py — OCR de painéis e displays espaciais
=============================================
Extrai texto de imagens de painéis de controle usando Tesseract OCR.
"""
from __future__ import annotations
from pathlib import Path
from typing import Tuple
import cv2
import numpy as np
import pytesseract
from PIL import Image

class PanelOCR:
    def __init__(self, lang: str = "eng", psm: int = 6):
        """
        psm 6: Assume um bloco de texto uniforme. Ideal para displays de dados.
        """
        self.lang = lang
        self.psm = psm

        pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

    def preprocess(self, image: np.ndarray) -> np.ndarray:
        """ Pipeline de tratamento de imagem para melhorar a assertividade do OCR """
        # 1. Garante escala de cinza
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()

        # 2. Redimensiona para aumentar a nitidez dos caracteres pequenos (Upscaling)
        gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)

        # 3. Limpeza de ruído e binarização adaptativa (ótimo para displays LED/LCD)
        blurred = cv2.GaussianBlur(gray, (3, 3), 0)
        binary = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 11, 2
        )
        return binary

    def extract_text(self, image: Image.Image | np.ndarray, region: Tuple[int, int, int, int] | None = None) -> str:
        # Conversão para formato OpenCv (numpy array BGR)
        if isinstance(image, Image.Image):
            img = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        else:
            img = image.copy()

        # Armazena dimensões máximas para evitar estouro de Bounding Box
        h, w = img.shape[:2]

        # Se houver uma Bounding Box detectada pelo YOLO, faz o crop seguro na região do display
        if region is not None:
            try:
                x1, y1, x2, y2 = region
                # Garante que as coordenadas respeitem os limites da imagem física
                x1_safe = max(0, min(x1, w))
                y1_safe = max(0, min(y1, h))
                x2_safe = max(0, min(x2, w))
                y2_safe = max(0, min(y2, h))
                
                # Só faz o recorte se a área resultante for geometricamente válida
                if x2_safe > x1_safe and y2_safe > y1_safe:
                    img = img[y1_safe:y2_safe, x1_safe:x2_safe]
            except Exception:
                pass # Se falhar o cálculo, mantém a imagem cheia como fallback de segurança

        if img.size == 0:
            return ""

        processed = self.preprocess(img)

        # Configuração restritiva para evitar caracteres fantasmas e focar em dados técnicos
        custom_config = f"--psm {self.psm} -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz.:%° "
        
        try:
            text = pytesseract.image_to_string(processed, lang=self.lang, config=custom_config)
            return " ".join(text.strip().split())
        except Exception as e:
            print(f"[OCR] Erro ao processar Tesseract: {e}")
            return ""