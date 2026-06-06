# ml-edge/ — Classificador de risco do tripulante (Edge ML)

Modelo **RandomForest** (scikit-learn) que classifica o estado de um tripulante
em `normal` / `fadiga` / `risco` a partir dos sinais vitais. Substitui as regras
placeholder de `classify_risk()` no backend ([`backend/main.py:96`](../../backend/main.py)).

## Arquivos
| Arquivo | Descrição |
|---------|-----------|
| `train_model.py` | Gera o dataset sintético, treina o modelo e salva tudo |
| `model.pkl` | Bundle joblib: `{model, features, labels, sklearn_version}` |
| `metrics.txt` | Relatório de métricas (citar no PDF) |
| `confusion_matrix.png` | Matriz de confusão (figura para o PDF) |
| `requirements.txt` | Dependências do treino |

## Contrato (features e rótulos)

**Features** — ordem fixa do vetor de entrada (a mesma que o backend monta):

| # | Feature | Unidade | Faixa física |
|---|---------|---------|--------------|
| 0 | `hr` | bpm | 40–200 |
| 1 | `spo2` | % | 70–100 |
| 2 | `temp` | °C | 34–42 |
| 3 | `radiation` | µSv/h | 0–25 |
| 4 | `resp` | rpm | 3–45 |

**Rótulos** (severidade crescente): `normal` → `fadiga` → `risco`.

**Política de risco** (limiares que definem os rótulos, espelhados de `classify_risk`):
- **risco** se `spo2<90` ou `hr>140` ou `temp>38.5` ou `radiation>5.0` ou `resp>28`
- **fadiga** se `spo2<94` ou `hr>110` ou `temp>37.8` ou `radiation>1.0` ou `resp>24` ou `resp<8`
- caso contrário **normal** (risco tem prioridade sobre fadiga)

## Abordagem: dataset sintético (e por que não é "if/else disfarçado")

Não existe dataset real adequado: os rótulos são política **desta** missão,
`radiation` é específico do espaço e dado de astronauta é restrito. Então geramos
dados sintéticos — mas **bem-feitos**, de forma que o modelo agregue valor real:

1. **Físico-plausível e correlacionado** — uma variável latente de "estresse"
   puxa HR/respiração/temperatura para cima e SpO₂ para baixo juntas; a radiação
   é ambiental (fundo baixo + picos de tempestade solar), quase independente.
2. **Cobertura de cantos** — 30% das amostras são uniformes em toda a faixa, para
   cobrir combinações raras (ex.: bradipneia `resp<8`, pico isolado de radiação).
3. **Ruído de sensor** — o rótulo é definido sobre o estado **verdadeiro**, mas o
   modelo treina sobre uma leitura **com ruído**. Resultado: ele aprende uma
   **fronteira difusa** e tolera ruído de medição — ganho concreto sobre o
   threshold rígido, que erra feio a um décimo do limiar.

## Como rodar
```bash
pip install -r requirements.txt
python train_model.py          # gera model.pkl + metrics.txt + PNG
```
Reprodutível (seed fixa `42`) — roda do zero e produz sempre o mesmo modelo.

> O `model.pkl` **não é versionado** (`.gitignore`: `*.pkl`). Gere-o com
> `python train_model.py` antes de subir o backend com ML. Sem ele, o backend
> cai nas regras determinísticas (fallback). Os artefatos `metrics.txt` e os
> `*.png` **são** versionados (para o PDF).

## Resultados (seed 42, 10.000 amostras)
- **Acurácia (teste): 94.4%**
- Erros concentrados **apenas em fronteiras adjacentes** (normal↔fadiga,
  fadiga↔risco); **zero** confusão normal↔risco — nenhum erro perigoso.
- Importância das features: `spo2` 0.34 · `radiation` 0.21 · `hr` 0.18 ·
  `temp` 0.18 · `resp` 0.09. Coerente: SpO₂ é o sinal mais decisivo.

Números completos e matriz de confusão em [`metrics.txt`](metrics.txt).

## Integração no backend
Carregar uma vez no startup e predizer respeitando a ordem das features:
```python
import joblib, numpy as np
_bundle = joblib.load("iot-esp32/ml-edge/model.pkl")
_model, _feats = _bundle["model"], _bundle["features"]  # ['hr','spo2','temp','radiation','resp']

def classify_risk(hr, spo2, temp, radiation=0.0, resp=14.0):
    x = np.array([[hr, spo2, temp, radiation, resp]])   # MESMA ordem de _feats
    return str(_model.predict(x)[0])
    # fallback para a regra antiga se model.pkl não existir
```

> **Pinar versão**: o `model.pkl` exige a **mesma** `scikit-learn` (1.6.*) no
> backend que o usado no treino. Manter `scikit-learn==1.6.*` em ambos os
> `requirements.txt`, senão o `joblib.load` pode falhar ou avisar.
