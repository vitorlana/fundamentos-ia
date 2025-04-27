import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.ticker as ticker
from pathlib import Path

# Função para análise do consumo de memória com tratamento de valores negativos
def analisar_memoria(df, salvar_grafico=True, nome_arquivo="consumo_memoria_ajustado.png"):
    """
    Analisa o consumo de memória dos algoritmos com tratamento para valores negativos.
    """
    print("\n===== ANÁLISE DE CONSUMO DE MEMÓRIA =====")
    
    # Verificar se as colunas de memória existem
    if 'MemMBFim' not in df.columns or 'MemMBInicio' not in df.columns:
        print("Colunas de memória não encontradas no DataFrame.")
        return None
    
    # Criar cópia para análise
    df_mem = df.copy()
    
    # Analisar os dados brutos primeiro
    print("\nDados brutos de memória:")
    print("Estatísticas de MemMBInicio:")
    print(df_mem.groupby('Algorithm')['MemMBInicio'].describe())
    print("\nEstatísticas de MemMBFim:")
    print(df_mem.groupby('Algorithm')['MemMBFim'].describe())
    
    # Calcular consumo usando valores absolutos
    df_mem['ConsumoMemoria'] = df_mem['MemMBFim'] - df_mem['MemMBInicio']
    df_mem['ConsumoMemoriaAbs'] = abs(df_mem['ConsumoMemoria'])
    
    # Verificar quantos valores negativos existem
    negativos = df_mem[df_mem['ConsumoMemoria'] < 0].shape[0]
    total = df_mem.shape[0]
    porcentagem_neg = (negativos / total) * 100 if total > 0 else 0
    
    print(f"\nValores negativos de consumo: {negativos} de {total} ({porcentagem_neg:.2f}%)")
    
    # Mostrar médias por algoritmo para ambas as versões
    consumo_por_algo = df_mem.groupby('Algorithm')['ConsumoMemoria'].mean()
    consumo_abs_por_algo = df_mem.groupby('Algorithm')['ConsumoMemoriaAbs'].mean()
    
    print("\nConsumo médio de memória por algoritmo (original):")
    print(consumo_por_algo)
    
    print("\nConsumo médio de memória por algoritmo (valor absoluto):")
    print(consumo_abs_por_algo)
    
    # Analisar comportamento por iteração
    df_mem['Iteracao'] = df_mem['Iteration']
    
    # Ver se há um padrão relacionado à iteração
    print("\nMédia de consumo por iteração:")
    print(df_mem.groupby('Iteracao')['ConsumoMemoria'].mean())
    
    # Sugerir interpretação
    if negativos > 0:
        print("\nINTERPRETAÇÃO DOS VALORES NEGATIVOS:")
        print("Os valores negativos podem indicar:")
        print("1. Algum tipo de liberação de memória pelo sistema durante a execução.")
        print("2. Possível erro na coleta de dados de memória pelo programa.")
        print("3. Medo menos precisa de medir consumo de memória para algoritmos muito eficientes.")
        print("\nSUGESTÃO: Para análise comparativa, considere:")
        print("- Usar valores absolutos para comparação geral.")
        print("- Analisar o consumo máximo de memória, que é mais relevante para o desempenho.")
    
    # Se solicitado, criar gráfico de consumo de memória
    if salvar_grafico:
        # Criando gráfico com valores absolutos para tornar comparação mais clara
        plt.figure(figsize=(12, 8))
        
        # Gráfico de barras para cada algoritmo
        algoritmos = df_mem['Algorithm'].unique()
        cores = {'BFS': 'blue', 'DFS': 'red', 'A*': 'green'}
        
        # Dados para o gráfico
        consumo_abs = [consumo_abs_por_algo[algo] for algo in algoritmos]
        consumo_org = [consumo_por_algo[algo] for algo in algoritmos]
        
        # Criar barras para valores originais
        x = np.arange(len(algoritmos))
        largura = 0.35
        
        plt.bar(x - largura/2, consumo_org, largura, 
               label='Valor Original', alpha=0.7,
               color=[cores.get(algo, 'gray') for algo in algoritmos])
        
        plt.bar(x + largura/2, consumo_abs, largura, 
               label='Valor Absoluto', alpha=0.7,
               color=[cores.get(algo, 'gray') for algo in algoritmos],
               hatch='///')
        
        # Adicionar valores nas barras
        for i, valor in enumerate(consumo_org):
            plt.text(i - largura/2, valor + (1 if valor >= 0 else -3),
                    f"{valor:.2f}", ha='center', va='bottom' if valor >= 0 else 'top')
        
        for i, valor in enumerate(consumo_abs):
            plt.text(i + largura/2, valor + 1,
                    f"{valor:.2f}", ha='center', va='bottom')
        
        plt.title('Comparação de Métodos de Medição de Consumo de Memória')
        plt.ylabel('Consumo de Memória (MB)')
        plt.xlabel('Algoritmo')
        plt.xticks(x, algoritmos)
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        plt.legend()
        
        plt.tight_layout()
        plt.savefig(nome_arquivo)
        print(f"\nGráfico '{nome_arquivo}' gerado.")
        plt.close()
        
        # Adicionar um gráfico de dispersão para visualizar a relação entre memória inicial e final
        plt.figure(figsize=(12, 8))
        
        for algo in algoritmos:
            df_algo = df_mem[df_mem['Algorithm'] == algo]
            plt.scatter(df_algo['MemMBInicio'], df_algo['MemMBFim'], 
                       label=algo, alpha=0.7, s=50,
                       color=cores.get(algo, 'gray'))
        
        # Adicionar linha y=x para referência
        max_val = max(df_mem['MemMBInicio'].max(), df_mem['MemMBFim'].max())
        plt.plot([0, max_val], [0, max_val], 'k--', alpha=0.5, label='y=x (sem mudança)')
        
        plt.title('Relação entre Memória Inicial e Final por Algoritmo')
        plt.xlabel('Memória Inicial (MB)')
        plt.ylabel('Memória Final (MB)')
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.legend()
        
        plt.tight_layout()
        plt.savefig('relacao_memoria_ini_fim.png')
        print("Gráfico 'relacao_memoria_ini_fim.png' gerado.")
        plt.close()
    
    # Retornar o DataFrame com a análise de memória
    return df_mem

