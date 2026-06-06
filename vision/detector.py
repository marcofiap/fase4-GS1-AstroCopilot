"""Deteccao de componentes com YOLOv8."""

from pathlib import Path
from typing import List
import numpy as np
from PIL import Image
from ultralytics import YOLO


class ComponentDetector:
    def __init__(self, model_path: str | Path | None = None, confidence: float = 0.5):
        self.confidence = confidence
        # Garante o carregamento seguro do modelo customizado ou do base
        if model_path and Path(model_path).exists():
            self.model = YOLO(str(model_path))
        else:
            self.model = YOLO("yolov8n.pt")
            print("[Detector] Usando YOLOv8n pré-treinado (modo básico)")

    def detect(self, image) -> List[dict]:
        """Detecta componentes e retorna lista com classe, confianca e bbox."""
        # Proteção: se a imagem for nula ou inválida, retorna lista vazia imediatamente
        if image is None:
            return []

        try:
            results = self.model(image, conf=self.confidence, verbose=False)
        except Exception as e:
            print(f"[Detector] Erro interno na inferência do YOLO: {e}")
            return []

        detections = []
        for result in results:
            if result.boxes is None:
                continue
            for box in result.boxes:
                try:
                    cls_id = int(box.cls[0])
                    # Mantemos 'box' e 'bbox' para compatibilidade total com o pipeline
                    bbox_coords = [int(c) for c in box.xyxy[0].tolist()]
                    
                    detections.append({
                        "class": self._map_class(cls_id),
                        "confidence": round(float(box.conf[0]), 3),
                        "box": bbox_coords,   # Adicionado para redundância de segurança
                        "bbox": bbox_coords,  # Chave principal utilizada no pipeline
                    })
                except (IndexError, ValueError):
                    continue # Se uma caixinha vier corrompida, ignora e vai para a próxima
                    
        return detections

    def _map_class(self, coco_id: int) -> str:
        """Mapeia classes COCO para domínio espacial (MVP)."""
        mapping = {
            62: "painel_de_controle", # TV/Monitor no COCO
            63: "painel_de_controle", # Laptop no COCO
            64: "botao_emergencia",    # Mouse no COCO
            67: "display_numerico",   # Celular no COCO
        }
        return mapping.get(coco_id, f"objeto_{coco_id}")

    def get_display_regions(self, detections: List[dict]) -> List[tuple]:
        """Retorna bounding boxes de painéis/displays para OCR."""
        regions = []
        for d in detections:
            if not isinstance(d, dict):
                continue
            if d.get("class") in ("painel_de_controle", "display_numerico"):
                bbox = d.get("bbox")
                if bbox:
                    regions.append((d["class"], tuple(bbox)))
        return regions