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

def analisar_tabuleiros(num_execucoes=100):
    """
    Analisa a geração de tabuleiros, um por execução.
    Retorna as proporções de tabuleiros solucionáveis.
    """
    resultados = []
    solucionaveis = 0
    
    for exec_num in range(1, num_execucoes + 1):
        tabuleiro = gerar_tabuleiro_aleatorio()
        is_soluvel = eh_soluvel(tabuleiro)
        if is_soluvel:
            solucionaveis += 1
        
        proporcao_atual = (solucionaveis / exec_num) * 100
        resultados.append(proporcao_atual)
        # print(f"Execução {exec_num}: {proporcao_atual:.2f}% solucionáveis até agora")
    
    print(f"\nTotal: {solucionaveis} tabuleiros solucionáveis de {num_execucoes}")
    return resultados

def plotar_resultados(resultados):
    """
    Plota um gráfico com os resultados acumulados da análise.
    """
    execucoes = list(range(1, len(resultados) + 1))
    valor_final = resultados[-1]
    
    plt.figure(figsize=(12, 6))
    plt.plot(execucoes, resultados, 'bo-', alpha=0.5, label='Proporção Acumulada')
    plt.axhline(y=valor_final, color='r', linestyle='--', 
                label=f'Valor Final: {valor_final:.2f}%')
    
    plt.xlabel('Número de Execuções')
    plt.ylabel('Porcentagem Acumulada de Tabuleiros Solucionáveis')
    plt.title('Análise de Solucionabilidade - Evolução Temporal')
    plt.grid(True)
    plt.legend()
    plt.savefig('analise_tabuleiros.png')
    plt.close()

if __name__ == "__main__":
    # Análise com 1000 execuções (um tabuleiro por execução)
    resultados = analisar_tabuleiros(num_execucoes=1000)
    plotar_resultados(resultados)