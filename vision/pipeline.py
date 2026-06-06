"""
pipeline.py — Orquestrador de Visão Computacional
===================================================
Recebe os bytes do arquivo, roda a detecção e o OCR, devolvendo o contrato exato.
"""
from __future__ import annotations
import io
from pathlib import Path
from typing import List
import numpy as np
from PIL import Image
from detector import ComponentDetector  # Classe do grupo
from ocr import PanelOCR

class VisionPipeline:
    def __init__(self, model_path: str | Path | None = None, confidence: float = 0.45):
        self.detector = ComponentDetector(model_path=model_path, confidence=confidence)
        self.ocr = PanelOCR()

    def process(self, image_bytes: bytes) -> dict:
        """
        Processa os bytes vindos do UploadFile da rota FastAPI.
        """
        try:
            # Converte bytes brutos em uma imagem PIL de forma segura
            image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        except Exception as e:
            return {
                "objects": [],
                "ocr_text": "",
                "description": f"Erro crítico ao ler o arquivo de imagem: {e}"
            }

        # Converte para array numpy apenas para o detector YOLO
        img_array = np.array(image)

        # 1. Executa a detecção de objetos (YOLOv8)
        try:
            detections = self.detector.detect(img_array)
            # Garante que 'detections' seja uma lista válida, mesmo se vier nula
            if not detections:
                detections = []
        except Exception:
            detections = []

        # Extrai as classes detectadas de forma segura
        objects = [d.get("class", "desconhecido") for d in detections if isinstance(d, dict) and "class" in d]

        # 2. Determina a região de interesse (ROI) para rodar o OCR de forma segura
        ocr_texts = []
        
        for det in detections:
            if not isinstance(det, dict):
                continue
                
            bbox = det.get("box") or det.get("bbox")
            
            # Se encontrar coordenadas válidas da caixa, faz o recorte para o OCR
            if bbox and len(bbox) == 4:
                try:
                    bbox_int = (int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3]))
                    text = self.ocr.extract_text(image, region=bbox_int)
                    if text and text.strip():
                        ocr_texts.append(text.strip())
                except Exception:
                    continue  # Se falhar o OCR de uma caixa, pula para a próxima

        # Fallback Estratégico: Se não achou caixas ou o OCR das ROIs veio vazio, lê a imagem cheia
        if ocr_texts:
            ocr_text = " | ".join(ocr_texts)
        else:
            try:
                ocr_text = self.ocr.extract_text(image)
            except Exception:
                ocr_text = ""

        # 3. Geração da descrição dinâmica baseada em regras de contexto de IA
        description = self._build_description(objects, ocr_text)

        return {
            "objects": objects,
            "ocr_text": ocr_text,
            "description": description
        }

    def _build_description(self, objects: List[str], ocr_text: str) -> str:
        # Se o YOLO não achar nada e o OCR vier totalmente vazio
        if not objects and not ocr_text:
            return "Nenhum componente ou dado legível identificado na captura da câmera."

        unique_objs = list(set(objects))
        desc = "Análise concluída. "
        
        if unique_objs:
            desc += f"Componentes identificados na cabine: {', '.join(unique_objs)}. "
        else:
            desc += "Nenhum componente mapeado foi detectado por aproximação visual. "
        
        if ocr_text:
            desc += f"Dados coletados via telemetria visual: '{ocr_text}'."
        
        # Identificação inteligente de anomalias visuais (Stretch goal do trabalho)
        if "led_alerta" in objects or "ALERTA" in ocr_text.upper() or "WARN" in ocr_text.upper():
            desc += " ⚠️ ATENÇÃO: Indicador de anomalia visual ou mensagem crítica ativa no painel!"
            
        return desc

# Função global que o backend invoca diretamente
def process_image(image_bytes: bytes, model_path: str | None = None) -> dict:
    pipeline = VisionPipeline(model_path=model_path)
    return pipeline.process(image_bytes)

# ── Teste standalone com imagem real ──────────────────────────────────────────
if __name__ == "__main__":
    print("\n[Teste] Iniciando simulação do Pipeline de Visão com imagem real...")
    
    # 1. Coloque o caminho de uma imagem que exista no seu computador
    caminho_imagem = "test_images/teste.jpg" 
    
    try:
        # 2. Abre e lê a imagem em formato de bytes
        with open(caminho_imagem, "rb") as f:
            imagem_bytes = f.read()
            
        resultado = process_image(imagem_bytes)
        
        print("\n==================================================")
        print("     RESULTADO DO PIPELINE DE VISÃO (TESTE REAL)")
        print("==================================================")
        print(f"Objetos detectados: {resultado['objects']}")
        print(f"Texto do OCR:       {resultado['ocr_text']}")
        print(f"Descrição da IA:    {resultado['description']}")
        print("==================================================\n")
        
    except FileNotFoundError:
        print(f"\n[Erro]: Não encontrei o arquivo no caminho: {caminho_imagem}")
        print("Por favor, coloque uma imagem válida lá ou ajuste o caminho do teste.")
    except Exception as e:
        print(f"\n[Erro no Teste]: Ocorreu uma falha: {e}")