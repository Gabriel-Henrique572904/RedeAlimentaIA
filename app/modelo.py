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
    - validar a estrutura do CSV;
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

    def __init__(self, caminho_csv: str):
        if not caminho_csv.endswith(".csv") or ".." in caminho_csv:
            raise ValueError("Erro de segurança: caminho de arquivo inválido.")

        self.caminho_csv = caminho_csv
        self.model = RandomForestRegressor(
            n_estimators=50,
            random_state=42,
        )
        self._is_trained = False

    def carregar_e_validar_dados(self) -> pd.DataFrame:
        """Carrega o CSV e verifica as colunas necessárias."""
        if not os.path.exists(self.caminho_csv):
            raise FileNotFoundError("O arquivo de dados não foi encontrado.")

        try:
            df = pd.read_csv(self.caminho_csv)
            colunas_obrigatorias = [
                "Quantity Sold (kilo)",
                "Unit Selling Price (RMB/kg)",
                "Wholesale Price (RMB/kg)",
                "Loss Rate (%)",
            ]

            if not all(coluna in df.columns for coluna in colunas_obrigatorias):
                raise ValueError("O dataset não possui todas as colunas necessárias.")

            return df
        except (FileNotFoundError, ValueError):
            raise
        except Exception as exc:
            raise RuntimeError("Falha ao processar o dataset.") from exc

    def treinar_modelo_com_dados_reais(self) -> None:
        """Treina o modelo utilizando os dados do dataset."""
        df = self.carregar_e_validar_dados()

        df_limpo = df.dropna(subset=self.COLUNAS_MODELO)
        X = df_limpo[self.COLUNAS_MODELO]

        y = (
            df_limpo["Loss Rate (%)"] * 2
            + df_limpo["Quantity Sold (kilo)"] * 0.5
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

        if not self._numero_valido(qtd_kilo) or not 0 < qtd_kilo <= 10000:
            return {"erro": "Parâmetro inválido: qtd_kilo deve estar entre 0 e 10.000."}

        if not self._numero_valido(preco_atacado) or not 0 < preco_atacado <= 1000:
            return {"erro": "Parâmetro inválido: preco_atacado está fora do intervalo permitido."}

        if not self._numero_valido(taxa_perda) or not 0 <= taxa_perda <= 100:
            return {"erro": "Parâmetro inválido: taxa_perda deve estar entre 0% e 100%."}

        try:
            features = pd.DataFrame(
                [[float(qtd_kilo), float(preco_atacado), float(taxa_perda)]],
                columns=self.COLUNAS_MODELO,
            )
            predicao = self.model.predict(features)

            return {
                "status": "sucesso",
                "pontuacao_urgencia": round(float(predicao[0]), 2),
            }
        except Exception:
            return {"erro": "Erro interno ao processar a previsão do lote."}

    @staticmethod
    def _numero_valido(valor: object) -> bool:
        return isinstance(valor, (int, float)) and math.isfinite(float(valor))
