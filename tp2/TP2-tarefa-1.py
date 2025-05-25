import numpy as np
import time
import itertools
import matplotlib.pyplot as plt

def f(x):
    return np.sum(x**2)

def inicializa_populacao(pop_size, n_var, limite):
    return np.random.uniform(-limite, limite, size=(pop_size, n_var))

def fitness(pop):
    return np.array([f(ind) for ind in pop])

def selecao_torneio(pop, fit, k=3):
    selected = []
    for _ in range(len(pop)):
        aspirantes_idx = np.random.choice(len(pop), k)
        melhor = aspirantes_idx[np.argmin(fit[aspirantes_idx])]
        selected.append(pop[melhor])
    return np.array(selected)

def cruzamento(pais, taxa_c):
    filhos = []
    pop_size, n_var = pais.shape
    for i in range(0, pop_size, 2):
        pai1 = pais[i]
        pai2 = pais[(i+1) % pop_size]
        if np.random.rand() < taxa_c:
            ponto = np.random.randint(1, n_var)
            filho1 = np.concatenate([pai1[:ponto], pai2[ponto:]])
            filho2 = np.concatenate([pai2[:ponto], pai1[ponto:]])
        else:
            filho1, filho2 = pai1.copy(), pai2.copy()
        filhos.extend([filho1, filho2])
    return np.array(filhos[:pop_size])

def mutacao(pop, taxa_m, sigma=0.1, limite=5):
    for ind in pop:
        for i in range(len(ind)):
            if np.random.rand() < taxa_m:
                ind[i] += np.random.normal(0, sigma)
                ind[i] = np.clip(ind[i], -limite, limite)
    return pop

def AG(pop_size, taxa_c, taxa_m, k=3, n_ger=20, n_var=5, limite=5):
    pop = inicializa_populacao(pop_size, n_var, limite)
    melhor_por_geracao = []
    for _ in range(n_ger):
        fit = fitness(pop)
        melhor_por_geracao.append(np.min(fit))
        pais = selecao_torneio(pop, fit, k)
        filhos = cruzamento(pais, taxa_c)
        pop = mutacao(filhos, taxa_m, limite=limite)
    fit_final = fitness(pop)
    melhor_por_geracao.append(np.min(fit_final))
    return np.min(fit_final), melhor_por_geracao

# Parâmetros reduzidos para não dar timeout
pop_sizes = [15, 25]
taxas_cruzamento = [0.6, 0.8, 0.9]
taxas_mutacao = [0.01, 0.04]
ks = [1, 3]
executions = 2  # execuções por configuração

configs = list(itertools.product(pop_sizes, taxas_cruzamento, taxas_mutacao, ks))
resultados = []

print("Executando AG para configurações reduzidas...\n")

for pop_size, taxa_c, taxa_m, k in configs:
    melhores = []
    tempos = []
    evolucoes = []
    label = f"Pop={pop_size}, Cruz={taxa_c}, Mut={taxa_m}, k={k}"
    for _ in range(executions):
        start = time.time()
        melhor, evol = AG(pop_size, taxa_c, taxa_m, k=k, n_ger=20)
        tempos.append(time.time() - start)
        melhores.append(melhor)
        evolucoes.append(evol)
    media = np.mean(melhores)
    desvio = np.std(melhores)
    melhor_geral = np.min(melhores)
    tempo_medio = np.mean(tempos)
    resultados.append({
        "config": label,
        "melhor_valor": melhor_geral,
        "media": media,
        "desvio": desvio,
        "tempo": tempo_medio,
        "todos_melhores": melhores,
        "evolucoes": evolucoes,
    })

print("\n| Configuração                 | Melhor Valor | Média     | Desvio Padrão | Tempo Médio (s) | Valores por Execução           |")
print("|-----------------------------|--------------|-----------|---------------|-----------------|-------------------------------|")
for r in resultados:
    vals_str = ", ".join(f"{v:.2f}" for v in r["todos_melhores"])
    print(f"| {r['config']:27} | {r['melhor_valor']:<12.2f} | {r['media']:<9.2f} | {r['desvio']:<13.2f} | {r['tempo']:<15.2f} | {vals_str} |")
# Plots simples só para verificar a evolução média
plt.figure(figsize=(12, 8))
for r in resultados:
    evolucoes_array = np.array(r["evolucoes"])
    media_evol = np.mean(evolucoes_array, axis=0)
    plt.plot(media_evol, label=r["config"])
plt.xlabel("Geração")
plt.ylabel("Melhor valor da função objetivo")
plt.title("Evolução média da função objetivo por geração")
plt.legend(fontsize=8)
plt.grid(True)
plt.show()
