import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

# Configuração para melhorar a aparência dos gráficos
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_context("talk")

# Leitura do arquivo de texto
try:
    # Tenta ler o arquivo assumindo que tem apenas duas colunas (índice e número de gerações)
    dados = pd.read_csv('dados_duplicacoes.txt', sep='\s+', header=None, names=['indice', 'geracoes'])
except Exception as e:
    print(f"Erro na primeira tentativa: {e}")
    try:
        # Tenta ler ignorando a primeira linha caso seja um cabeçalho
        dados = pd.read_csv('dados_duplicacoes.txt', sep='\s+', header=None, skiprows=1, names=['indice', 'geracoes'])
    except Exception as e:
        print(f"Erro na segunda tentativa: {e}")
        # Se ainda falhar, cria dados de teste a partir do texto fornecido
        linhas_cruas = []
        with open('dados_duplicacoes.txt', 'r') as file:
            linhas_cruas = file.readlines()

        indices = []
        geracoes = []

        for linha in linhas_cruas:
            partes = linha.strip().split()
            if len(partes) >= 2:
                try:
                    # Tenta extrair os números da linha
                    numero_str = partes[0].replace('(', '').replace(')', '')
                    indice = int(numero_str)
                    geracao_str = ' '.join(partes[3:]).replace('.', '')
                    geracao = int(geracao_str)

                    indices.append(indice)
                    geracoes.append(geracao)
                except:
                    pass

        dados = pd.DataFrame({'indice': indices, 'geracoes': geracoes})

# Ordenar os dados pelo índice
dados = dados.sort_values('indice')

# Converter gerações para milhões para facilitar a visualização
dados['geracoes_milhoes'] = dados['geracoes'] / 1000000

# Cálculo de estatísticas básicas
minimo = dados['geracoes'].min()
maximo = dados['geracoes'].max()
media = dados['geracoes'].mean()
mediana = dados['geracoes'].median()
desvio_padrao = dados['geracoes'].std()

# Configurações de figura para alta qualidade
plt.figure(figsize=(14, 10), dpi=150)

# ---- GRÁFICO 1: Histograma com todas as amostras ----
plt.subplot(2, 1, 1)

# Histograma principal
n, bins, patches = plt.hist(dados['geracoes_milhoes'], bins=18, range=(0, 18),
                            color='blue', alpha=0.7, edgecolor='black')

# Linha da média
plt.axvline(x=media / 1000000, color='red', linestyle='-', linewidth=2,
            label=f'Média: {media / 1000000:.2f} milhões')

# Estatísticas detalhadas
estatisticas = (f"Estatísticas (gerações):\n"
                f"Mínimo: {minimo:,.0f}\n"
                f"Máximo: {maximo:,.0f}\n"
                f"Média: {media:,.0f}\n"
                f"Mediana: {mediana:,.0f}\n"
                f"Desvio padrão: {desvio_padrao:,.0f}")

# Adicionar texto com estatísticas
plt.text(0.72, 0.95, estatisticas, transform=plt.gca().transAxes, fontsize=12,
         verticalalignment='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

plt.title('Histograma do número de gerações até encontrar um tabuleiro duplicado', fontsize=16)
plt.xlabel('Número de gerações (milhões)', fontsize=14)
plt.ylabel('Frequência', fontsize=14)
plt.xlim(0, 18)
plt.xticks(range(0, 19, 2))
plt.grid(True, linestyle='--', alpha=0.7)
plt.legend()

# ---- GRÁFICO 2: Scatterplot com todas as execuções ----
plt.subplot(2, 1, 2)

# Scatter plot de todas as execuções
plt.scatter(dados['indice'], dados['geracoes_milhoes'],
            color='blue', alpha=0.7, edgecolor='black')

# Linha horizontal para a média
plt.axhline(y=media / 1000000, color='red', linestyle='-', linewidth=2,
            label=f'Média: {media / 1000000:.2f} milhões')

# Linha de tendência (opcional)
z = np.polyfit(dados['indice'], dados['geracoes_milhoes'], 1)
p = np.poly1d(z)
plt.plot(dados['indice'], p(dados['indice']), "r--", alpha=0.5)

plt.title('Número de gerações até encontrar um tabuleiro duplicado (por execução)', fontsize=16)
plt.xlabel('Execução', fontsize=14)
plt.ylabel('Número de gerações (milhões)', fontsize=14)
plt.grid(True, linestyle='--', alpha=0.7)
plt.legend()

# Ajustar layout e salvar
plt.tight_layout()
plt.savefig('analise_duplicacoes_completa.pdf', bbox_inches='tight')
plt.savefig('analise_duplicacoes_completa.png', bbox_inches='tight')

# Exibir os gráficos
plt.show()

# Imprimir estatísticas detalhadas
print(f"\nEstatísticas Completas:")
print(f"Total de execuções: {len(dados)}")
print(f"Mínimo: {minimo:,.0f} gerações ({minimo / 1000000:.2f} milhões)")
print(f"Máximo: {maximo:,.0f} gerações ({maximo / 1000000:.2f} milhões)")
print(f"Média: {media:,.0f} gerações ({media / 1000000:.2f} milhões)")
print(f"Mediana: {mediana:,.0f} gerações ({mediana / 1000000:.2f} milhões)")
print(f"Desvio padrão: {desvio_padrao:,.0f} gerações ({desvio_padrao / 1000000:.2f} milhões)")
print(f"Intervalo: {maximo - minimo:,.0f} gerações ({(maximo - minimo) / 1000000:.2f} milhões)")

# Salvar os dados processados em um arquivo CSV para referência
dados.to_csv('dados_duplicacoes_processados.csv', index=False)