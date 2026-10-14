
from datetime import date
import hmac
import os

from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field, model_validator

from app.database import get_connection
from app.modelo import PipelineAlimentoSeguro

load_dotenv()

app = FastAPI(
    title="Rede Alimenta IA",
    description="API para previsão de prioridade de lotes de alimentos.",
    version="1.0.0"
)


# Verifica a chave de acesso da API
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


# Inicializa e treina o modelo de IA
modelo = PipelineAlimentoSeguro(
    "data/Consolidated_Supermarket_Data.csv"
)

modelo.treinar_modelo_com_dados_reais()


# Dados de entrada para previsão
class LoteInput(BaseModel):
    qtd_kilo: float = Field(gt=0, le=10000)
    preco_atacado: float = Field(gt=0, le=1000)
    taxa_perda: float = Field(ge=0, le=100)


# Dados de entrada para cadastro de doações
class DoacaoInput(BaseModel):
    alimento: str = Field(min_length=1, max_length=200)
    quantidade_kg: float = Field(gt=0, le=100000)
    data_validade: date | None = None
    nome_doador: str | None = Field(default=None, max_length=200)

    @model_validator(mode="after")
    def validar_textos(self):
        if not self.alimento.strip():
            raise ValueError("O nome do alimento não pode ficar vazio.")

        if self.nome_doador is not None:
            self.nome_doador = self.nome_doador.strip() or None

        return self


# Rota inicial
@app.get("/")
def inicio():
    return {
        "projeto": "Rede Alimenta IA",
        "status": "API funcionando"
    }


# Rota de verificação de saúde do serviço no Render
@app.get("/health")
def health():
    return {"status": "ok"}


# Previsão de prioridade de lotes
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


# Lista as últimas 100 doações
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


# Cadastra uma nova doação no Supabase
@app.post("/doacoes", status_code=201)
def cadastrar_doacao(
    doacao: DoacaoInput,
    x_api_key: str = Header(default="")
):
    verificar_token(x_api_key)

    try:
        with get_connection() as conn:
            linha = conn.execute(
                """
                INSERT INTO public.doacoes (
                    alimento,
                    quantidade_kg,
                    data_validade,
                    nome_doador
                )
                VALUES (%s, %s, %s, %s)
                RETURNING
                    id,
                    alimento,
                    quantidade_kg,
                    data_validade,
                    nome_doador,
                    status,
                    created_at
                """,
                (
                    doacao.alimento.strip(),
                    doacao.quantidade_kg,
                    doacao.data_validade,
                    doacao.nome_doador,
                ),
            ).fetchone()

        return {
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

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Não foi possível cadastrar a doação."
        )
                                