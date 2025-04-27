import matplotlib.pyplot as plt
import pandas as pd
import glob
import re
import os
import numpy as np


# Função para ler os arquivos de resultados na pasta de execução
def ler_dados_relatorio():
    # Lista todos os arquivos de dados na pasta atual
    arquivos = glob.glob('dados_analise_15puzzle-*.txt')
    
    # Lista para armazenar os dados de cada arquivo
    dados_completos = []

    # Iterar sobre os arquivos encontrados
    for arquivo in arquivos:
        try:
            with open(arquivo, 'r') as f:
                conteudo = f.read()

                # Verificar se o arquivo foi lido corretamente
                if not conteudo:
                    print(f"Conteúdo vazio ou erro ao ler o arquivo {arquivo}.")
                    continue

                # Extrair os dados relevantes usando expressões regulares
                dados = {
                    "config": os.path.basename(arquivo).split('.')[0],
                    # Usar o nome do arquivo para identificar a configuração
                }
                
                # Extrair dados para cada algoritmo
                for algoritmo in ["BFS", "DFS", "A*"]:
                    # Tempo médio
                    tempo = extrair_valor(conteudo, r"Tempo médio: (\d+\.\d+) segundos", algoritmo)
                    dados[f"tempo_{algoritmo.replace('*', 'star')}"] = tempo
                    
                    # Nós expandidos - com tratamento especial para os padrões diferentes
                    nos_padrao1 = extrair_valor(conteudo, r"Nós expandidos: (\d+\.\d+) mil", algoritmo)
                    nos_padrao2 = extrair_valor(conteudo, r"Nós expandidos: (\d+\.\d+) milhões", algoritmo)
                    nos_padrao3 = extrair_valor(conteudo, r"Nós expandidos: (\d+\.\d+)(?!\s*mil|\s*milhões)", algoritmo)
                    
                    # Verifica se os valores são None antes de fazer operações
                    if nos_padrao1 is not None:
                        dados[f"nos_{algoritmo.replace('*', 'star')}"] = nos_padrao1 * 1000
                    elif nos_padrao2 is not None:
                        dados[f"nos_{algoritmo.replace('*', 'star')}"] = nos_padrao2 * 1000000
                    elif nos_padrao3 is not None:
                        dados[f"nos_{algoritmo.replace('*', 'star')}"] = nos_padrao3
                    else:
                        # Se todos os padrões falharem, tenta um regex mais genérico
                        nos_generico = extrair_valor(conteudo, r"Nós expandidos:?\s*(\d+\.?\d*)", algoritmo)
                        if nos_generico is not None:
                            dados[f"nos_{algoritmo.replace('*', 'star')}"] = nos_generico
                        else:
                            print(f"Não foi possível extrair nós expandidos para {algoritmo} no arquivo {arquivo}")
                            dados[f"nos_{algoritmo.replace('*', 'star')}"] = None
                    
                    # Taxa de sucesso
                    dados[f"taxa_sucesso_{algoritmo.replace('*', 'star')}"] = extrair_valor(conteudo, r"Taxa de sucesso: (\d+\.\d+)%", algoritmo)
                    
                    # Eficiência
                    dados[f"eficiencia_{algoritmo.replace('*', 'star')}"] = extrair_valor(conteudo, r"Eficiência \(nós/passo\): (\d+\.\d+)", algoritmo)
                    
                    # Consumo de memória
                    dados[f"memoria_{algoritmo.replace('*', 'star')}"] = extrair_valor(conteudo, r"Consumo de Memória \(Valor Absoluto\): (\d+\.\d+)", algoritmo)

                dados_completos.append(dados)
                print(f"Arquivo {arquivo} processado com sucesso!")
        except Exception as e:
            print(f"Erro ao processar o arquivo {arquivo}: {e}")

    # Verificar se há dados antes de criar o DataFrame
    if not dados_completos:
        print("Nenhum dado foi extraído dos arquivos.")
        return pd.DataFrame()
        
    df = pd.DataFrame(dados_completos)
    print(f"Total de {len(df)} configurações processadas.")
    return df


# Função para extrair valor usando expressão regular
def extrair_valor(conteudo, padrao, algoritmo):
    try:
        # Encontrar a seção do algoritmo no conteúdo
        secoes = conteudo.split('###')
        secao_algoritmo = None
        
        for secao in secoes:
            if algoritmo in secao:
                secao_algoritmo = secao
                break
        
        # Se encontrou a seção, busca o padrão na seção
        if secao_algoritmo:
            resultado = re.search(padrao, secao_algoritmo)
            if resultado:
                return float(resultado.group(1))
        
        # Se não encontrou na seção específica, tenta em todo o conteúdo próximo ao nome do algoritmo
        partes = conteudo.split(algoritmo)
        for parte in partes[1:]:  # Ignora a primeira parte (antes da primeira menção ao algoritmo)
            resultado = re.search(padrao, parte[:500])  # Limita a busca aos primeiros 500 caracteres após o nome do algoritmo
            if resultado:
                return float(resultado.group(1))
                
        return None
    except Exception as e:
        print(f"Erro ao extrair valor para {algoritmo} com padrão {padrao}: {e}")
        return None


