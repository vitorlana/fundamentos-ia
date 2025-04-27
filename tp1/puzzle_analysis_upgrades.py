import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.ticker as ticker
from pathlib import Path
import re

# Configuração global de estilo para os gráficos
plt.rcParams['font.size'] = 12
plt.rcParams['axes.grid'] = True
plt.rcParams['grid.alpha'] = 0.3
plt.rcParams['figure.figsize'] = [12, 8]
plt.rcParams['figure.dpi'] = 100
plt.rcParams['savefig.dpi'] = 300

# Função para formatar números grandes (evitar notação científica)
def formatar_numero(x, pos):
    """Formata números para apresentação em milhares, milhões, etc."""
    if x >= 1e6:
        return f'{x/1e6:.1f}M'
    elif x >= 1e3:
        return f'{x/1e3:.1f}K'
    else:
        return f'{x:.0f}'

# Função para criar o gráfico de solucionabilidade no estilo solicitado
def grafico_solucionabilidade_estilo(df, nome_arquivo="analise_solucionabilidade.png"):
    """
    Cria um gráfico de evolução temporal da solucionabilidade,
    exatamente no estilo do exemplo fornecido.
    """
    # Verificar se a coluna 'Solvable' está no DataFrame
    if 'Solvable' not in df.columns:
        print("Erro: Coluna 'Solvable' não encontrada no DataFrame.")
        return None
    
    # Ordenar o DataFrame por iteração para análise sequencial
    df_sorted = df.sort_values(['Iteration'])
    
    # Calcular proporção acumulada de tabuleiros solucionáveis
    # Converter para valores numéricos (True = 1, False = 0)
    df_sorted['Solvable_Num'] = df_sorted['Solvable'].astype(int)
    solucionaveis = df_sorted['Solvable_Num'].cumsum()
    total = np.arange(1, len(df_sorted) + 1)
    proporcao = (solucionaveis / total) * 100
    
    # Valor final
    valor_final = proporcao.iloc[-1]
    
    # Criar figura com o estilo exato solicitado
    plt.figure(figsize=(12, 8))
    
    # Configurações gerais do gráfico
    plt.title('Análise de Solucionabilidade - Evolução Temporal', fontsize=16)
    plt.xlabel('Número de Execuções', fontsize=12)
    plt.ylabel('Porcentagem Acumulada de Tabuleiros Solucionáveis', fontsize=12)
    
    # Configuração de grid (estilo do exemplo)
    plt.grid(True, linestyle=':', alpha=0.7, color='gray')
    
    # Linha horizontal de valor final (para manter a linha de referência visual)
    plt.axhline(y=valor_final, linestyle='--', color='red', 
               label=f'Valor Final: {valor_final:.2f}%')
    
    # Plotar gráfico de linha com marcadores circulares
    plt.plot(total, proporcao, 'o-', color='blue', linewidth=1.5, 
             label=f'Proporção Acumulada', markersize=3)
    
    # Configurar limites e formato dos eixos
    plt.xlim(0, len(total))
    plt.ylim(0, 85)  # Ajustado para ser visualmente similar ao exemplo
    
    # Formatador para o eixo x (números em K)
    plt.gca().xaxis.set_major_formatter(ticker.FuncFormatter(formatar_numero))
    
    # Legenda
    plt.legend(loc='upper right', fontsize=10)
    
    # Salvar figura
    plt.tight_layout()
    plt.savefig(nome_arquivo)
    print(f"Gráfico '{nome_arquivo}' gerado com o estilo solicitado.")
    plt.close()
    
    return True

