"""Deteccao de componentes com YOLOv8."""

from pathlib import Path
from typing import List

import numpy as np
from PIL import Image
from ultralytics import YOLO


class ComponentDetector:
    def __init__(self, model_path: str | Path | None = None, confidence: float = 0.5):
        self.confidence = confidence
        if model_path and Path(model_path).exists():
            self.model = YOLO(str(model_path))
        else:
            self.model = YOLO("yolov8n.pt")
            print("[Detector] Usando YOLOv8n pre-treinado (modo basico)")

    def detect(self, image) -> List[dict]:
        """Detecta componentes e retorna lista com classe, confianca e bbox."""
        results = self.model(image, conf=self.confidence, verbose=False)
        detections = []
        for result in results:
            if result.boxes is None:
                continue
            for box in result.boxes:
                cls_id = int(box.cls[0])
                detections.append({
                    "class": self._map_class(cls_id),
                    "confidence": round(float(box.conf[0]), 3),
                    "bbox": [int(c) for c in box.xyxy[0].tolist()],
                })
        return detections

    def _map_class(self, coco_id: int) -> str:
        """Mapeia classes COCO para dominio espacial (MVP)."""
        mapping = {
            62: "painel_de_controle",
            63: "painel_de_controle",
            64: "botao_emergencia",
            67: "display_numerico",
        }
        return mapping.get(coco_id, f"objeto_{coco_id}")

    def get_display_regions(self, detections: List[dict]) -> List[tuple]:
        """Retorna bounding boxes de paineis/displays para OCR."""
        regions = []
        for d in detections:
            if d["class"] in ("painel_de_controle", "display_numerico"):
                regions.append((d["class"], tuple(d["bbox"])))
        return regions