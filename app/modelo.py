import math
import os
from typing import Dict, Union

import pandas as pd
from sklearn.ensemble import RandomForestRegressor


class PipelineAlimentoSeguro:
    """
    Modelo de IA do projeto Rede Alimenta IA.

    Responsabilidades:
    - validar o caminho do dataset;
    - carregar somente as colunas necessárias;
    - limitar a quantidade de dados usados no treinamento;
    - tratar valores ausentes;
    - treinar o Random Forest;
    - validar os dados recebidos para previsão;
    - calcular a pontuação de urgência do lote.
    """

    COLUNAS_MODELO = [
        "Quantity Sold (kilo)",
        "Wholesale Price (RMB/kg)",
        "Loss Rate (%)",
    ]

    COLUNAS_OBRIGATORIAS = [
        "Quantity Sold (kilo)",
        "Unit Selling Price (RMB/kg)",
        "Wholesale Price (RMB/kg)",
        "Loss Rate (%)",
    ]

    # Limite inicial para reduzir o consumo de memória no Render.
    MAX_LINHAS_TREINAMENTO = 30000

    def __init__(self, caminho_csv: str):
        if not caminho_csv.endswith(".csv") or ".." in caminho_csv:
            raise ValueError(
                "Erro de segurança: caminho de arquivo inválido."
            )

        self.caminho_csv = caminho_csv

        self.model = RandomForestRegressor(
            n_estimators=20,
            random_state=42,
            n_jobs=1,
            max_depth=12,
            min_samples_leaf=2,
        )

        self._is_trained = False

    def carregar_e_validar_dados(self) -> pd.DataFrame:
        """Carrega uma amostra do CSV e valida sua estrutura."""

        if not os.path.exists(self.caminho_csv):
            raise FileNotFoundError(
                "O arquivo de dados não foi encontrado."
            )

        try:
            # Lê somente as colunas necessárias e limita as linhas.
            df = pd.read_csv(
                self.caminho_csv,
                usecols=self.COLUNAS_OBRIGATORIAS,
                nrows=self.MAX_LINHAS_TREINAMENTO,
                low_memory=True,
            )

            if not all(
                coluna in df.columns
                for coluna in self.COLUNAS_OBRIGATORIAS
            ):
                raise ValueError(
                    "O dataset não possui todas as colunas necessárias."
                )

            # Garante que as colunas do modelo sejam numéricas.
            for coluna in self.COLUNAS_OBRIGATORIAS:
                df[coluna] = pd.to_numeric(
                    df[coluna],
                    errors="coerce",
                )

            # Remove registros sem os valores necessários.
            df = df.dropna(subset=self.COLUNAS_OBRIGATORIAS)

            # Evita valores infinitos nos dados.
            df = df[
                df[self.COLUNAS_OBRIGATORIAS]
                .apply(lambda coluna: coluna.map(math.isfinite))
                .all(axis=1)
            ]

            if df.empty:
                raise ValueError(
                    "Não existem registros válidos para treinamento."
                )

            return df

        except (FileNotFoundError, ValueError):
            raise
        except Exception as exc:
            raise RuntimeError(
                "Falha ao processar o dataset."
            ) from exc

    def treinar_modelo_com_dados_reais(self) -> None:
        """Treina o modelo usando uma amostra dos dados reais."""

        df = self.carregar_e_validar_dados()

        X = df[self.COLUNAS_MODELO]

        # Mantém a fórmula de pontuação do projeto.
        y = (
            df["Loss Rate (%)"] * 2
            + df["Quantity Sold (kilo)"] * 0.5
        )

        self.model.fit(X, y)
        self._is_trained = True

    def prever_prioridade_lote(
        self,
        qtd_kilo: float,
        preco_atacado: float,
        taxa_perda: float,
    ) -> Dict[str, Union[str, float]]:
        """Realiza uma previsão de urgência para um lote."""

        if not self._is_trained:
            return {"erro": "O modelo não foi treinado."}

        if (
            not self._numero_valido(qtd_kilo)
            or not 0 < qtd_kilo <= 10000
        ):
            return {
                "erro": (
                    "Parâmetro inválido: qtd_kilo deve estar "
                    "entre 0 e 10.000."
                )
            }

        if (
            not self._numero_valido(preco_atacado)
            or not 0 < preco_atacado <= 1000
        ):
            return {
                "erro": (
                    "Parâmetro inválido: preco_atacado está "
                    "fora do intervalo permitido."
                )
            }

        if (
            not self._numero_valido(taxa_perda)
            or not 0 <= taxa_perda <= 100
        ):
            return {
                "erro": (
                    "Parâmetro inválido: taxa_perda deve estar "
                    "entre 0% e 100%."
                )
            }

        try:
            features = pd.DataFrame(
                [[
                    float(qtd_kilo),
                    float(preco_atacado),
                    float(taxa_perda),
                ]],
                columns=self.COLUNAS_MODELO,
            )

            predicao = self.model.predict(features)

            return {
                "status": "sucesso",
                "pontuacao_urgencia": round(
                    float(predicao[0]),
                    2,
                ),
            }

        except Exception:
            return {
                "erro": (
                    "Erro interno ao processar a previsão do lote."
                )
            }

    @staticmethod
    def _numero_valido(valor: object) -> bool:
        """Verifica se o valor é numérico e finito."""

        return (
            isinstance(valor, (int, float))
            and math.isfinite(float(valor))
        )
