import random

def gerar_tabuleiro_aleatorio():
    """Gera uma configuração aleatória do tabuleiro 4x4"""
    tabuleiro = list(range(1, 16)) + [0]  # 0 representa o espaço vazio
    random.shuffle(tabuleiro)
    return [tabuleiro[i:i+4] for i in range(0, 16, 4)]

def contar_inversoes(tabuleiro):
    """Conta o número de inversões no tabuleiro"""
    plano = [num for linha in tabuleiro for num in linha if num != 0]
    inversoes = 0
    for i in range(len(plano)):
        for j in range(i + 1, len(plano)):
            if plano[i] > plano[j]:
                inversoes += 1
    return inversoes

def posicao_linha_vazio(tabuleiro):
    """Retorna a linha do espaço vazio, contando de baixo para cima"""
    for i in range(4):
        if 0 in tabuleiro[i]:
            return 4 - i  # linhas são contadas de baixo para cima

def eh_soluvel(tabuleiro):
    """Verifica se uma configuração do tabuleiro é solucionável"""
    inversoes = contar_inversoes(tabuleiro)
    linha_vazio = posicao_linha_vazio(tabuleiro)

    if (linha_vazio % 2 == 0 and inversoes % 2 == 1) or \
       (linha_vazio % 2 == 1 and inversoes % 2 == 0):
        return True
    else:
        return False

# Exemplo de uso
tabuleiro = gerar_tabuleiro_aleatorio()
for linha in tabuleiro:
    print(linha)
print("É solucionável?" , eh_soluvel(tabuleiro))
