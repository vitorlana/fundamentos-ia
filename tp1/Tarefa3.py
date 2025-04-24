import random
from collections import deque

# Estado objetivo do quebra-cabeça 15
objetivo = (
    (1, 2, 3, 4),
    (5, 6, 7, 8),
    (9,10,11,12),
    (13,14,15, 0)
)

# Movimentos válidos: cima, baixo, esquerda, direita
movimentos = [(-1,0),(1,0),(0,-1),(0,1)]

# ---------- Funções de utilidade ----------

def contar_inversoes(tab):
    plano = [n for linha in tab for n in linha if n != 0]
    inversoes = 0
    for i in range(len(plano)):
        for j in range(i + 1, len(plano)):
            if plano[i] > plano[j]:
                inversoes += 1
    return inversoes

def encontrar_linha_zero(tab):
    for i in range(4):
        if 0 in tab[i]:
            return 4 - i  # linha a partir de baixo

def eh_soluvel(tab):
    inversoes = contar_inversoes(tab)
    linha_zero = encontrar_linha_zero(tab)
    return (inversoes + linha_zero) % 2 == 0

def encontrar_zero(tab):
    for i in range(4):
        for j in range(4):
            if tab[i][j] == 0:
                return i, j

def mover(tab, direcao):
    i, j = encontrar_zero(tab)
    ni, nj = i + direcao[0], j + direcao[1]
    if 0 <= ni < 4 and 0 <= nj < 4:
        novo = [list(l) for l in tab]
        novo[i][j], novo[ni][nj] = novo[ni][nj], novo[i][j]
        return tuple(tuple(l) for l in novo)
    return None

# ---------- Geração de estado inicial ----------

def gerar_estado_inicial(passos=30):
    tab = objetivo
    for _ in range(passos):
        random.shuffle(movimentos)
        for mov in movimentos:
            novo = mover(tab, mov)
            if novo:
                tab = novo
                break
    return tab

# ---------- Busca em largura (BFS) ----------

def bfs(inicio):
    fila = deque([(inicio, [])])
    visitados = set()
    while fila:
        atual, caminho = fila.popleft()
        if atual == objetivo:
            return caminho + [atual]
        visitados.add(atual)
        for mov in movimentos:
            prox = mover(atual, mov)
            if prox and prox not in visitados:
                fila.append((prox, caminho + [atual]))
    return None

# ---------- Busca em profundidade (DFS) iterativo ----------

def dfs(inicio, limite=20):
    pilha = [(inicio, [], 0)]  # estado, caminho, profundidade

    while pilha:
        atual, caminho, profundidade = pilha.pop()

        if atual == objetivo:
            return caminho + [atual]

        if profundidade >= limite:
            continue

        for mov in movimentos:
            prox = mover(atual, mov)
            if prox and prox not in caminho:  # evita ciclos
                pilha.append((prox, caminho + [atual], profundidade + 1))
    
    return None

# ---------- Execução direta ----------

estado = gerar_estado_inicial()

print("Estado inicial:")
for linha in estado:
    print(linha)

print("\nÉ solucionável?", "Sim" if eh_soluvel(estado) else "Não")

print("\n--- RESOLVENDO COM BFS ---")
solucao_bfs = bfs(estado)
if solucao_bfs:
    print(f"Solução encontrada com BFS em {len(solucao_bfs) - 1} movimentos.")
else:
    print("Solução não encontrada com BFS.")

print("\n--- RESOLVENDO COM DFS ---")
solucao_dfs = dfs(estado, limite=20)
if solucao_dfs:
    print(f"Solução encontrada com DFS em {len(solucao_dfs) - 1} movimentos.")
else:
    print("Solução não encontrada com DFS.")
