from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.modelo import PipelineAlimentoSeguro

import hmac
import os

from fastapi import Header
from dotenv import load_dotenv

load_dotenv()

from app.database import get_connection

app = FastAPI(
    title="Rede Alimenta IA",
    description="API para previsão de prioridade de lotes de alimentos.",
    version="1.0.0"
)

def verificar_token(x_api_key: str = Header(default="")):
    token_configurado = os.getenv("API_ACCESS_TOKEN")

    if not token_configurado:
        raise HTTPException(
            status_code=500,
            detail="Chave de acesso não configurada."
        )

    if not hmac.compare_digest(x_api_key, token_configurado):
        raise HTTPException(
            status_code=401,
            detail="Chave de acesso inválida."
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


@app.get("/health")
def health():
    return {"status": "ok"}



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

@app.get("/doacoes")
def listar_doacoes(
    x_api_key: str = Header(default="")
):
    verificar_token(x_api_key)

    try:
        with get_connection() as conn:
            linhas = conn.execute(
                """
                SELECT
                    id,
                    alimento,
                    quantidade_kg,
                    data_validade,
                    nome_doador,
                    status,
                    created_at
                FROM public.doacoes
                ORDER BY created_at DESC
                LIMIT 100
                """
            ).fetchall()

        return [
            {
                "id": linha[0],
                "alimento": linha[1],
                "quantidade_kg": float(linha[2]),
                "data_validade": (
                    linha[3].isoformat() if linha[3] else None
                ),
                "nome_doador": linha[4],
                "status": linha[5],
                "created_at": linha[6].isoformat(),
            }
            for linha in linhas
        ]

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Não foi possível consultar as doações."
        )