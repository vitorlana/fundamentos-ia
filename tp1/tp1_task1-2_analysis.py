from tp1_completo import *
import matplotlib.pyplot as plt
import numpy as np

def teste_gerar_tabuleiro_aleatorio():
    """
    Testa a função gerar_tabuleiro_aleatorio.
    """
    while True:
        tabuleiro = gerar_tabuleiro_aleatorio()
        soluvel = eh_soluvel(tabuleiro)
        print("Tabuleiro gerado:")
        for linha in tabuleiro:
            print(linha)
        print("É solucionável?", soluvel)
        if not soluvel:
            break

def analisar_tabuleiros(num_execucoes_array):
    """
    Analisa a geração de tabuleiros para cada valor no array de execuções.
    Retorna um dicionário com os resultados para cada número de execuções.
    """
    resultados_por_execucao = {}

    for num_execucoes in num_execucoes_array:
        resultados = []
        solucionaveis = 0
        tabuleiros_gerados = []

        for exec_num in range(1, num_execucoes + 1):
            tabuleiro = gerar_tabuleiro_aleatorio()
            tabuleiros_gerados.append(tabuleiro)
            is_soluvel = eh_soluvel(tabuleiro)
            if is_soluvel:
                solucionaveis += 1

            proporcao_atual = (solucionaveis / exec_num) * 100
            resultados.append(proporcao_atual)

        print(f"\nTotal: {solucionaveis} tabuleiros solucionáveis de {num_execucoes}")
        resultados_por_execucao[num_execucoes] = (resultados, tabuleiros_gerados)

    return resultados_por_execucao

def analisar_tabuleiros_iguais(tabuleiros_gerados):
    """
    Analisa a quantidade de tabuleiros duplicados em um array fornecido.
    """
    contagem = {}
    for tabuleiro in tabuleiros_gerados:
        t = tuple(tuple(linha) for linha in tabuleiro)
        contagem[t] = contagem.get(t, 0) + 1

    total_tabuleiros_unicos = len(contagem)
    total_tabuleiros = len(tabuleiros_gerados)
    total_duplicados = total_tabuleiros - total_tabuleiros_unicos
    porcentagem_duplicados = (total_duplicados / total_tabuleiros) * 100

    print(f"Total gerados: {total_tabuleiros}, "
          f"Únicos: {total_tabuleiros_unicos}, "
          f"Duplicados: {total_duplicados} ({porcentagem_duplicados:.2f}%)")

def plotar_resultados_analise_tabuleiros(resultados):
    """
    Plota um gráfico com os resultados acumulados da análise.
    """
    execucoes = list(range(1, len(resultados) + 1))
    valor_final = resultados[-1]

    plt.figure(figsize=(10, 6))  # Ajusta o tamanho do gráfico
    plt.plot(execucoes, resultados, 'bo-', alpha=0.7, label='Proporção Acumulada')
    plt.axhline(y=valor_final, color='r', linestyle='--',
                label=f'Valor Final: {valor_final:.2f}%')

    plt.xlabel('Número de Execuções', fontsize=12)
    plt.ylabel('Porcentagem Acumulada de Tabuleiros Solucionáveis', fontsize=12)
    plt.title('Análise de Solucionabilidade - Evolução Temporal', fontsize=14)
    plt.xticks(fontsize=10)
    plt.yticks(fontsize=10)
    plt.grid(True, linestyle='--', linewidth=0.5, alpha=0.7)
    plt.legend(fontsize=10, loc='best')
    plt.tight_layout()  # Ajusta os elementos para caberem melhor no gráfico
    plt.savefig(f'analise_tabuleiros-{len(resultados)}-execucoes.png', dpi=300)  # Aumenta a qualidade do gráfico
    plt.close()

def gerar_tabuleiros_ate_encontrar_igual():
    """
    Gera tabuleiros aleatórios até encontrar um tabuleiro repetido.
    """
    gerados = set()
    contador = 0
    while True:
        tabuleiro = gerar_tabuleiro_aleatorio()
        t = tuple(tuple(linha) for linha in tabuleiro)
        if t in gerados:
            print(f"Tabuleiro repetido encontrado após {contador + 1} gerações.")
            return tabuleiro
        gerados.add(t)
        contador += 1

if __name__ == "__main__":
    # Análise com diferentes números de execuções
    execucoes_array = [100, 1000, 10000, 100000,1000000,10000000]
    # execucoes_array = [10]
    resultados_por_execucao = analisar_tabuleiros(execucoes_array)

    for num_execucoes, (resultados, tabuleiros_gerados) in resultados_por_execucao.items():
        print(f"Plotando resultados para {num_execucoes} execuções...")
        plotar_resultados_analise_tabuleiros(resultados)
        print(f"Analisando tabuleiros duplicados para {num_execucoes} execuções...")
        analisar_tabuleiros_iguais(tabuleiros_gerados)

    print(f"Gerando tabuleiros até encontrar um igual")
    for i in range(100):
        print(f"({i + 1})",end=" ")
        gerar_tabuleiros_ate_encontrar_igual()


