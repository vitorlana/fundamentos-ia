import random

def ler_dados_mochila(caminho_arquivo):
    """
    Lê os dados do problema da mochila a partir de um arquivo.
    Formato esperado do arquivo
    """
    itens = []
    try:
        with open(caminho_arquivo, 'r') as f:
            num_itens_str = f.readline().strip()
            if not num_itens_str:
                raise ValueError("Primeira linha (número de itens) está vazia.")
            num_itens = int(num_itens_str)

            capacidade_maxima_str = f.readline().strip()
            if not capacidade_maxima_str:
                raise ValueError("Segunda linha (capacidade máxima) está vazia.")
            capacidade_maxima = int(capacidade_maxima_str)

            itens_lidos = 0
            while itens_lidos < num_itens:
                linha = f.readline()
                if not linha:
                    raise EOFError(f"Esperava {num_itens} itens, mas o arquivo terminou após ler {itens_lidos}.")
                linha_strip = linha.strip()
                if not linha_strip:
                    continue

                partes = linha_strip.split()
                if len(partes) < 2:
                    raise ValueError(f"Linha de item mal formatada: '{linha_strip}'")

                valor = int(partes[0])
                peso = int(partes[1])
                itens.append({'valor': valor, 'peso': peso})
                itens_lidos += 1

        return itens, capacidade_maxima, num_itens
    except FileNotFoundError:
        print(f"Erro: Arquivo '{caminho_arquivo}' não encontrado.")
        return None, 0, 0
    except ValueError as ve:
        print(f"Erro de valor ao processar o arquivo: {ve}")
        return None, 0, 0
    except EOFError as eofe:
        print(f"Erro de formato de arquivo: {eofe}")
        return None, 0, 0
    except Exception as e:
        print(f"Erro ao ler o arquivo '{caminho_arquivo}': {e}")
        return None, 0, 0


def inicializar_individuo(num_itens):
    """
    Cria um indivíduo aleatório (solução candidata).
    Um indivíduo é uma lista de bits, onde 1 significa que o item foi escolhido.
    """
    return [random.randint(0, 1) for _ in range(num_itens)]

def calcular_fitness(individuo, itens, capacidade_maxima):
    """
    Calcula o fitness (aptidão) de um indivíduo.
    O fitness é o valor total dos itens na mochila.
    Se o peso total exceder a capacidade, o fitness é penalizado (aqui, zerado),
    conforme a necessidade de tratar restrições.
    """
    valor_total = 0
    peso_total = 0
    for i, escolhido in enumerate(individuo):
        if escolhido == 1:
            valor_total += itens[i]['valor']
            peso_total += itens[i]['peso']

    if peso_total > capacidade_maxima:
        return 0  # Penalidade: indivíduo inválido tem fitness zero
    else:
        return valor_total

def selecao_torneio(populacao, aptidoes, tamanho_torneio):
    """
    Seleciona um indivíduo da população usando o método de seleção por torneio.
    """
    selecionados_para_torneio_indices = random.sample(range(len(populacao)), tamanho_torneio)

    melhor_individuo_torneio_indice = selecionados_para_torneio_indices[0]
    melhor_aptidao_torneio = aptidoes[melhor_individuo_torneio_indice]

    for i in range(1, tamanho_torneio):
        indice_atual = selecionados_para_torneio_indices[i]
        if aptidoes[indice_atual] > melhor_aptidao_torneio:
            melhor_aptidao_torneio = aptidoes[indice_atual]
            melhor_individuo_torneio_indice = indice_atual

    return populacao[melhor_individuo_torneio_indice]

def cruzamento_um_ponto(pai1, pai2, taxa_cruzamento):
    """
    Realiza o cruzamento de um ponto entre dois pais para gerar dois filhos.
    O cruzamento só ocorre se um número aleatório for menor que a taxa_cruzamento.
    """
    filho1, filho2 = list(pai1), list(pai2)
    if random.random() < taxa_cruzamento:
        if len(pai1) > 1:
            ponto_corte = random.randint(1, len(pai1) - 1)
            filho1 = pai1[:ponto_corte] + pai2[ponto_corte:]
            filho2 = pai2[:ponto_corte] + pai1[ponto_corte:]
    return filho1, filho2

def mutacao_bit_flip(individuo, taxa_mutacao_gene):
    """
    Realiza a mutação do tipo bit-flip em um indivíduo.
    Cada gene (bit) do indivíduo tem uma chance de ser invertido.
    """
    individuo_mutado = list(individuo) # Copia o indivíduo
    for i in range(len(individuo_mutado)):
        if random.random() < taxa_mutacao_gene:
            individuo_mutado[i] = 1 - individuo_mutado[i] # Inverte o bit
    return individuo_mutado