# Exemplo de uso da função de gráfico especializado
def criar_grafico_especial(df, algoritmo='A*'):
    """
    Cria um gráfico que mostra a relação entre inversões e movimentos
    para o algoritmo especificado.
    """
    # Filtrar apenas o algoritmo desejado e soluções encontradas
    df_algo = df[(df['Algorithm'] == algoritmo) & (df['Found'] == True)].copy()
    
    if df_algo.empty:
        print(f"Sem dados suficientes para o algoritmo {algoritmo}.")
        return None
    
    # Se houver a coluna de inversões, analisar a relação com a quantidade de movimentos
    if 'Inversoes' in df_algo.columns and 'QtdMovimentos' in df_algo.columns:
        plt.figure(figsize=(10, 7))
        
        # Gráfico de dispersão com regressão
        plt.scatter(df_algo['Inversoes'], df_algo['QtdMovimentos'], 
                  alpha=0.7, s=60, c='blue', label=f'Soluções do {algoritmo}')
        
        # Adicionar linha de tendência
        z = np.polyfit(df_algo['Inversoes'], df_algo['QtdMovimentos'], 1)
        p = np.poly1d(z)
        plt.plot(df_algo['Inversoes'], p(df_algo['Inversoes']), "r--", 
                alpha=0.8, linewidth=2, 
                label=f'Tendência: y={z[0]:.2f}x+{z[1]:.2f}')
        
        plt.title(f'Relação entre Inversões e Movimentos para {algoritmo}')
        plt.xlabel('Número de Inversões')
        plt.ylabel('Quantidade de Movimentos')
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.legend()
        
        plt.tight_layout()
        plt.savefig(f"inversoes_movimentos_{algoritmo}.png")
        print(f"Gráfico 'inversoes_movimentos_{algoritmo}.png' gerado.")
        plt.close()
        
        return True
    else:
        print("Colunas necessárias não encontradas para este gráfico.")
        return None

# Função para analisar o consumo de memória
def grafico_memoria(df, nome_arquivo="consumo_memoria.png"):
    """
    Cria um gráfico especializado para análise de consumo de memória por algoritmo.
    """
    if 'MemMBFim' not in df.columns or 'MemMBInicio' not in df.columns:
        print("Colunas de memória não encontradas no DataFrame.")
        return None
    
    # Calcular consumo de memória
    df['ConsumoMemoria'] = df['MemMBFim'] - df['MemMBInicio']
    
    # Agrupar por algoritmo
    memoria_algo = df.groupby('Algorithm')['ConsumoMemoria'].agg(['mean', 'max', 'min'])
    
    # Criar gráfico
    plt.figure(figsize=(10, 7))
    
    # Configurar cores
    colors = {'BFS': 'blue', 'DFS': 'red', 'A*': 'green'}
    
    # Criar barras para cada algoritmo
    algoritmos = memoria_algo.index
    largura = 0.7
    
    for i, algo in enumerate(algoritmos):
        # Barras para média
        plt.bar(i, memoria_algo.loc[algo, 'mean'], 
               width=largura, 
               color=colors.get(algo, 'gray'),
               alpha=0.7, 
               label=f'{algo}')
        
        # Linha de erro para min/max
        plt.vlines(x=i, 
                  ymin=memoria_algo.loc[algo, 'min'],
                  ymax=memoria_algo.loc[algo, 'max'],
                  color='black', 
                  linewidth=2)
        
        # Adicionar valores nas barras
        plt.text(i, memoria_algo.loc[algo, 'mean'] + 1, 
                f"{memoria_algo.loc[algo, 'mean']:.1f} MB", 
                ha='center', 
                va='bottom', 
                fontsize=10)
    
    plt.title('Consumo de Memória por Algoritmo')
    plt.ylabel('Consumo de Memória (MB)')
    plt.xticks(range(len(algoritmos)), algoritmos)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Ajustar limites para melhor visualização
    max_val = memoria_algo['max'].max()
    plt.ylim(0, max_val * 1.2)
    
    plt.tight_layout()
    plt.savefig(nome_arquivo)
    print(f"Gráfico '{nome_arquivo}' gerado.")
    plt.close()
    
    return True

# Exemplo de uso das funções melhoradas
if __name__ == "__main__":
    print("Este módulo contém funções melhoradas para análise de dados do 15-puzzle.")
    print("Importe-o em seu script principal para utilizar estas funções.")
