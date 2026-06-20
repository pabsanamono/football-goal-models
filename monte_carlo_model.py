import math
import random
from collections import defaultdict


def poisson_rv(lmbda: float) -> int:
    """
    Genera un numero aleatorio con distribucion Poisson sin librerias externas.
    Algoritmo de Knuth (1969).

    Args:
        lmbda: Lambda (media esperada) de la distribucion Poisson.

    Returns:
        Entero aleatorio con distribucion Poisson.
    """
    L = math.exp(-lmbda)
    k = 0
    p = 1.0
    while p > L:
        k += 1
        p *= random.random()
    return k - 1


def monte_carlo_score_probabilities(
    lambda_home: float,
    lambda_away: float,
    max_goals: int = 10,
    n_simulations: int = 100000
) -> dict:
    """
    Simulador Monte Carlo de probabilidades de marcador correcto.

    Simula n_simulaciones partidos y calcula la frecuencia relativa
    de cada marcador posible.

    Args:
        lambda_home: Goles esperados del equipo local.
        lambda_away: Goles esperados del equipo visitante.
        max_goals: Maximo de goles por equipo a registrar individualmente.
        n_simulations: Numero de simulaciones.

    Returns:
        Diccionario con marcadores y sus probabilidades estimadas.
    """
    results = defaultdict(int)

    for _ in range(n_simulations):
        home_goals = poisson_rv(lambda_home)
        away_goals = poisson_rv(lambda_away)

        if home_goals <= max_goals and away_goals <= max_goals:
            key = f"{home_goals}-{away_goals}"
        else:
            key = "Other"

        results[key] += 1

    return {
        score: round(count / n_simulations, 6)
        for score, count in sorted(results.items(), key=lambda x: -x[1])
    }


def match_outcomes(score_probs: dict) -> dict:
    """
    Calcula probabilidades de resultado final (1X2) a partir de los marcadores.

    Args:
        score_probs: Diccionario de marcadores con probabilidades.

    Returns:
        Diccionario con probabilidad de ganar local, empate y ganar visitante.
    """
    home_win = 0.0
    draw = 0.0
    away_win = 0.0

    for score, prob in score_probs.items():
        if score == "Other":
            continue
        h, a = map(int, score.split("-"))
        if h > a:
            home_win += prob
        elif h == a:
            draw += prob
        else:
            away_win += prob

    return {
        "Home_win": round(home_win, 4),
        "Draw": round(draw, 4),
        "Away_win": round(away_win, 4)
    }


if __name__ == "__main__":
    HOME_XG = 1.4
    AWAY_XG = 0.7

    print(f"Simulando partido con xG local = {HOME_XG} | xG visitante = {AWAY_XG}")
    print("-" * 40)

    score_probs = monte_carlo_score_probabilities(HOME_XG, AWAY_XG)

    print("\n== PROBABILIDADES DE MARCADOR (Top 15) ==")
    for i, (score, prob) in enumerate(list(score_probs.items())[:15]):
        print(f"  {score}: {prob*(100):.3f}%")

    outcomes = match_outcomes(score_probs)
    print("\n== RESULTADOS FINALES (1X2) ==")
    for k, v in outcomes.items():
        print(f"  {k}: {v*100:.2f}%")
