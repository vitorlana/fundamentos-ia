import time
import csv
import os
import psutil
import random
import threading
from tp1_completo import *

def executar_iteracao(profundidade_maxima, qtd_movimentos, seed):
    resultados_iteracao = {}

    # Dados de processamento antes (overall iteration)
    process = psutil.Process(os.getpid())
    wall_start = time.time()

    # Gerar um tabuleiro inicial solucionável com seed fixa
    random.seed(seed)
    tabuleiro_soluvel = gerar_estado_inicial_soluvel(qtd_movimentos=qtd_movimentos)
    resultados_iteracao["initial_state"] = tabuleiro_soluvel
    resultados_iteracao["is_solvable"] = eh_soluvel(tabuleiro_soluvel)
    resultados_iteracao["qtd_movimentos"] = qtd_movimentos
    resultados_iteracao["seed"] = seed
    resultados_iteracao["inversoes"] = contar_inversoes(tabuleiro_soluvel)
    resultados_iteracao["linha_vazio"] = posicao_linha_vazio(tabuleiro_soluvel)
    resultados_iteracao["profundidade_maxima"] = profundidade_maxima

    inicial = tabuleiro_para_estado(tabuleiro_soluvel)
    meta = tabuleiro_para_estado(objetivo)

    alg_results = {}

    def run_algorithm(algorithm_name, algorithm_func, *args):
        t_cpu_start = time.thread_time()
        t_wall_start = time.time()
        mem_start = process.memory_info().rss / (1024 * 1024)  # MB
        solution, expanded = algorithm_func(*args)
        t_cpu_end = time.thread_time()
        t_wall_end = time.time()
        mem_end = process.memory_info().rss / (1024 * 1024)  # MB

        if solution:
            directions = converter_caminho_em_direcoes(inicial, solution)
            step_count = len(solution) - 1
        else:
            directions = []
            step_count = 0

        alg_results[algorithm_name] = {
            "time": t_wall_end - t_wall_start,
            "cpu_time": t_cpu_end - t_cpu_start,
            "expanded": expanded,
            "found": bool(solution),
            "directions": directions,
            "step_count": step_count,
            "mem_MB_inicio": mem_start,
            "mem_MB_fim": mem_end
        }

    # Create and start threads for each algorithm
    threads = []
    for name, func in [("BFS", bfs), ("DFS", dfs), ("A*", a_star)]:
        t = threading.Thread(target=run_algorithm, args=(name, func, inicial, meta) if name != "DFS" else (name, func, inicial, meta, profundidade_maxima))
        t.start()
        threads.append(t)
    for t in threads:
        t.join()

    # Dados de processamento depois (overall iteration)
    wall_end = time.time()

    resultados_iteracao["BFS"] = alg_results["BFS"]
    resultados_iteracao["DFS"] = alg_results["DFS"]
    resultados_iteracao["A*"] = alg_results["A*"]
    resultados_iteracao["processamento"] = {
        "wall_time_total": wall_end - wall_start,
        "pid": os.getpid()
    }
    return resultados_iteracao

def gerar_relatorio_final(iteration_results, resultados, iteracoes):
    # Agora lemos somente o arquivo gerado e calculamos as médias no final
    dados_por_algoritmo = {"BFS": [], "DFS": [], "A*": []}

    with open("resultados.csv", "r", newline='', encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            alg = row["Algorithm"]
            if alg in dados_por_algoritmo:
                dados_por_algoritmo[alg].append(row)

    with open("resultados.csv", "a", newline='', encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([])
        writer.writerow(["Algorithm", "Avg Time", "Avg Expanded", "Solutions Found/Iterations"])

        for alg, dados in dados_por_algoritmo.items():
            soma_tempo = sum(float(d["Time"]) for d in dados)
            soma_expandidos = sum(int(d["Expanded"]) for d in dados)
            solucoes = sum(1 for d in dados if d["Found"] == "True")
            media_tempo = soma_tempo / len(dados) if dados else 0
            media_expandidos = soma_expandidos / len(dados) if dados else 0
            writer.writerow([
                alg,
                f"{media_tempo:.4f}",
                f"{media_expandidos:.2f}",
                f"{solucoes}/{iteracoes}"
            ])

def testar_algoritmos(iteracoes, profundidade_maxima=30, qtd_movimentos=10):
    resultados = {
        "BFS": {"tempo_total": 0, "nos_expandidos_total": 0, "solucoes_encontradas": 0},
        "DFS": {"tempo_total": 0, "nos_expandidos_total": 0, "solucoes_encontradas": 0},
        "A*": {"tempo_total": 0, "nos_expandidos_total": 0, "solucoes_encontradas": 0},
    }
    iteration_results = []

    # Update CSV header to use algorithm-specific processing fields
    with open("resultados.csv", "w", newline='', encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([
            "Iteration", "Algorithm", "Time", "CPUTime", "Expanded", "Found",
            "Steps", "Directions", "InitialBoard", "Solvable",
            "ProfundidadeMaximaDFS", "QtdMovimentos", "Seed", "Inversoes", "LinhaVazio",
            "MemMBInicio", "MemMBFim", "PID"
        ])

    for i in range(iteracoes):
        seed = random.randint(0, 99999999)
        iter_data = executar_iteracao(profundidade_maxima, qtd_movimentos, seed)
        iteration_results.append(iter_data)

        # Write data for each algorithm separately
        with open("resultados.csv", "a", newline='', encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            for alg in ["BFS", "DFS", "A*"]:
                writer.writerow([
                    i + 1,
                    alg,
                    iter_data[alg]["time"],
                    iter_data[alg].get("cpu_time", ""),  # per-thread CPU time
                    iter_data[alg]["expanded"],
                    iter_data[alg]["found"],
                    iter_data[alg]["step_count"],
                    iter_data[alg]["directions"],
                    str(iter_data["initial_state"]),
                    str(iter_data["is_solvable"]),
                    iter_data["profundidade_maxima"] if alg == "DFS" else "",
                    iter_data["qtd_movimentos"],
                    iter_data["seed"],
                    iter_data["inversoes"],
                    iter_data["linha_vazio"],
                    iter_data[alg].get("mem_MB_inicio", ""),
                    iter_data[alg].get("mem_MB_fim", ""),
                    iter_data["processamento"].get("pid", "")
                ])

        # Update results for each algorithm separately
        for alg in ["BFS", "DFS", "A*"]:
            resultados[alg]["tempo_total"] += iter_data[alg]["time"]
            resultados[alg]["nos_expandidos_total"] += iter_data[alg]["expanded"]
            if iter_data[alg]["found"]:
                resultados[alg]["solucoes_encontradas"] += 1

    gerar_relatorio_final(iteration_results, resultados, iteracoes)

if __name__ == "__main__":
    testar_algoritmos(iteracoes=5, profundidade_maxima=10, qtd_movimentos=10)
    # testar_algoritmos(iteracoes=5, profundidade_maxima=20, qtd_movimentos=10)
    # testar_algoritmos(iteracoes=5, profundidade_maxima=30, qtd_movimentos=10)
    # testar_algoritmos(iteracoes=5, profundidade_maxima=40, qtd_movimentos=10)
    # testar_algoritmos(iteracoes=5, profundidade_maxima=50, qtd_movimentos=10) Nao rodou em tempo viavel
    # testar_algoritmos(iteracoes=5, profundidade_maxima=30, qtd_movimentos=5)
    # testar_algoritmos(iteracoes=5, profundidade_maxima=30, qtd_movimentos=15)
    # testar_algoritmos(iteracoes=5, profundidade_maxima=30, qtd_movimentos=20)


