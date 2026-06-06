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
from detector import ComponentDetector  # Certifique-se de que o detector.py está na mesma pasta
from ocr import PanelOCR

class VisionPipeline:
    def __init__(self, model_path: str | Path | None = None, confidence: float = 0.45):
        # Inicializa o detector customizado ou o modelo base
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

        img_array = np.array(image)

        # 1. Executa a detecção de objetos (YOLOv8)
        detections = self.detector.detect(img_array)
        objects = [d["class"] for d in detections]

        # 2. Determina a região de interesse (ROI) para rodar o OCR
        # Procura se algum objeto detectado se parece com um display ou painel técnico
        rois = self.detector.get_regions_of_interest(detections)
        
        if rois:
            # Executa o OCR especificamente na caixa delimitadora do display encontrado
            ocr_texts = []
            for _, bbox in rois:
                text = self.ocr.extract_text(image, region=bbox)
                if text:
                    ocr_texts.append(text)
            ocr_text = " | ".join(ocr_texts) if ocr_texts else ""
        else:
            # Fallback: Se o YOLO não achar um display específico, tenta ler a imagem inteira
            ocr_text = self.ocr.extract_text(image)

        # 3. Geração da descrição dinâmica baseada em regras de contexto de IA
        description = self._build_description(objects, ocr_text)

        return {
            "objects": objects,
            "ocr_text": ocr_text,
            "description": description
        }

    def _build_description(self, objects: List[str], ocr_text: str) -> str:
        if not objects and not ocr_text:
            return "Nenhum componente ou dado legível identificado na captura da câmera."

        unique_objs = list(set(objects))
        desc = f"Análise concluída. Componentes identificados na cabine: {', '.join(unique_objs) if unique_objs else 'Nenhum'}. "
        
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
# ── Teste standalone (Adicione isso no final do pipeline.py) ──────────────────
# ── Teste standalone corrigido ──────────────────────────────────────────────
if __name__ == "__main__":
    print("\n[Teste] Iniciando simulação do Pipeline de Visão...")
    
    try:
        # Passamos a string de bytes mockada direto aqui dentro para evitar o NameError
        resultado = process_image(b"pixels_de_mentira_para_teste")
        
        print("\n==================================================")
        print("     RESULTADO DO PIPELINE DE VISÃO (TESTE)")
        print("==================================================")
        print(f"Objetos detectados: {resultado['objects']}")
        print(f"Texto do OCR:       {resultado['ocr_text']}")
        print(f"Descrição da IA:    {resultado['description']}")
        print("==================================================\n")
        
    except Exception as e:
        print(f"\n[Erro no Teste]: Ocorreu uma falha ao rodar o pipeline: {e}")