# Função para extrair o consumo máximo de memória
def analisar_pico_memoria(df):
    """
    Analisa o pico de consumo de memória por algoritmo, que é mais relevante
    para comparar o desempenho dos algoritmos em termos de memória.
    """
    if 'MemMBFim' not in df.columns or 'MemMBInicio' not in df.columns:
        print("Colunas de memória não encontradas no DataFrame.")
        return None
    
    # Criar cópia para análise
    df_mem = df.copy()
    
    # Calcular o máximo das duas medidas para cada execução
    df_mem['PicoMemoria'] = df_mem[['MemMBInicio', 'MemMBFim']].max(axis=1)
    
    # Analisar por algoritmo
    pico_por_algo = df_mem.groupby('Algorithm')['PicoMemoria'].agg(['mean', 'max', 'min'])
    
    print("\n===== ANÁLISE DE PICO DE CONSUMO DE MEMÓRIA =====")
    print("\nEstatísticas de pico de memória por algoritmo:")
    print(pico_por_algo)
    
    # Criar gráfico de pico de memória
    plt.figure(figsize=(12, 8))
    
    algoritmos = pico_por_algo.index
    cores = {'BFS': 'blue', 'DFS': 'red', 'A*': 'green'}
    
    # Criar barras para valores médios
    bars = plt.bar(algoritmos, pico_por_algo['mean'], 
                  color=[cores.get(algo, 'gray') for algo in algoritmos],
                  alpha=0.7)
    
    # Adicionar valores nas barras
    for bar, valor in zip(bars, pico_por_algo['mean']):
        plt.text(bar.get_x() + bar.get_width()/2., valor + 0.5,
                f"{valor:.2f} MB", ha='center', va='bottom')
    
    # Adicionar linhas de erro min-max
    for i, algo in enumerate(algoritmos):
        plt.vlines(x=i, 
                  ymin=pico_por_algo.loc[algo, 'min'],
                  ymax=pico_por_algo.loc[algo, 'max'],
                  color='black', linewidth=2)
        
        # Adicionar anotações para min/max
        plt.text(i, pico_por_algo.loc[algo, 'max'] + 0.5,
                f"Max: {pico_por_algo.loc[algo, 'max']:.2f}", 
                ha='center', va='bottom', fontsize=8)
    
    plt.title('Pico de Consumo de Memória por Algoritmo')
    plt.ylabel('Memória (MB)')
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.ylim(0, pico_por_algo['max'].max() * 1.2)  # Espaço para anotações
    
    plt.tight_layout()
    plt.savefig('pico_memoria.png')
    print("Gráfico 'pico_memoria.png' gerado.")
    plt.close()
    
    return pico_por_algo

# Função para demonstrar como usar as análises de memória
def exemplo_analise_memoria(caminho_arquivo='puzzle_data.csv'):
    """
    Exemplo de como usar as funções de análise de memória.
    """
    try:
        df = pd.read_csv(caminho_arquivo)
        print(f"Arquivo carregado com sucesso! Dimensões: {df.shape}")
        
        # Executar análises de memória
        df_mem = analisar_memoria(df)
        picos = analisar_pico_memoria(df)
        
        print("\nAnálise de memória concluída!")
        
    except Exception as e:
        print(f"Erro ao analisar o arquivo: {e}")

if __name__ == "__main__":
    print("Esse script pode ser executado diretamente para analisar o consumo de memória.")
    print("Ou importado como módulo para uso em outros scripts.")
    
    # Verificar se o arquivo padrão existe
    arquivo_padrao = 'resultados.csv'
    if Path(arquivo_padrao).exists():
        exemplo_analise_memoria(arquivo_padrao)
    else:
        print(f"Arquivo '{arquivo_padrao}' não encontrado.")
        caminho = input("Digite o caminho do arquivo CSV para análise: ")
        if caminho:
            exemplo_analise_memoria(caminho)
