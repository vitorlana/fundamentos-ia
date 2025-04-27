import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.ticker as ticker
from pathlib import Path
import re
from matplotlib.gridspec import GridSpec

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
        return f'{x / 1e6:.1f}M'
    elif x >= 1e3:
        return f'{x / 1e3:.1f}K'
    else:
        return f'{x:.0f}'


# Função para carregar os dados
def carregar_dados(caminho_arquivo):
    """Carrega o arquivo CSV e retorna um DataFrame pandas."""
    try:
        df = pd.read_csv(caminho_arquivo)
        print(f"Arquivo carregado com sucesso! Dimensões: {df.shape}")

        # Processamento inicial dos dados
        if 'Directions' in df.columns:
            # Converter strings de direções em listas e calcular tamanho
            df['DirectionsList'] = df['Directions'].apply(
                lambda x: eval(x) if isinstance(x, str) and x.startswith('[') else []
            )
            df['TamanhoSolucao'] = df['DirectionsList'].apply(len)

        # Calcular consumo de memória
        if 'MemMBFim' in df.columns and 'MemMBInicio' in df.columns:
            df['ConsumoMemoria'] = df['MemMBFim'] - df['MemMBInicio']

        return df
    except Exception as e:
        print(f"Erro ao carregar o arquivo: {e}")
        return None


# Função para estatísticas básicas
def estatisticas_basicas(df):
    """Exibe estatísticas básicas sobre os dados."""
    print("\n===== ESTATÍSTICAS BÁSICAS =====")

    # Estatísticas gerais
    algoritmos = df['Algorithm'].unique()
    print(f"Total de iterações: {df['Iteration'].nunique()}")
    print(f"Algoritmos analisados: {', '.join(algoritmos)}")

    # Estatísticas por algoritmo
    stats = pd.DataFrame(index=algoritmos)

    # Tempo médio, min, max
    stats['Tempo Médio (s)'] = df.groupby('Algorithm')['Time'].mean()
    stats['Tempo Min (s)'] = df.groupby('Algorithm')['Time'].min()
    stats['Tempo Max (s)'] = df.groupby('Algorithm')['Time'].max()

    # Nós expandidos
    stats['Média Nós Expandidos'] = df.groupby('Algorithm')['Expanded'].mean()

    # Taxa de sucesso
    stats['Taxa Sucesso (%)'] = df.groupby('Algorithm')['Found'].mean() * 100

    # Passos para casos resolvidos
    df_solved = df[df['Found'] == True]
    if not df_solved.empty:
        stats['Passos Médios (soluções)'] = df_solved.groupby('Algorithm')['Steps'].mean()

    # Eficiência (nós por passo)
    df_eff = df[df['Steps'] > 0].copy()
    if not df_eff.empty:
        df_eff['Eficiencia'] = df_eff['Expanded'] / df_eff['Steps']
        stats['Eficiência (nós/passo)'] = df_eff.groupby('Algorithm')['Eficiencia'].mean()

    # Consumo de memória
    if 'ConsumoMemoria' in df.columns:
        stats['Consumo Memória (MB)'] = df.groupby('Algorithm')['ConsumoMemoria'].mean()

    print("\nEstatísticas por algoritmo:")
    print(stats.round(2))

    return stats


# Função para criar gráficos de evolução temporal
def grafico_evolucao_temporal(df, nome_arquivo="evolucao_temporal.png"):
    """
    Cria gráficos de evolução temporal no estilo solicitado.
    """
    # Ordenar o DataFrame por algoritmo e iteração para análise sequencial
    df_sorted = df.sort_values(['Algorithm', 'Iteration'])

    # Garantir ordem consistente dos algoritmos
    ordem_algoritmos = ['BFS', 'DFS', 'A*']
    algoritmos_presentes = [algo for algo in ordem_algoritmos if algo in df['Algorithm'].unique()]

    # Definir cores para os algoritmos (ordem consistente)
    colors = {'BFS': 'blue', 'DFS': 'red', 'A*': 'green'}

    # Criar três figuras separadas em vez de subplots

    # 1. Gráfico da Taxa de Sucesso Acumulada
    plt.figure(figsize=(12, 8))

    # Calcular taxa de sucesso acumulada para cada algoritmo
    for algo in algoritmos_presentes:
        df_algo = df_sorted[df_sorted['Algorithm'] == algo].copy()  # Usar .copy() para evitar SettingWithCopyWarning
        success_count = df_algo['Found'].cumsum()
        total_count = np.arange(1, len(df_algo) + 1)
        success_rate = (success_count / total_count) * 100

        # Plotar gráfico de linha com marcadores circulares
        plt.plot(total_count, success_rate, 'o-', color=colors.get(algo, 'gray'),
                 label=f'{algo} - Final: {success_rate.iloc[-1]:.2f}%', markersize=4)

        # Adicionar linha horizontal para o valor final
        plt.axhline(y=success_rate.iloc[-1], linestyle='--', color=colors.get(algo, 'gray'), alpha=0.7)

    plt.xlabel('Número de Execuções')
    plt.ylabel('Taxa de Sucesso Acumulada (%)')
    plt.title('Análise de Sucesso - Evolução Temporal')
    plt.legend(loc='best')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.ylim(0, 105)  # Limitar eixo y de 0 a 105%

    # Configurar formatação do eixo x para mostrar milhares (K)
    plt.gca().xaxis.set_major_formatter(ticker.FuncFormatter(formatar_numero))

    plt.tight_layout()
    nome_arquivo_taxa = nome_arquivo.replace('.png', '_taxa_sucesso.png')
    plt.savefig(nome_arquivo_taxa)
    print(f"Gráfico '{nome_arquivo_taxa}' gerado.")
    plt.close()

    # 2. Gráfico de Tempo de Execução (média móvel)
    plt.figure(figsize=(12, 8))

    window_size = min(5, df['Iteration'].nunique())  # Tamanho da janela para média móvel

    for algo in algoritmos_presentes:
        df_algo = df_sorted[df_sorted['Algorithm'] == algo].copy()  # Usar .copy() para evitar SettingWithCopyWarning

        # Calcular média móvel para suavizar a curva
        if len(df_algo) >= window_size:
            rolling_time = df_algo['Time'].rolling(window=window_size, min_periods=1).mean()
        else:
            rolling_time = df_algo['Time']

        # Plotar tempo vs. iteração
        plt.plot(np.arange(1, len(df_algo) + 1), rolling_time, 'o-', color=colors.get(algo, 'gray'),
                 label=f'{algo} - Média: {df_algo["Time"].mean():.4f}s', markersize=4)

    plt.xlabel('Número de Execuções')
    plt.ylabel('Tempo de Execução (segundos)')
    plt.title('Desempenho Temporal - Média Móvel')
    plt.legend(loc='best')
    plt.grid(True, linestyle='--', alpha=0.7)

    # Decidir se usa escala logarítmica com base nos dados
    if df['Time'].max() / df['Time'].min() > 100:
        plt.yscale('log')
        plt.ylabel('Tempo de Execução (segundos) - Escala Log')

    # Configurar formatação do eixo x para mostrar milhares (K)
    plt.gca().xaxis.set_major_formatter(ticker.FuncFormatter(formatar_numero))

    plt.tight_layout()
    nome_arquivo_tempo = nome_arquivo.replace('.png', '_tempo.png')
    plt.savefig(nome_arquivo_tempo)
    print(f"Gráfico '{nome_arquivo_tempo}' gerado.")
    plt.close()

    # 3. Gráfico de Eficiência (nós expandidos / passos)
    plt.figure(figsize=(12, 8))

    for algo in algoritmos_presentes:
        # Filtrar e criar cópia para evitar SettingWithCopyWarning
        df_algo = df_sorted[(df_sorted['Algorithm'] == algo) & (df_sorted['Steps'] > 0)].copy()

        if not df_algo.empty:
            # Calcular eficiência
            df_algo.loc[:, 'Eficiencia'] = df_algo['Expanded'] / df_algo['Steps']

            # Calcular média móvel para suavizar a curva
            if len(df_algo) >= window_size:
                rolling_eff = df_algo['Eficiencia'].rolling(window=window_size, min_periods=1).mean()
            else:
                rolling_eff = df_algo['Eficiencia']

            # Plotar eficiência vs. iteração
            plt.plot(np.arange(1, len(df_algo) + 1), rolling_eff, 'o-', color=colors.get(algo, 'gray'),
                     label=f'{algo} - Média: {df_algo["Eficiencia"].mean():.0f}', markersize=4)

    plt.xlabel('Número de Execuções')
    plt.ylabel('Eficiência (Nós/Passo)')
    plt.title('Evolução da Eficiência dos Algoritmos')
    plt.legend(loc='best')
    plt.grid(True, linestyle='--', alpha=0.7)

    # Escala logarítmica para eficiência devido à grande variação
    plt.yscale('log')

    # Configurar formatação do eixo x para mostrar milhares (K)
    plt.gca().xaxis.set_major_formatter(ticker.FuncFormatter(formatar_numero))
    plt.gca().yaxis.set_major_formatter(ticker.FuncFormatter(formatar_numero))

    plt.tight_layout()
    nome_arquivo_eficiencia = nome_arquivo.replace('.png', '_eficiencia.png')
    plt.savefig(nome_arquivo_eficiencia)
    print(f"Gráfico '{nome_arquivo_eficiencia}' gerado.")
    plt.close()

    print(f"Todos os gráficos de evolução temporal foram gerados.")

    return True


