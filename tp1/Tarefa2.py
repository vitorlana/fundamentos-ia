import random
import copy

# Configuração objetivo
objetivo = [
    [1, 2, 3, 4],
    [5, 6, 7, 8],
    [9,10,11,12],
    [13,14,15, 0]
]

# Direções de movimento (cima, baixo, esquerda, direita)
movimentos = [(-1,0),(1,0),(0,-1),(0,1)]

def encontrar_posicao_vazio(tabuleiro):
    """Encontra a posição do espaço vazio (0)"""
    for i in range(4):
        for j in range(4):
            if tabuleiro[i][j] == 0:
                return i, j

def mover(tabuleiro, direcao):
    """Move a peça na direção indicada, se possível"""
    i, j = encontrar_posicao_vazio(tabuleiro)
    di, dj = direcao
    ni, nj = i + di, j + dj

    if 0 <= ni < 4 and 0 <= nj < 4:
        tabuleiro[i][j], tabuleiro[ni][nj] = tabuleiro[ni][nj], tabuleiro[i][j]
        return True
    return False

def gerar_estado_inicial_soluvel(qtd_movimentos=100):
    """Gera um tabuleiro aleatório a partir da configuração objetivo usando movimentos válidos"""
    tabuleiro = copy.deepcopy(objetivo)
    ultimo_movimento = None

    for _ in range(qtd_movimentos):
        movs_validos = movimentos.copy()

        # Evita desfazer o último movimento
        if ultimo_movimento:
            oposto = (-ultimo_movimento[0], -ultimo_movimento[1])
            if oposto in movs_validos:
                movs_validos.remove(oposto)

        random.shuffle(movs_validos)

        for direcao in movs_validos:
            if mover(tabuleiro, direcao):
                ultimo_movimento = direcao
                break

    return tabuleiro

# Exemplo de uso
tabuleiro = gerar_estado_inicial_soluvel()
for linha in tabuleiro:
    print(linha)