# Função para simplificar o nome da configuração
def simplificar_config(config):
    # Extrair apenas os números da configuração (ex: "dados_analise_15puzzle-5-30-20" -> "5-30-20")
    match = re.search(r'15puzzle-(\d+-\d+-\d+)', config)
    if match:
        return match.group(1)
    return config


# Função para gerar gráficos comparativos
def gerar_graficos_comparativos(df):
    if df.empty:
        print("Nenhum dado disponível para gerar gráficos.")
        return

    # Simplificar os nomes das configurações para a legenda
    df['config_simplificada'] = df['config'].apply(simplificar_config)

    # Certifique-se que estamos trabalhando apenas com dados numéricos válidos
    for coluna in df.columns:
        if coluna != 'config' and coluna != 'config_simplificada':
            df[coluna] = pd.to_numeric(df[coluna], errors='coerce')

    # Configuração para posicionar as barras lado a lado
    config_list = df['config_simplificada'].tolist()
    x = range(len(config_list))  # Posições no eixo x
    width = 0.25  # Largura de cada barra
    
    # Função auxiliar para substituir zeros e valores negativos por um valor mínimo para escala log
    def prepare_for_log(values, min_value=0.0000001):
        return [max(abs(v), min_value) if pd.notna(v) else min_value for v in values]
    
    # Gráfico de Tempo de Execução (escala logarítmica)
    fig, ax = plt.subplots(figsize=(12, 7))
    tempo_bfs = prepare_for_log(df['tempo_BFS'])
    tempo_dfs = prepare_for_log(df['tempo_DFS'])
    tempo_astar = prepare_for_log(df['tempo_Astar'])
    
    ax.bar([i - width for i in x], tempo_bfs, width=width, label='BFS')
    ax.bar(x, tempo_dfs, width=width, label='DFS')
    ax.bar([i + width for i in x], tempo_astar, width=width, label='A*')
    
    ax.set_title('Tempo de Execução por Configuração (escala logarítmica)')
    ax.set_xlabel('Configuração')
    ax.set_ylabel('Tempo de Execução (segundos) - log scale')
    ax.set_yscale('log')
    ax.set_xticks(x)
    ax.set_xticklabels(config_list, rotation=45)
    ax.legend()
    plt.tight_layout()
    plt.savefig('grafico_comparativo_execucao_log.png')
    plt.close()
    
    # Versão não-logarítmica para comparação
    fig, ax = plt.subplots(figsize=(12, 7))
    ax.bar([i - width for i in x], df['tempo_BFS'], width=width, label='BFS')
    ax.bar(x, df['tempo_DFS'], width=width, label='DFS')
    ax.bar([i + width for i in x], df['tempo_Astar'], width=width, label='A*')
    ax.set_title('Tempo de Execução por Configuração')
    ax.set_xlabel('Configuração')
    ax.set_ylabel('Tempo de Execução (segundos)')
    ax.set_xticks(x)
    ax.set_xticklabels(config_list, rotation=45)
    ax.legend()
    plt.tight_layout()
    plt.savefig('grafico_comparativo_execucao.png')
    plt.close()

    # Gráfico de Nós Expandidos (escala logarítmica)
    fig, ax = plt.subplots(figsize=(12, 7))
    nos_bfs = prepare_for_log(df['nos_BFS'])
    nos_dfs = prepare_for_log(df['nos_DFS'])
    nos_astar = prepare_for_log(df['nos_Astar'])
    
    ax.bar([i - width for i in x], nos_bfs, width=width, label='BFS')
    ax.bar(x, nos_dfs, width=width, label='DFS')
    ax.bar([i + width for i in x], nos_astar, width=width, label='A*')
    
    ax.set_title('Nós Expandidos por Configuração (escala logarítmica)')
    ax.set_xlabel('Configuração')
    ax.set_ylabel('Número de Nós Expandidos - log scale')
    ax.set_yscale('log')
    ax.set_xticks(x)
    ax.set_xticklabels(config_list, rotation=45)
    ax.legend()
    plt.tight_layout()
    plt.savefig('grafico_comparativo_nos_expandidos_log.png')
    plt.close()
    
    # Versão não-logarítmica para comparação
    fig, ax = plt.subplots(figsize=(12, 7))
    ax.bar([i - width for i in x], df['nos_BFS'], width=width, label='BFS')
    ax.bar(x, df['nos_DFS'], width=width, label='DFS')
    ax.bar([i + width for i in x], df['nos_Astar'], width=width, label='A*')
    ax.set_title('Nós Expandidos por Configuração')
    ax.set_xlabel('Configuração')
    ax.set_ylabel('Número de Nós Expandidos')
    ax.set_xticks(x)
    ax.set_xticklabels(config_list, rotation=45)
    ax.legend()
    plt.tight_layout()
    plt.savefig('grafico_comparativo_nos_expandidos.png')
    plt.close()

    # Gráfico de Taxa de Sucesso
    fig, ax = plt.subplots(figsize=(12, 7))
    ax.bar([i - width for i in x], df['taxa_sucesso_BFS'], width=width, label='BFS')
    ax.bar(x, df['taxa_sucesso_DFS'], width=width, label='DFS')
    ax.bar([i + width for i in x], df['taxa_sucesso_Astar'], width=width, label='A*')
    
    ax.set_title('Taxa de Sucesso por Configuração')
    ax.set_xlabel('Configuração')
    ax.set_ylabel('Taxa de Sucesso (%)')
    ax.set_xticks(x)
    ax.set_xticklabels(config_list, rotation=45)
    ax.legend()
    plt.tight_layout()
    plt.savefig('grafico_comparativo_taxa_sucesso.png')
    plt.close()

    # Gráfico de Eficiência (nós/passo) (escala logarítmica)
    fig, ax = plt.subplots(figsize=(12, 7))
    ef_bfs = prepare_for_log(df['eficiencia_BFS'])
    ef_dfs = prepare_for_log(df['eficiencia_DFS'])
    ef_astar = prepare_for_log(df['eficiencia_Astar'])
    
    ax.bar([i - width for i in x], ef_bfs, width=width, label='BFS')
    ax.bar(x, ef_dfs, width=width, label='DFS')
    ax.bar([i + width for i in x], ef_astar, width=width, label='A*')
    
    ax.set_title('Eficiência (Nós/Passo) por Configuração (escala logarítmica)')
    ax.set_xlabel('Configuração')
    ax.set_ylabel('Eficiência (Nós/Passo) - log scale')
    ax.set_yscale('log')
    ax.set_xticks(x)
    ax.set_xticklabels(config_list, rotation=45)
    ax.legend()
    plt.tight_layout()
    plt.savefig('grafico_comparativo_eficiencia_log.png')
    plt.close()
    
    # Versão não-logarítmica para comparação
    fig, ax = plt.subplots(figsize=(12, 7))
    ax.bar([i - width for i in x], df['eficiencia_BFS'], width=width, label='BFS')
    ax.bar(x, df['eficiencia_DFS'], width=width, label='DFS')
    ax.bar([i + width for i in x], df['eficiencia_Astar'], width=width, label='A*')
    ax.set_title('Eficiência (Nós/Passo) por Configuração')
    ax.set_xlabel('Configuração')
    ax.set_ylabel('Eficiência (Nós/Passo)')
    ax.set_xticks(x)
    ax.set_xticklabels(config_list, rotation=45)
    ax.legend()
    plt.tight_layout()
    plt.savefig('grafico_comparativo_eficiencia.png')
    plt.close()

    # Gráfico de Consumo de Memória (escala logarítmica)
    fig, ax = plt.subplots(figsize=(12, 7))
    # Usamos valores absolutos para memória para evitar problemas com valores negativos
    mem_bfs = prepare_for_log(df['memoria_BFS'])
    mem_dfs = prepare_for_log(df['memoria_DFS'])
    mem_astar = prepare_for_log(df['memoria_Astar'])
    
    ax.bar([i - width for i in x], mem_bfs, width=width, label='BFS')
    ax.bar(x, mem_dfs, width=width, label='DFS')
    ax.bar([i + width for i in x], mem_astar, width=width, label='A*')
    
    ax.set_title('Consumo de Memória (Valor Absoluto) por Configuração (escala logarítmica)')
    ax.set_xlabel('Configuração')
    ax.set_ylabel('Memória (MB) - log scale (valores absolutos)')
    ax.set_yscale('log')
    ax.set_xticks(x)
    ax.set_xticklabels(config_list, rotation=45)
    ax.legend()
    plt.tight_layout()
    plt.savefig('grafico_comparativo_memoria_log.png')
    plt.close()
    
    # Versão não-logarítmica para comparação
    fig, ax = plt.subplots(figsize=(12, 7))
    # Usamos valores absolutos para memória para evitar problemas com valores negativos
    ax.bar([i - width for i in x], [abs(v) if pd.notna(v) else 0 for v in df['memoria_BFS']], width=width, label='BFS')
    ax.bar(x, [abs(v) if pd.notna(v) else 0 for v in df['memoria_DFS']], width=width, label='DFS')
    ax.bar([i + width for i in x], [abs(v) if pd.notna(v) else 0 for v in df['memoria_Astar']], width=width, label='A*')
    ax.set_title('Consumo de Memória (Valor Absoluto) por Configuração')
    ax.set_xlabel('Configuração')
    ax.set_ylabel('Memória (MB) (valores absolutos)')
    ax.set_xticks(x)
    ax.set_xticklabels(config_list, rotation=45)
    ax.legend()
    plt.tight_layout()
    plt.savefig('grafico_comparativo_memoria.png')
    plt.close()

    print("Gráficos comparativos foram gerados com sucesso!")


# Executar o código principal
if __name__ == "__main__":
    # Ler os dados dos arquivos de relatório diretamente da pasta atual
    df = ler_dados_relatorio()
    
    # Gerar gráficos comparativos se houver dados
    if not df.empty:
        gerar_graficos_comparativos(df)
    else:
        print("Não foi possível gerar gráficos. Nenhum dado válido foi encontrado.")