# Função para análise comparativa de algoritmos
def grafico_comparativo_algoritmos(df, stats, nome_arquivo="comparativo_algoritmos.png"):
    """
    Cria gráficos comparativos entre os algoritmos em diferentes métricas, separados em arquivos individuais.
    """
    algoritmos = df['Algorithm'].unique()

    # 1. Gráfico de Barras: Tempo Médio
    plt.figure(figsize=(10, 7))
    tempos = df.groupby('Algorithm')['Time'].mean()
    bars = plt.bar(algoritmos, tempos, color=['blue', 'red', 'green'])

    # Adicionar valores nas barras
    for bar, valor in zip(bars, tempos):
        if valor < 0.01:
            texto = f"{valor:.4f}s"
        elif valor < 0.1:
            texto = f"{valor:.3f}s"
        else:
            texto = f"{valor:.2f}s"
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width() / 2., height + 0.05 * max(tempos),
                 f"{texto}", ha='center', va='bottom', rotation=0)

    plt.title('Tempo Médio de Execução por Algoritmo')
    plt.ylabel('Tempo (segundos)')
    plt.grid(axis='y', linestyle='--', alpha=0.7)

    # Decidir se usa escala logarítmica com base nos dados
    if tempos.max() / tempos.min() > 100:
        plt.yscale('log')
        plt.ylabel('Tempo (segundos) - Escala Log')

    plt.tight_layout()
    plt.savefig(f"tempo_medio_{nome_arquivo}")
    print(f"Gráfico 'tempo_medio_{nome_arquivo}' gerado.")
    plt.close()

    # 2. Gráfico de Barras: Nós Expandidos (médio)
    plt.figure(figsize=(10, 7))
    nos = df.groupby('Algorithm')['Expanded'].mean()
    bars = plt.bar(algoritmos, nos, color=['blue', 'red', 'green'])

    # Adicionar valores nas barras (formatados para K ou M)
    for bar, valor in zip(bars, nos):
        if valor >= 1e6:
            texto = f"{valor / 1e6:.1f}M"
        elif valor >= 1e3:
            texto = f"{valor / 1e3:.1f}K"
        else:
            texto = f"{valor:.0f}"
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width() / 2., height + 0.05 * max(nos),
                 f"{texto}", ha='center', va='bottom', rotation=0)

    plt.title('Média de Nós Expandidos por Algoritmo')
    plt.ylabel('Nós Expandidos')
    plt.grid(axis='y', linestyle='--', alpha=0.7)

    # Usar escala logarítmica para nós expandidos
    plt.yscale('log')
    plt.gca().yaxis.set_major_formatter(ticker.FuncFormatter(formatar_numero))

    plt.tight_layout()
    plt.savefig(f"nos_expandidos_{nome_arquivo}")
    print(f"Gráfico 'nos_expandidos_{nome_arquivo}' gerado.")
    plt.close()

    # 3. Diagrama de Dispersão: Tempo vs. Nós Expandidos
    plt.figure(figsize=(10, 7))

    # Definir cores e marcadores para algoritmos
    cores = {'BFS': 'blue', 'DFS': 'red', 'A*': 'green'}
    marcadores = {'BFS': 'o', 'DFS': 's', 'A*': '^'}

    for algo in algoritmos:
        subset = df[df['Algorithm'] == algo]
        plt.scatter(subset['Expanded'], subset['Time'],
                    color=cores.get(algo, 'gray'),
                    marker=marcadores.get(algo, 'o'),
                    alpha=0.7, s=50, label=algo)

    plt.title('Relação entre Tempo e Nós Expandidos')
    plt.xlabel('Nós Expandidos')
    plt.ylabel('Tempo (segundos)')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend(loc='best')

    # Usar escala logarítmica para ambos os eixos
    plt.xscale('log')
    plt.yscale('log')

    # Formatadores para evitar notação científica
    plt.gca().xaxis.set_major_formatter(ticker.FuncFormatter(formatar_numero))
    plt.gca().yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, pos: f"{x:.2f}" if x < 0.1 else f"{x:.1f}"))

    plt.tight_layout()
    plt.savefig(f"tempo_vs_nos_{nome_arquivo}")
    print(f"Gráfico 'tempo_vs_nos_{nome_arquivo}' gerado.")
    plt.close()

    # 4. Gráfico de Taxa de Sucesso
    plt.figure(figsize=(10, 7))

    # Taxa de sucesso (barras)
    taxa_sucesso = df.groupby('Algorithm')['Found'].mean() * 100
    bars1 = plt.bar(algoritmos, taxa_sucesso, color=['blue', 'red', 'green'], alpha=0.7)

    # Adicionar valores nas barras
    for bar, valor in zip(bars1, taxa_sucesso):
        plt.text(bar.get_x() + bar.get_width() / 2., valor + 2,
                 f"{valor:.1f}%", ha='center', va='bottom', rotation=0)

    plt.title('Taxa de Sucesso por Algoritmo')
    plt.ylabel('Taxa de Sucesso (%)')
    plt.ylim(0, 105)  # Limitar eixo y de 0 a 105%
    plt.grid(axis='y', linestyle='--', alpha=0.7)

    plt.tight_layout()
    plt.savefig(f"taxa_sucesso_{nome_arquivo}")
    print(f"Gráfico 'taxa_sucesso_{nome_arquivo}' gerado.")
    plt.close()

    # 5. Gráfico de Passos Médios da Solução
    plt.figure(figsize=(10, 7))

    # Calcular passos médios para soluções encontradas
    df_solved = df[df['Found'] == True]
    if not df_solved.empty:
        passos_medios = df_solved.groupby('Algorithm')['Steps'].mean()
        bars = plt.bar(algoritmos, passos_medios, color=['blue', 'red', 'green'])

        # Adicionar valores nas barras
        for bar, valor in zip(bars, passos_medios):
            plt.text(bar.get_x() + bar.get_width() / 2., valor + 0.5,
                     f"{valor:.1f}", ha='center', va='bottom')

        plt.title('Tamanho Médio da Solução por Algoritmo')
        plt.ylabel('Número Médio de Passos')
        plt.grid(axis='y', linestyle='--', alpha=0.7)

        plt.tight_layout()
        plt.savefig(f"passos_medios_{nome_arquivo}")
        print(f"Gráfico 'passos_medios_{nome_arquivo}' gerado.")
        plt.close()

    print(f"Todos os gráficos comparativos foram gerados.")

    return True


