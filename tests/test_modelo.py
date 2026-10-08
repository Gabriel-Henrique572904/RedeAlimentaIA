import pytest

from app.modelo import PipelineAlimentoSeguro


@pytest.fixture
def modelo():
    instancia = PipelineAlimentoSeguro(
        "tests/data/Consolidated_Supermarket_Data.csv"
    )
    instancia.treinar_modelo_com_dados_reais()
    return instancia


def test_modelo_consegue_prever(modelo):
    resultado = modelo.prever_prioridade_lote(
        qtd_kilo=50,
        preco_atacado=5.5,
        taxa_perda=12.5
    )

    assert resultado["status"] == "sucesso"
    assert "pontuacao_urgencia" in resultado
    assert isinstance(resultado["pontuacao_urgencia"], float)


def test_rejeita_quantidade_negativa(modelo):
    resultado = modelo.prever_prioridade_lote(
        qtd_kilo=-1,
        preco_atacado=5.5,
        taxa_perda=12.5
    )

    assert "erro" in resultado


def test_rejeita_quantidade_acima_do_limite(modelo):
    resultado = modelo.prever_prioridade_lote(
        qtd_kilo=10001,
        preco_atacado=5.5,
        taxa_perda=12.5
    )

    assert "erro" in resultado


def test_rejeita_preco_invalido(modelo):
    resultado = modelo.prever_prioridade_lote(
        qtd_kilo=50,
        preco_atacado=0,
        taxa_perda=12.5
    )

    assert "erro" in resultado


def test_rejeita_taxa_de_perda_invalida(modelo):
    resultado = modelo.prever_prioridade_lote(
        qtd_kilo=50,
        preco_atacado=5.5,
        taxa_perda=101
    )

    assert "erro" in resultado