def algoritmo_genetico_mochila(itens, capacidade_maxima, num_itens,
                               tamanho_populacao, taxa_cruzamento,
                               taxa_mutacao_gene, num_geracoes,
                               tamanho_torneio=3, usar_elitismo=True):
    """
    Executa o Algoritmo Genético para o problema da mochila.
    """
    if not itens:
        print("Não há itens para processar. Verifique o arquivo de entrada.")
        return None, 0

    # 1. Inicializar a população
    populacao = [inicializar_individuo(num_itens) for _ in range(tamanho_populacao)]

    melhor_solucao_geral = None
    melhor_fitness_geral = -1

    #print(f"\nIniciando Algoritmo Genético para o Problema da Mochila...")
    #print(f"Configurações: População={tamanho_populacao}, Taxa Cruzamento={taxa_cruzamento}, "
          #f"Taxa Mutação Gene={taxa_mutacao_gene}, Gerações={num_geracoes}, Torneio={tamanho_torneio}, Elitismo={usar_elitismo}")

    for geracao in range(num_geracoes):
        # 2. Calcular fitness de cada indivíduo na população
        aptidoes = [calcular_fitness(ind, itens, capacidade_maxima) for ind in populacao]

        # Atualizar a melhor solução encontrada até agora
        for i in range(tamanho_populacao):
            if aptidoes[i] > melhor_fitness_geral:
                melhor_fitness_geral = aptidoes[i]
                melhor_solucao_geral = list(populacao[i]) # Armazena uma cópia

        # 3. Criar nova população
        nova_populacao = []

        # Elitismo: copiar o melhor indivíduo da geração atual para a próxima
        if usar_elitismo:
            indice_elite = aptidoes.index(max(aptidoes))
            nova_populacao.append(list(populacao[indice_elite]))

        # Preencher o restante da nova população com descendentes
        while len(nova_populacao) < tamanho_populacao:
            # a. Selecionar pais
            pai1 = selecao_torneio(populacao, aptidoes, tamanho_torneio)
            pai2 = selecao_torneio(populacao, aptidoes, tamanho_torneio)

            # b. Aplicar cruzamento
            filho1, filho2 = cruzamento_um_ponto(pai1, pai2, taxa_cruzamento)

            # c. Aplicar mutação
            filho1_mutado = mutacao_bit_flip(filho1, taxa_mutacao_gene)
            filho2_mutado = mutacao_bit_flip(filho2, taxa_mutacao_gene)

            nova_populacao.append(filho1_mutado)
            if len(nova_populacao) < tamanho_populacao:
                nova_populacao.append(filho2_mutado)

        populacao = nova_populacao

        #if (geracao + 1) % 10 == 0 or geracao == num_geracoes -1 : # Imprime o progresso
        #    print(f"Geração {geracao + 1}/{num_geracoes} - Melhor Fitness: {melhor_fitness_geral}")

    # Calcular o fitness da melhor solução geral ao final
    fitness_final_melhor_solucao = calcular_fitness(melhor_solucao_geral, itens, capacidade_maxima)

    # Se por acaso a melhor_solucao_geral foi invalidada ou não é a melhor após a última mutação/cruzamento
    # re-busca na população final.
    aptidoes_finais = [calcular_fitness(ind, itens, capacidade_maxima) for ind in populacao]
    max_fitness_final_pop = max(aptidoes_finais)
    if max_fitness_final_pop > melhor_fitness_geral:
        melhor_fitness_geral = max_fitness_final_pop
        melhor_solucao_geral = populacao[aptidoes_finais.index(max_fitness_final_pop)]
    elif fitness_final_melhor_solucao > melhor_fitness_geral: # caso melhor_solucao_geral tenha sido de uma geracao anterior e seja melhor
         melhor_fitness_geral = fitness_final_melhor_solucao


    #print("Otimização concluída.")
    return melhor_solucao_geral, melhor_fitness_geral

if __name__ == "__main__":
    arquivo_mochila = "mochila.txt"
    itens, capacidade, n_itens = ler_dados_mochila(arquivo_mochila)

    if itens:
        print("\n--- Dados Carregados do Arquivo ---")
        print(f"Número de itens: {n_itens}")
        print(f"Capacidade da mochila: {capacidade}")
        print(f"Primeiros 3 itens (exemplo): {itens[:3]}")
        print("-----------------------------------\n")

        TAMANHO_POPULACAO = 50
        TAXA_CRUZAMENTO = 0.85
        TAXA_MUTACAO_GENE = 0.05
        NUM_GERACOES = 100
        TAMANHO_TORNEIO = 3
        USAR_ELITISMO = True

        melhor_solucao, melhor_valor = algoritmo_genetico_mochila(
            itens, capacidade, n_itens,
            TAMANHO_POPULACAO, TAXA_CRUZAMENTO,
            TAXA_MUTACAO_GENE, NUM_GERACOES,
            TAMANHO_TORNEIO, USAR_ELITISMO
        )

        if melhor_solucao:
            print(f"\nMelhor solução encontrada: {melhor_solucao}")
            print(f"Valor total na mochila: {melhor_valor}")

            peso_final = sum(itens[i]['peso'] for i, bit in enumerate(melhor_solucao) if bit == 1)
            print(f"Peso total na mochila: {peso_final} (Capacidade: {capacidade})")

            print("\nItens selecionados na melhor solução:")
            for i, bit in enumerate(melhor_solucao):
                if bit == 1:
                    print(f"  - Item {i+1}: Valor={itens[i]['valor']}, Peso={itens[i]['peso']}")
        else:
            print("Não foi possível encontrar uma solução.")
    else:
        print("Não foi possível carregar os dados da mochila. Verifique o arquivo e o caminho.")
