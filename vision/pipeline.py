"""Pipeline completo: detector + OCR + descricao."""

from io import BytesIO
from pathlib import Path
from typing import List

import numpy as np
from PIL import Image

from detector import ComponentDetector
from ocr import PanelOCR


class VisionPipeline:
    def __init__(self, model_path=None, confidence=0.5):
        self.detector = ComponentDetector(model_path, confidence)
        self.ocr = PanelOCR()

    def process(self, image_input: bytes | str | Path | Image.Image) -> dict:
        """Processa imagem e retorna resultado no formato VisionResponse."""
        if isinstance(image_input, bytes):
            image = Image.open(BytesIO(image_input))
        elif isinstance(image_input, (str, Path)):
            image = Image.open(image_input)
        else:
            image = image_input

        img_array = np.array(image)

        # 1. Detecta componentes
        detections = self.detector.detect(img_array)
        objects = list(dict.fromkeys([d["class"] for d in detections]))

        # 2. OCR nas regioes de interesse
        regions = self.detector.get_display_regions(detections)
        if regions:
            ocr_results = self.ocr.extract_regions(image, regions)
            ocr_text = " | ".join([r["text"] for r in ocr_results])
        else:
            ocr_text = self.ocr.extract(image)

        # 3. Gera descricao
        description = self._describe(objects, ocr_text)

        return {
            "objects": objects,
            "ocr_text": ocr_text,
            "description": description,
        }

    def _describe(self, objects: List[str], ocr_text: str) -> str:
        """Gera descricao contextual."""
        if not objects:
            return "Nenhum componente espacial detectado."

        parts = [f"Detectados: {', '.join(objects)}."]
        
        if ocr_text:
            parts.append(f"Texto do painel: '{ocr_text}'.")

        if "led_alerta" in objects or "ALERTA" in ocr_text.upper():
            parts.append("ALERTA VISUAL DETECTADO.")
        elif "botao_emergencia" in objects:
            parts.append("Botao de emergencia identificado.")

        return " ".join(parts)


# Funcao que o backend chama
def process_image(image_bytes: bytes, model_path: str | None = None) -> dict:
    pipeline = VisionPipeline(model_path=model_path)
    return pipeline.process(image_bytes)