from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.modelo import PipelineAlimentoSeguro


app = FastAPI(
    title="Rede Alimenta IA",
    description="API para previsão de prioridade de lotes de alimentos.",
    version="1.0.0"
)


# Inicializa o modelo
modelo = PipelineAlimentoSeguro(
    "data/Consolidated_Supermarket_Data.csv"
)

modelo.treinar_modelo_com_dados_reais()


class LoteInput(BaseModel):
    qtd_kilo: float = Field(gt=0, le=10000)
    preco_atacado: float = Field(gt=0, le=1000)
    taxa_perda: float = Field(ge=0, le=100)


@app.get("/")
def inicio():
    return {
        "projeto": "Rede Alimenta IA",
        "status": "API funcionando"
    }


@app.post("/prever")
def prever(lote: LoteInput):
    resultado = modelo.prever_prioridade_lote(
        lote.qtd_kilo,
        lote.preco_atacado,
        lote.taxa_perda
    )

    if "erro" in resultado:
        raise HTTPException(
            status_code=400,
            detail=resultado["erro"]
        )

    return resultado