# Função para análise de solucionabilidade
def grafico_solucionabilidade(df, nome_arquivo="analise_solucionabilidade.png"):
    """
    Cria um gráfico de evolução temporal da solucionabilidade, similar ao exemplo fornecido.
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
    if isinstance(proporcao, pd.Series):
        valor_final = proporcao.iloc[-1]
    else:
        # If proporcao is a scalar (numpy.float64), use it directly
        valor_final = proporcao

    # Criar figura com o estilo exato solicitado
    plt.figure(figsize=(12, 8))

    # Configurações gerais do gráfico
    plt.title('Análise de Solucionabilidade - Evolução Temporal', fontsize=16)
    plt.xlabel('Número de Execuções', fontsize=12)
    plt.ylabel('Porcentagem Acumulada de Tabuleiros Solucionáveis', fontsize=12)

    # Configuração de grid (estilo do exemplo)
    plt.grid(True, linestyle=':', alpha=0.7, color='gray')

    # Plotar gráfico de linha com marcadores circulares
    plt.plot(total, proporcao, 'o-', color='blue', linewidth=1.5,
             label=f'Proporção Acumulada', markersize=3)

    # Adicionar linha horizontal para o valor final
    plt.axhline(y=valor_final, linestyle='--', color='red',
                label=f'Valor Final: {valor_final:.2f}%')

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
    print(f"Gráfico '{nome_arquivo}' gerado.")
    plt.close()

    # Salvar dados resumidos (apenas algumas linhas representativas)
    dados_solucionabilidade = pd.DataFrame({
        'Execucao': total,
        'Solucionaveis_Acumulados': solucionaveis,
        'Proporcao_Acumulada': proporcao
    })

    # Selecionar apenas algumas linhas representativas
    num_linhas = len(dados_solucionabilidade)
    if num_linhas > 20:
        # Primeiras 5, 5 do meio e últimas 5
        indices_selecionados = list(range(5))
        meio = num_linhas // 2
        indices_selecionados.extend(list(range(meio - 2, meio + 3)))
        indices_selecionados.extend(list(range(num_linhas - 5, num_linhas)))
        dados_solucionabilidade_resumidos = dados_solucionabilidade.iloc[indices_selecionados]
    else:
        dados_solucionabilidade_resumidos = dados_solucionabilidade

    return dados_solucionabilidade_resumidos


# Função para análise de movimentos na solução
def grafico_analise_movimentos(df, nome_arquivo="analise_movimentos.png"):
    """
    Cria gráficos separados para análise dos movimentos nas soluções.
    """
    # Filtrar apenas os casos resolvidos
    df_solved = df[df['Found'] == True].copy()

    if df_solved.empty:
        print("Sem soluções encontradas para analisar movimentos.")
        return None

    # Garantir ordem consistente dos algoritmos
    ordem_algoritmos = ['BFS', 'DFS', 'A*']
    algoritmos_presentes = [algo for algo in ordem_algoritmos if algo in df_solved['Algorithm'].unique()]

    # Converter strings de direções em listas se necessário
    if 'DirectionsList' not in df_solved.columns:
        df_solved['DirectionsList'] = df_solved['Directions'].apply(
            lambda x: eval(x) if isinstance(x, str) and x.startswith('[') else []
        )

    # 1. Frequência total de movimentos
    plt.figure(figsize=(10, 7))

    # Contar frequência de movimentos
    movimento_counts = {'direita': 0, 'esquerda': 0, 'cima': 0, 'baixo': 0}

    for directions in df_solved['DirectionsList']:
        for direction in directions:
            if direction in movimento_counts:
                movimento_counts[direction] += 1

    movimentos = list(movimento_counts.keys())
    freq = list(movimento_counts.values())

    # Gráfico de barras para frequência total
    bars = plt.bar(movimentos, freq, color=['#3498db', '#e74c3c', '#2ecc71', '#f39c12'])

    # Adicionar valores acima das barras
    for bar, valor in zip(bars, freq):
        if valor >= 1e6:
            texto = f"{valor / 1e6:.1f}M"
        elif valor >= 1e3:
            texto = f"{valor / 1e3:.1f}K"
        else:
            texto = f"{valor}"
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width() / 2., height + 0.02 * max(freq),
                 texto, ha='center', va='bottom')

    plt.title('Frequência Total de Movimentos')
    plt.ylabel('Número de Ocorrências')
    plt.grid(axis='y', linestyle='--', alpha=0.7)

    plt.tight_layout()
    nome_arquivo_freq = nome_arquivo.replace('.png', '_freq_movimentos.png')
    plt.savefig(nome_arquivo_freq)
    print(f"Gráfico '{nome_arquivo_freq}' gerado.")
    plt.close()

    # 2. Frequência de movimentos por algoritmo
    plt.figure(figsize=(10, 7))

    # Calcular frequência por algoritmo
    movimento_por_algo = {algo: {'direita': 0, 'esquerda': 0, 'cima': 0, 'baixo': 0}
                          for algo in algoritmos_presentes}

    for idx, row in df_solved.iterrows():
        if row['Algorithm'] in movimento_por_algo:  # Verificar se o algoritmo está no dicionário
            for direction in row['DirectionsList']:
                if direction in movimento_por_algo[row['Algorithm']]:
                    movimento_por_algo[row['Algorithm']][direction] += 1

    # Preparar dados para gráfico de barras agrupadas
    x = np.arange(len(movimentos))
    width = 0.25
    multiplier = 0

    # Criar barras para cada algoritmo
    for algo in algoritmos_presentes:
        # Converter dicionário para lista na ordem correta
        valores = [movimento_por_algo[algo][mov] for mov in movimentos]

        offset = width * multiplier
        rects = plt.bar(x + offset, valores, width, label=algo)

        # Adicionar valores nas barras
        for rect, valor in zip(rects, valores):
            if valor >= 1e3:
                texto = f"{valor / 1e3:.1f}K"
            else:
                texto = f"{valor}"
            height = rect.get_height()
            max_height = max([max(movimento_por_algo[a].values()) for a in algoritmos_presentes])
            plt.text(rect.get_x() + rect.get_width() / 2., height + 0.02 * max_height,
                     texto, ha='center', va='bottom', fontsize=8)

        multiplier += 1

    plt.title('Frequência de Movimentos por Algoritmo')
    plt.xticks(x + width, movimentos)
    plt.ylabel('Número de Ocorrências')
    plt.legend(loc='best')
    plt.grid(axis='y', linestyle='--', alpha=0.7)

    plt.tight_layout()
    nome_arquivo_freq_algo = nome_arquivo.replace('.png', '_freq_movimentos_algo.png')
    plt.savefig(nome_arquivo_freq_algo)
    print(f"Gráfico '{nome_arquivo_freq_algo}' gerado.")
    plt.close()

    # 3. Distribuição do tamanho das soluções
    plt.figure(figsize=(10, 7))

    # Calcular comprimento das soluções
    df_solved.loc[:, 'TamanhoSolucao'] = df_solved['DirectionsList'].apply(len)

    # Histograma dos tamanhos de solução
    plt.hist(df_solved['TamanhoSolucao'], bins=15, alpha=0.7, color='#3498db')
    plt.title('Distribuição do Tamanho das Soluções')
    plt.xlabel('Número de Passos')
    plt.ylabel('Frequência')
    plt.grid(True, linestyle='--', alpha=0.7)

    plt.tight_layout()
    nome_arquivo_dist = nome_arquivo.replace('.png', '_dist_tamanho.png')
    plt.savefig(nome_arquivo_dist)
    print(f"Gráfico '{nome_arquivo_dist}' gerado.")
    plt.close()

    # 4. Tamanho médio da solução por algoritmo
    plt.figure(figsize=(10, 7))

    # Calcular tamanho médio por algoritmo
    tamanho_medio = {}
    for algo in algoritmos_presentes:
        df_algo = df_solved[df_solved['Algorithm'] == algo]
        if not df_algo.empty:
            tamanho_medio[algo] = df_algo['TamanhoSolucao'].mean()

    # Gráfico de barras
    if tamanho_medio:  # Verificar se há dados
        cores = ['blue', 'red', 'green'][:len(tamanho_medio)]
        bars = plt.bar(list(tamanho_medio.keys()), list(tamanho_medio.values()), color=cores)

        # Adicionar valores nas barras
        for bar, valor in zip(bars, tamanho_medio.values()):
            plt.text(bar.get_x() + bar.get_width() / 2., valor + 0.5,
                     f"{valor:.1f}", ha='center', va='bottom')

        plt.title('Tamanho Médio da Solução por Algoritmo')
        plt.ylabel('Número Médio de Passos')
        plt.grid(axis='y', linestyle='--', alpha=0.7)

        plt.tight_layout()
        nome_arquivo_tamanho = nome_arquivo.replace('.png', '_tamanho_medio.png')
        plt.savefig(nome_arquivo_tamanho)
        print(f"Gráfico '{nome_arquivo_tamanho}' gerado.")
    else:
        print("Sem dados suficientes para gerar o gráfico de tamanho médio por algoritmo.")

    plt.close()

    print(f"Todos os gráficos de análise de movimentos foram gerados.")

    return True


# Função para analisar desempenho por algoritmo
def analisar_desempenho(df):
    """Analisa o desempenho dos diferentes algoritmos."""
    print("\n===== ANÁLISE DE DESEMPENHO =====")

    # Calcular métricas relevantes por algoritmo
    for algo in df['Algorithm'].unique():
        df_algo = df[df['Algorithm'] == algo]

        print(f"\nAlgoritmo: {algo}")
        print(f"  Taxa de sucesso: {df_algo['Found'].mean() * 100:.2f}%")
        print(f"  Tempo médio: {df_algo['Time'].mean():.6f} segundos")
        print(f"  Nós expandidos (média): {df_algo['Expanded'].mean():.2f}")

        # Para casos bem-sucedidos
        df_success = df_algo[df_algo['Found'] == True]
        if not df_success.empty:
            print(f"  Para casos bem-sucedidos:")
            print(f"    Passos médios: {df_success['Steps'].mean():.2f}")
            print(f"    Tempo médio: {df_success['Time'].mean():.6f} segundos")
            print(f"    Nós expandidos (média): {df_success['Expanded'].mean():.2f}")

        # Consumo de memória
        if 'ConsumoMemoria' in df.columns:
            print(f"  Consumo médio de memória: {df_algo['ConsumoMemoria'].mean():.2f} MB")


# Função principal
def main():
    """Função principal que coordena a análise."""
    print("===== ANÁLISE DE ALGORITMOS PARA 15-PUZZLE =====")

    # Solicitar o caminho do arquivo
    caminho_arquivo = input("Digite o caminho do arquivo CSV (ou pressione Enter para usar 'puzzle_data.csv'): ")
    if not caminho_arquivo:
        caminho_arquivo = 'puzzle_data.csv'

    # Verificar se o arquivo existe
    if not Path(caminho_arquivo).exists():
        print(f"Arquivo '{caminho_arquivo}' não encontrado!")
        return

    # Carregar os dados
    df = carregar_dados(caminho_arquivo)
    if df is None:
        return

    # Realizar análises
    stats = estatisticas_basicas(df)
    analisar_desempenho(df)

    # Gerar visualizações
    print("\n===== GERANDO VISUALIZAÇÕES =====")

    # Importar módulo para manipulação de caminhos
    import os

    # Criar pasta para os resultados
    pasta_resultados = "resultados_analise"
    os.makedirs(pasta_resultados, exist_ok=True)
    print(f"Resultados serão salvos na pasta: {pasta_resultados}")

    # Dicionário para armazenar todos os dados para o arquivo unificado
    todos_dados = {}

    # Garantir ordem consistente dos algoritmos em todos os gráficos
    ordem_algoritmos = ['BFS', 'DFS', 'A*']
    algoritmos_presentes = [algo for algo in ordem_algoritmos if algo in df['Algorithm'].unique()]

    # Evolução temporal dos algoritmos
    # 1. Taxa de Sucesso Acumulada
    plt.figure(figsize=(12, 8))
    df_sorted = df.sort_values(['Algorithm', 'Iteration'])
    for algo in algoritmos_presentes:
        df_algo = df_sorted[df_sorted['Algorithm'] == algo].copy()
        success_count = df_algo['Found'].cumsum()
        total_count = np.arange(1, len(df_algo) + 1)
        success_rate = (success_count / total_count) * 100
        plt.plot(total_count, success_rate, 'o-',
                 color={'BFS': 'blue', 'DFS': 'red', 'A*': 'green'}.get(algo, 'gray'),
                 label=f'{algo} - Final: {success_rate.iloc[-1]:.2f}%', markersize=4)
        plt.axhline(y=success_rate.iloc[-1], linestyle='--',
                    color={'BFS': 'blue', 'DFS': 'red', 'A*': 'green'}.get(algo, 'gray'), alpha=0.7)
    plt.xlabel('Número de Execuções')
    plt.ylabel('Taxa de Sucesso Acumulada (%)')
    plt.title('Análise de Sucesso - Evolução Temporal')
    plt.legend(loc='best')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.ylim(0, 105)
    plt.gca().xaxis.set_major_formatter(ticker.FuncFormatter(formatar_numero))
    plt.tight_layout()
    plt.savefig(os.path.join(pasta_resultados, "evolucao_taxa_sucesso.png"))
    print(f"Gráfico '{os.path.join(pasta_resultados, 'evolucao_taxa_sucesso.png')}' gerado.")
    plt.close()

    # 2. Tempo de Execução
    plt.figure(figsize=(12, 8))
    window_size = min(5, df['Iteration'].nunique())
    for algo in algoritmos_presentes:
        df_algo = df_sorted[df_sorted['Algorithm'] == algo].copy()
        if len(df_algo) >= window_size:
            rolling_time = df_algo['Time'].rolling(window=window_size, min_periods=1).mean()
        else:
            rolling_time = df_algo['Time']
        plt.plot(np.arange(1, len(df_algo) + 1), rolling_time, 'o-',
                 color={'BFS': 'blue', 'DFS': 'red', 'A*': 'green'}.get(algo, 'gray'),
                 label=f'{algo} - Média: {df_algo["Time"].mean():.4f}s', markersize=4)
    plt.xlabel('Número de Execuções')
    plt.ylabel('Tempo de Execução (segundos)')
    plt.title('Desempenho Temporal - Média Móvel')
    plt.legend(loc='best')
    plt.grid(True, linestyle='--', alpha=0.7)
    if df['Time'].max() / df['Time'].min() > 100:
        plt.yscale('log')
        plt.ylabel('Tempo de Execução (segundos) - Escala Log')
    plt.gca().xaxis.set_major_formatter(ticker.FuncFormatter(formatar_numero))
    plt.tight_layout()
    plt.savefig(os.path.join(pasta_resultados, "evolucao_tempo.png"))
    print(f"Gráfico '{os.path.join(pasta_resultados, 'evolucao_tempo.png')}' gerado.")
    plt.close()

    # Salvar dados usados
    dados_evolucao = df.sort_values(['Algorithm', 'Iteration'])[
        ['Algorithm', 'Iteration', 'Time', 'Found', 'Expanded', 'Steps']]
    todos_dados['evolucao_temporal'] = dados_evolucao.head(20).to_string()  # Primeiras 20 linhas apenas

    # Comparativo entre algoritmos
    # 1. Tempo Médio
    plt.figure(figsize=(10, 7))
    tempos = [df[df['Algorithm'] == algo]['Time'].mean() for algo in algoritmos_presentes]
    cores = ['blue', 'red', 'green'][:len(algoritmos_presentes)]
    bars = plt.bar(algoritmos_presentes, tempos, color=cores)
    for bar, valor in zip(bars, tempos):
        if valor < 0.01:
            texto = f"{valor:.4f}s"
        elif valor < 0.1:
            texto = f"{valor:.3f}s"
        else:
            texto = f"{valor:.2f}s"
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width() / 2., height + 0.05 * max(tempos),
                 f"{texto}", ha='center', va='bottom', rotation=0)
    plt.title('Tempo Médio de Execução por Algoritmo')
    plt.ylabel('Tempo (segundos)')
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    if max(tempos) / min(tempos) > 100:
        plt.yscale('log')
        plt.ylabel('Tempo (segundos) - Escala Log')
    plt.tight_layout()
    plt.savefig(os.path.join(pasta_resultados, "comparativo_tempo_medio.png"))
    print(f"Gráfico '{os.path.join(pasta_resultados, 'comparativo_tempo_medio.png')}' gerado.")
    plt.close()

    # 2. Nós Expandidos
    plt.figure(figsize=(10, 7))
    nos = [df[df['Algorithm'] == algo]['Expanded'].mean() for algo in algoritmos_presentes]
    bars = plt.bar(algoritmos_presentes, nos, color=cores)
    for bar, valor in zip(bars, nos):
        if valor >= 1e6:
            texto = f"{valor / 1e6:.1f}M"
        elif valor >= 1e3:
            texto = f"{valor / 1e3:.1f}K"
        else:
            texto = f"{valor:.0f}"
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width() / 2., height + 0.05 * max(nos),
                 f"{texto}", ha='center', va='bottom', rotation=0)
    plt.title('Média de Nós Expandidos por Algoritmo')
    plt.ylabel('Nós Expandidos')
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.yscale('log')
    plt.gca().yaxis.set_major_formatter(ticker.FuncFormatter(formatar_numero))
    plt.tight_layout()
    plt.savefig(os.path.join(pasta_resultados, "comparativo_nos_expandidos.png"))
    print(f"Gráfico '{os.path.join(pasta_resultados, 'comparativo_nos_expandidos.png')}' gerado.")
    plt.close()

    # Salvar dados comparativos
    dados_comparativos = {}
    for algo in algoritmos_presentes:
        dados_comparativos[algo] = {
            'tempo_medio': df[df['Algorithm'] == algo]['Time'].mean(),
            'nos_expandidos': df[df['Algorithm'] == algo]['Expanded'].mean(),
            'taxa_sucesso': df[df['Algorithm'] == algo]['Found'].mean() * 100
        }
        df_solved = df[(df['Algorithm'] == algo) & (df['Found'] == True)]
        if not df_solved.empty:
            dados_comparativos[algo]['passos_medios'] = df_solved['Steps'].mean()

    todos_dados['comparativos'] = str(dados_comparativos)

    # Análise de solucionabilidade
    if 'Solvable' in df.columns:
        # Verificar se a coluna 'Solvable' está no DataFrame
        df_sorted = df.sort_values(['Iteration'])
        df_sorted['Solvable_Num'] = df_sorted['Solvable'].astype(int)
        solucionaveis = df_sorted['Solvable_Num'].cumsum()
        total = np.arange(1, len(df_sorted) + 1)
        proporcao = (solucionaveis / total) * 100
        if isinstance(proporcao, pd.Series):
            valor_final = proporcao.iloc[-1]
        else:
            # If proporcao is a scalar (numpy.float64), use it directly
            valor_final = proporcao

        plt.figure(figsize=(12, 8))
        plt.title('Análise de Solucionabilidade - Evolução Temporal', fontsize=16)
        plt.xlabel('Número de Execuções', fontsize=12)
        plt.ylabel('Porcentagem Acumulada de Tabuleiros Solucionáveis', fontsize=12)
        plt.grid(True, linestyle=':', alpha=0.7, color='gray')
        plt.plot(total, proporcao, 'o-', color='blue', linewidth=1.5,
                 label=f'Proporção Acumulada', markersize=3)
        plt.axhline(y=valor_final, linestyle='--', color='red',
                    label=f'Valor Final: {valor_final:.2f}%')
        plt.xlim(0, len(total))
        plt.ylim(0, 85)
        plt.gca().xaxis.set_major_formatter(ticker.FuncFormatter(formatar_numero))
        plt.legend(loc='upper right', fontsize=10)
        plt.tight_layout()
        plt.savefig(os.path.join(pasta_resultados, "analise_solucionabilidade.png"))
        print(f"Gráfico '{os.path.join(pasta_resultados, 'analise_solucionabilidade.png')}' gerado.")
        plt.close()

        # Salvar dados resumidos (apenas algumas linhas representativas)
        dados_solucionabilidade = pd.DataFrame({
            'Execucao': total,
            'Solucionaveis_Acumulados': solucionaveis,
            'Proporcao_Acumulada': proporcao
        })

        # Selecionar apenas algumas linhas representativas
        num_linhas = len(dados_solucionabilidade)
        if num_linhas > 20:
            # Primeiras 5, 5 do meio e últimas 5
            indices_selecionados = list(range(5))
            meio = num_linhas // 2
            indices_selecionados.extend(list(range(meio - 2, meio + 3)))
            indices_selecionados.extend(list(range(num_linhas - 5, num_linhas)))
            dados_solucionabilidade_resumidos = grafico_solucionabilidade(df, os.path.join(pasta_resultados,
                                                                                           "analise_solucionabilidade.png"))
        else:
            dados_solucionabilidade_resumidos = dados_solucionabilidade

        todos_dados['solucionabilidade'] = dados_solucionabilidade_resumidos.to_string()

    # Análise de movimentos
    df_solved = df[df['Found'] == True].copy()
    if not df_solved.empty:
        if 'DirectionsList' not in df_solved.columns:
            df_solved['DirectionsList'] = df_solved['Directions'].apply(
                lambda x: eval(x) if isinstance(x, str) and x.startswith('[') else []
            )

        # 1. Frequência total de movimentos
        movimento_counts = {'direita': 0, 'esquerda': 0, 'cima': 0, 'baixo': 0}
        for directions in df_solved['DirectionsList']:
            for direction in directions:
                if direction in movimento_counts:
                    movimento_counts[direction] += 1

        plt.figure(figsize=(10, 7))
        movimentos = list(movimento_counts.keys())
        freq = list(movimento_counts.values())
        bars = plt.bar(movimentos, freq, color=['#3498db', '#e74c3c', '#2ecc71', '#f39c12'])
        for bar, valor in zip(bars, freq):
            if valor >= 1e6:
                texto = f"{valor / 1e6:.1f}M"
            elif valor >= 1e3:
                texto = f"{valor / 1e3:.1f}K"
            else:
                texto = f"{valor}"
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width() / 2., height + 0.02 * max(freq),
                     texto, ha='center', va='bottom')
        plt.title('Frequência Total de Movimentos')
        plt.ylabel('Número de Ocorrências')
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        plt.tight_layout()
        plt.savefig(os.path.join(pasta_resultados, "movimentos_frequencia_total.png"))
        print(f"Gráfico '{os.path.join(pasta_resultados, 'movimentos_frequencia_total.png')}' gerado.")
        plt.close()

        # Salvar dados de movimentos
        movimento_por_algo = {}
        for algo in algoritmos_presentes:
            movimento_por_algo[algo] = {'direita': 0, 'esquerda': 0, 'cima': 0, 'baixo': 0}
            df_algo = df_solved[df_solved['Algorithm'] == algo]
            for idx, row in df_algo.iterrows():
                for direction in row['DirectionsList']:
                    if direction in movimento_por_algo[algo]:
                        movimento_por_algo[algo][direction] += 1

        # Tamanho das soluções
        df_solved.loc[:, 'TamanhoSolucao'] = df_solved['DirectionsList'].apply(len)
        tamanho_medio = {}
        for algo in algoritmos_presentes:
            df_algo = df_solved[df_solved['Algorithm'] == algo]
            if not df_algo.empty:
                tamanho_medio[algo] = df_algo['TamanhoSolucao'].mean()

        dados_movimentos = {
            'movimento_total': movimento_counts,
            'movimento_por_algoritmo': movimento_por_algo,
            'tamanho_medio_solucao': tamanho_medio
        }
        todos_dados['movimentos'] = str(dados_movimentos)

    # Análise de consumo de memória
    if 'MemMBFim' in df.columns and 'MemMBInicio' in df.columns:
        # Criar cópia para análise
        df_mem = df.copy()
        # Calcular diferentes métricas de memória
        df_mem['ConsumoMemoria'] = df_mem['MemMBFim'] - df_mem['MemMBInicio']
        df_mem['ConsumoMemoriaAbs'] = abs(df_mem['ConsumoMemoria'])
        df_mem['PicoMemoria'] = df_mem[['MemMBInicio', 'MemMBFim']].max(axis=1)

        # Gráfico de pico de memória
        plt.figure(figsize=(10, 7))

        # Calcular estatísticas de pico por algoritmo
        pico_por_algo = {}
        for algo in algoritmos_presentes:
            df_algo = df_mem[df_mem['Algorithm'] == algo]
            if not df_algo.empty:
                pico_por_algo[algo] = {
                    'mean': df_algo['PicoMemoria'].mean(),
                    'max': df_algo['PicoMemoria'].max(),
                    'min': df_algo['PicoMemoria'].min()
                }

        # Criar barras para valores médios
        valores_medios = [pico_por_algo[algo]['mean'] for algo in algoritmos_presentes]
        cores = ['blue', 'red', 'green'][:len(algoritmos_presentes)]
        bars = plt.bar(algoritmos_presentes, valores_medios, color=cores, alpha=0.7)

        # Adicionar valores nas barras
        for bar, valor in zip(bars, valores_medios):
            plt.text(bar.get_x() + bar.get_width() / 2., valor + 0.5,
                     f"{valor:.2f} MB", ha='center', va='bottom')

        # Adicionar linhas de erro min-max
        for i, algo in enumerate(algoritmos_presentes):
            plt.vlines(x=i,
                       ymin=pico_por_algo[algo]['min'],
                       ymax=pico_por_algo[algo]['max'],
                       color='black', linewidth=2)

        plt.title('Pico de Consumo de Memória por Algoritmo')
        plt.ylabel('Memória (MB)')
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        max_val = max([pico_por_algo[algo]['max'] for algo in algoritmos_presentes])
        plt.ylim(0, max_val * 1.2)

        plt.tight_layout()
        plt.savefig(os.path.join(pasta_resultados, 'pico_memoria.png'))
        print(f"Gráfico '{os.path.join(pasta_resultados, 'pico_memoria.png')}' gerado.")
        plt.close()

        # Salvar dados de memória
        dados_memoria = {
            'consumo_original': {algo: df_mem[df_mem['Algorithm'] == algo]['ConsumoMemoria'].mean()
                                 for algo in algoritmos_presentes},
            'consumo_absoluto': {algo: df_mem[df_mem['Algorithm'] == algo]['ConsumoMemoriaAbs'].mean()
                                 for algo in algoritmos_presentes},
            'pico_memoria': pico_por_algo
        }
        todos_dados['memoria'] = str(dados_memoria)

    # Salvar todos os dados em um único arquivo de texto estruturado para análise por outra LLM
    with open(os.path.join(pasta_resultados, 'dados_analise_15puzzle.txt'), 'w') as f:
        f.write("# ANÁLISE DE ALGORITMOS PARA RESOLUÇÃO DO 15-PUZZLE\n\n")

        # Metadados gerais
        f.write("## METADADOS\n")
        f.write(f"- Data da análise: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}\n")
        f.write(f"- Total de execuções analisadas: {len(df)}\n")
        f.write(f"- Algoritmos analisados: {', '.join(algoritmos_presentes)}\n")
        f.write(f"- Iterações: {df['Iteration'].nunique()}\n\n")

        # Resumo geral
        f.write("## RESUMO EXECUTIVO\n")
        for algo in algoritmos_presentes:
            f.write(f"### {algo}\n")
            tempo_medio = df[df['Algorithm'] == algo]['Time'].mean()
            nos_medio = df[df['Algorithm'] == algo]['Expanded'].mean()
            taxa_sucesso = df[df['Algorithm'] == algo]['Found'].mean() * 100

            # Formatação adequada para valores grandes
            if nos_medio >= 1e6:
                nos_formatado = f"{nos_medio / 1e6:.2f} milhões"
            elif nos_medio >= 1e3:
                nos_formatado = f"{nos_medio / 1e3:.2f} mil"
            else:
                nos_formatado = f"{nos_medio:.2f}"

            # Formato para tempo
            if tempo_medio < 0.01:
                tempo_formatado = f"{tempo_medio:.6f}"
            elif tempo_medio < 0.1:
                tempo_formatado = f"{tempo_medio:.4f}"
            else:
                tempo_formatado = f"{tempo_medio:.2f}"

            f.write(f"- Tempo médio: {tempo_formatado} segundos\n")
            f.write(f"- Nós expandidos: {nos_formatado}\n")
            f.write(f"- Taxa de sucesso: {taxa_sucesso:.2f}%\n")

            df_success = df[(df['Algorithm'] == algo) & (df['Found'] == True)]
            if not df_success.empty:
                passos_medios = df_success['Steps'].mean()
                f.write(f"- Passos médios na solução: {passos_medios:.2f}\n")

                # Eficiência
                eficiencia = df_success['Expanded'].mean() / passos_medios
                f.write(f"- Eficiência (nós/passo): {eficiencia:.2f}\n")

            # Consumo de memória se disponível
            if 'PicoMemoria' in df.columns:
                memoria_media = df[df['Algorithm'] == algo]['PicoMemoria'].mean()
                f.write(f"- Consumo de memória médio: {memoria_media:.2f} MB\n")

            f.write("\n")

        # Análise comparativa
        f.write("## ANÁLISE COMPARATIVA\n")

        # 1. Tempo de execução
        f.write("### Tempo de Execução\n")
        tempos_por_algo = {algo: df[df['Algorithm'] == algo]['Time'].mean() for algo in algoritmos_presentes}
        algoritmo_mais_rapido = min(tempos_por_algo.items(), key=lambda x: x[1])[0]
        algoritmo_mais_lento = max(tempos_por_algo.items(), key=lambda x: x[1])[0]
        proporcao = tempos_por_algo[algoritmo_mais_lento] / tempos_por_algo[algoritmo_mais_rapido]

        f.write(
            f"- Algoritmo mais rápido: {algoritmo_mais_rapido} ({tempos_por_algo[algoritmo_mais_rapido]:.6f} segundos)\n")
        f.write(
            f"- Algoritmo mais lento: {algoritmo_mais_lento} ({tempos_por_algo[algoritmo_mais_lento]:.6f} segundos)\n")
        f.write(f"- O algoritmo {algoritmo_mais_lento} é {proporcao:.2f}x mais lento que o {algoritmo_mais_rapido}\n\n")

        # 2. Nós expandidos
        f.write("### Nós Expandidos\n")
        nos_por_algo = {algo: df[df['Algorithm'] == algo]['Expanded'].mean() for algo in algoritmos_presentes}
        algoritmo_menos_nos = min(nos_por_algo.items(), key=lambda x: x[1])[0]
        algoritmo_mais_nos = max(nos_por_algo.items(), key=lambda x: x[1])[0]
        proporcao_nos = nos_por_algo[algoritmo_mais_nos] / nos_por_algo[algoritmo_menos_nos]

        # Formatação para exibição
        def formatar_numero_texto(valor):
            if valor >= 1e6:
                return f"{valor / 1e6:.2f} milhões"
            elif valor >= 1e3:
                return f"{valor / 1e3:.2f} mil"
            else:
                return f"{valor:.2f}"

        f.write(
            f"- Algoritmo com menos nós expandidos: {algoritmo_menos_nos} ({formatar_numero_texto(nos_por_algo[algoritmo_menos_nos])})\n")
        f.write(
            f"- Algoritmo com mais nós expandidos: {algoritmo_mais_nos} ({formatar_numero_texto(nos_por_algo[algoritmo_mais_nos])})\n")
        f.write(
            f"- O algoritmo {algoritmo_mais_nos} expande {proporcao_nos:.2f}x mais nós que o {algoritmo_menos_nos}\n\n")

        # 3. Taxa de sucesso
        f.write("### Taxa de Sucesso\n")
        taxas_por_algo = {algo: df[df['Algorithm'] == algo]['Found'].mean() * 100 for algo in algoritmos_presentes}
        for algo, taxa in taxas_por_algo.items():
            f.write(f"- {algo}: {taxa:.2f}%\n")
        f.write("\n")

        # 4. Eficiência (nós/passo)
        f.write("### Eficiência\n")
        eficiencia_por_algo = {}
        for algo in algoritmos_presentes:
            df_success = df[(df['Algorithm'] == algo) & (df['Found'] == True)]
            if not df_success.empty and df_success['Steps'].mean() > 0:
                eficiencia = df_success['Expanded'].mean() / df_success['Steps'].mean()
                eficiencia_por_algo[algo] = eficiencia

        if eficiencia_por_algo:
            algoritmo_mais_eficiente = min(eficiencia_por_algo.items(), key=lambda x: x[1])[0]
            algoritmo_menos_eficiente = max(eficiencia_por_algo.items(), key=lambda x: x[1])[0]

            f.write(
                f"- Algoritmo mais eficiente: {algoritmo_mais_eficiente} ({formatar_numero_texto(eficiencia_por_algo[algoritmo_mais_eficiente])} nós/passo)\n")
            f.write(
                f"- Algoritmo menos eficiente: {algoritmo_menos_eficiente} ({formatar_numero_texto(eficiencia_por_algo[algoritmo_menos_eficiente])} nós/passo)\n\n")

        # Análise de movimentos
        if 'movimentos' in todos_dados:
            f.write("## ANÁLISE DE MOVIMENTOS\n")

            # Frequência de movimentos
            f.write("### Frequência Total de Movimentos\n")
            for direcao, freq in movimento_counts.items():
                f.write(f"- {direcao.capitalize()}: {freq}\n")
            f.write("\n")

            # Movimentos por algoritmo
            f.write("### Movimentos por Algoritmo\n")
            for algo in algoritmos_presentes:
                if algo in movimento_por_algo:
                    f.write(f"#### {algo}\n")
                    for direcao, freq in movimento_por_algo[algo].items():
                        f.write(f"- {direcao.capitalize()}: {freq}\n")
                    f.write("\n")

            # Tamanho médio das soluções
            if tamanho_medio:
                f.write("### Tamanho Médio das Soluções\n")
                for algo, tamanho in tamanho_medio.items():
                    f.write(f"- {algo}: {tamanho:.2f} passos\n")
                f.write("\n")

        # Análise de solucionabilidade se disponível
        if 'Solvable' in df.columns:
            f.write("## ANÁLISE DE SOLUCIONABILIDADE\n")
            proporcao_final = valor_final
            f.write(f"- Proporção final de tabuleiros solucionáveis: {proporcao_final:.2f}%\n")
            f.write(f"- Total de tabuleiros solucionáveis: {solucionaveis.iloc[-1]}\n")
            f.write(f"- Total de tabuleiros analisados: {len(df)}\n\n")

            # Adicionar algumas observações sobre a evolução da proporção
            if isinstance(proporcao, pd.Series) and len(proporcao) > 10:
                inicio = proporcao.iloc[9]  # Após 10 execuções
                meio = proporcao.iloc[len(proporcao) // 2]
                f.write("### Evolução da Proporção\n")
                f.write(f"- Após 10 execuções: {inicio:.2f}%\n")
                f.write(f"- No meio da análise: {meio:.2f}%\n")
                f.write(f"- No final: {proporcao_final:.2f}%\n\n")

                # Verificar estabilidade
                if abs(proporcao_final - meio) < 1:
                    f.write("- Observação: A proporção de tabuleiros solucionáveis se estabilizou rapidamente.\n\n")

        # Análise de consumo de memória
        if 'MemMBFim' in df.columns and 'MemMBInicio' in df.columns:
            f.write("## ANÁLISE DE CONSUMO DE MEMÓRIA\n")

            # Adicionar nota sobre valores negativos se existirem
            negativos = df_mem[df_mem['ConsumoMemoria'] < 0].shape[0]
            total = df_mem.shape[0]
            if negativos > 0:
                f.write("### Nota sobre Valores Negativos\n")
                f.write(
                    f"- {negativos} de {total} execuções ({(negativos / total) * 100:.2f}%) apresentaram valores negativos de consumo de memória.\n")
                f.write(
                    "- Possíveis explicações: liberação de memória pelo sistema durante a execução, imprecisão na medição, ou processos concorrentes.\n")
                f.write(
                    "- Para uma análise mais confiável, são apresentados também valores absolutos e pico de memória.\n\n")

            # Consumo original
            f.write("### Consumo de Memória (Original)\n")
            for algo, valor in dados_memoria['consumo_original'].items():
                f.write(f"- {algo}: {valor:.2f} MB\n")
            f.write("\n")

            # Consumo absoluto
            f.write("### Consumo de Memória (Valor Absoluto)\n")
            for algo, valor in dados_memoria['consumo_absoluto'].items():
                f.write(f"- {algo}: {valor:.2f} MB\n")
            f.write("\n")

            # Pico de memória
            f.write("### Pico de Consumo de Memória\n")
            for algo, dados in pico_por_algo.items():
                f.write(f"#### {algo}\n")
                f.write(f"- Média: {dados['mean']:.2f} MB\n")
                f.write(f"- Máximo: {dados['max']:.2f} MB\n")
                f.write(f"- Mínimo: {dados['min']:.2f} MB\n")
                f.write("\n")

        # Conclusões e insights
        f.write("## CONCLUSÕES E INSIGHTS\n")

        # Algoritmo de melhor desempenho geral
        f.write("### Algoritmo com Melhor Desempenho Geral\n")
        # Vamos determinar isso com base em um ranking simples considerando tempo, nós e taxa de sucesso
        ranking = {}
        for algo in algoritmos_presentes:
            ranking[algo] = 0

        # Tempo: quanto menor, melhor
        tempo_ranking = sorted(tempos_por_algo.items(), key=lambda x: x[1])
        for i, (algo, _) in enumerate(tempo_ranking):
            ranking[algo] += (len(algoritmos_presentes) - i)  # Mais pontos para os melhores

        # Nós: quanto menor, melhor
        nos_ranking = sorted(nos_por_algo.items(), key=lambda x: x[1])
        for i, (algo, _) in enumerate(nos_ranking):
            ranking[algo] += (len(algoritmos_presentes) - i)

        # Taxa de sucesso: quanto maior, melhor
        sucesso_ranking = sorted(taxas_por_algo.items(), key=lambda x: x[1], reverse=True)
        for i, (algo, _) in enumerate(sucesso_ranking):
            ranking[algo] += (len(algoritmos_presentes) - i)

        # Determinar o algoritmo com melhor ranking geral
        melhor_algoritmo = max(ranking.items(), key=lambda x: x[1])[0]

        f.write(f"Considerando os critérios de tempo de execução, número de nós expandidos e taxa de sucesso, ")
        f.write(f"o algoritmo {melhor_algoritmo} apresentou o melhor desempenho geral nesta análise.\n\n")

        # Comparações específicas
        f.write("### Comparações Importantes\n")

        # BFS vs DFS
        if 'BFS' in algoritmos_presentes and 'DFS' in algoritmos_presentes:
            f.write("#### BFS vs DFS\n")
            f.write(f"- Tempo: BFS é {tempos_por_algo['DFS'] / tempos_por_algo['BFS']:.2f}x mais rápido que DFS\n")
            f.write(
                f"- Nós expandidos: BFS expande {nos_por_algo['DFS'] / nos_por_algo['BFS']:.2f}x menos nós que DFS\n")
            f.write(f"- Taxa de sucesso: BFS={taxas_por_algo['BFS']:.2f}%, DFS={taxas_por_algo['DFS']:.2f}%\n\n")

        # BFS vs A*
        if 'BFS' in algoritmos_presentes and 'A*' in algoritmos_presentes:
            f.write("#### BFS vs A*\n")
            f.write(f"- Tempo: A* é {tempos_por_algo['BFS'] / tempos_por_algo['A*']:.2f}x mais rápido que BFS\n")
            f.write(f"- Nós expandidos: A* expande {nos_por_algo['BFS'] / nos_por_algo['A*']:.2f}x menos nós que BFS\n")
            f.write(f"- Taxa de sucesso: BFS={taxas_por_algo['BFS']:.2f}%, A*={taxas_por_algo['A*']:.2f}%\n\n")

        # DFS vs A*
        if 'DFS' in algoritmos_presentes and 'A*' in algoritmos_presentes:
            f.write("#### DFS vs A*\n")
            f.write(f"- Tempo: A* é {tempos_por_algo['DFS'] / tempos_por_algo['A*']:.2f}x mais rápido que DFS\n")
            f.write(f"- Nós expandidos: A* expande {nos_por_algo['DFS'] / nos_por_algo['A*']:.2f}x menos nós que DFS\n")
            f.write(f"- Taxa de sucesso: DFS={taxas_por_algo['DFS']:.2f}%, A*={taxas_por_algo['A*']:.2f}%\n\n")

        # Conclusão final
        f.write("### Conclusão Final\n")

        # Esta parte teria que ser customizada com base nos resultados,
        # mas aqui é feita uma análise geral
        if 'A*' in algoritmos_presentes:
            if melhor_algoritmo == 'A*':
                f.write("O algoritmo A* demonstrou ser a melhor escolha para resolver o problema do 15-puzzle, ")
                f.write("apresentando maior eficiência em termos de tempo de execução, número de nós expandidos ")
                f.write("e qualidade das soluções encontradas. Isto ocorre devido à sua capacidade de utilizar ")
                f.write(
                    "heurísticas que direcionam a busca, reduzindo significativamente o espaço de estados a ser explorado.\n\n")
            else:
                f.write(
                    f"Apesar das expectativas teóricas, o algoritmo {melhor_algoritmo} apresentou desempenho superior ao A* ")
                f.write(
                    "neste conjunto específico de dados. Isto pode estar relacionado a características particulares dos ")
                f.write("tabuleiros analisados ou à implementação dos algoritmos.\n\n")
        else:
            f.write(
                f"O algoritmo {melhor_algoritmo} demonstrou ser a melhor escolha para resolver o problema do 15-puzzle ")
            f.write("no conjunto de dados analisado, considerando os critérios de tempo de execução, ")
            f.write("número de nós expandidos e taxa de sucesso.\n\n")

        f.write("## DADOS PARA CONTEXTUALIZAÇÃO\n")
        f.write("Os dados acima são derivados da análise de múltiplas execuções dos algoritmos BFS, DFS e A* ")
        f.write("aplicados ao problema do 15-puzzle. Estas métricas incluem tempo de execução, nós expandidos, ")
        f.write("taxa de sucesso, passos na solução, movimentos realizados e consumo de memória. ")
        f.write("A análise foi realizada em diferentes configurações iniciais do tabuleiro, permitindo uma ")
        f.write("avaliação abrangente do desempenho relativo dos algoritmos.\n")

    print(f"\nDados de análise completos salvos em '{os.path.join(pasta_resultados, 'dados_analise_15puzzle.txt')}'")
    print("\nTodos os gráficos e dados foram gerados com sucesso!")

    print("\n===== CONCLUSÕES =====")
    # Determinar o algoritmo mais rápido
    tempo_medio = df.groupby('Algorithm')['Time'].mean()
    algoritmo_mais_rapido = tempo_medio.idxmin()

    # Formatar o valor para exibição
    if tempo_medio.min() < 0.01:
        valor_formatado = f"{tempo_medio.min():.6f}"
    elif tempo_medio.min() < 0.1:
        valor_formatado = f"{tempo_medio.min():.4f}"
    else:
        valor_formatado = f"{tempo_medio.min():.2f}"

    print(f"Algoritmo mais rápido: {algoritmo_mais_rapido} (tempo médio: {valor_formatado} segundos)")

    # Algoritmo mais eficiente (menos nós expandidos)
    nos_medio = df.groupby('Algorithm')['Expanded'].mean()
    algoritmo_mais_eficiente = nos_medio.idxmin()

    # Formatação para números grandes
    if nos_medio.min() >= 1e6:
        valor_formatado = f"{nos_medio.min() / 1e6:.2f} milhões"
    elif nos_medio.min() >= 1e3:
        valor_formatado = f"{nos_medio.min() / 1e3:.2f} mil"
    else:
        valor_formatado = f"{nos_medio.min():.2f}"

    print(f"Algoritmo mais eficiente: {algoritmo_mais_eficiente} (média de nós expandidos: {valor_formatado})")

    # Taxa de sucesso
    taxa_sucesso = df.groupby('Algorithm')['Found'].mean() * 100
    print("\nTaxa de sucesso por algoritmo:")
    for algo, taxa in taxa_sucesso.items():
        print(f"  {algo}: {taxa:.2f}%")

    print("\nAnálise concluída! Os resultados visuais estão disponíveis nos arquivos PNG gerados.")


if __name__ == "__main__":
    main()