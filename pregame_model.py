import math

def pregame_model(
    xg_a: float,
    xg_b: float,
    odds_a: float,
    odds_b: float,
    is_home_a: bool = True
) -> dict:
    """
    Pre-match next-goal probability model.
    Calculates the probability of the next goal being scored by
    team A or team B, based on xG and odds, at minute 0 (no dynamic motivation).

    Args:
        xg_a: Expected goals for team A (from odds or model).
        xg_b: Expected goals for team B (implied lambda).
        odds_a: Decimal odds for next goal by team A.
        odds_b: Decimal odds for next goal by team B.
        is_home_a: Whether team A is home (default True).

    Returns:
        dict with Prob_A, Prob_B, EV_A, EV_B, xg_a, xg_b
    """
    # Home advantage
    home_factor_a = 1.1 if is_home_a else 0.9
    home_factor_b = 0.9 if is_home_a else 1.1

    # Offensive power
    off_a = xg_a * home_factor_a
    off_b = xg_b * home_factor_b

    total = off_a + off_b
    if total == 0:
        return {"Prob_A": 0.5, "Prob_B": 0.5, "EV_A": 0, "EV_B": 0}

    prob_a = off_a / total
    prob_b = off_b / total

    # Expected Value
    ev_a = (prob_a * odds_a) - 1
    ev_b = (prob_b * odds_b) - 1

    return {
        "Prob_A": round(prob_a, 4),
        "Prob_B": round(prob_b, 4),
        "EV_A": round(ev_a, 4),
        "EV_B": round(ev_b, 4),
        "xg_a": xg_a,
        "xg_b": xg_b
    }


if __name__ == "__main__":
    result = pregame_model(
        xg_a=1.5,
        xg_b=1.0,
        odds_a=2.0,
        odds_b=2.5,
        is_home_a=True
    )
    print("=== PRE-MATCH MODEL OUTPUT ===")
    for k, v in result.items():
        print(f"  {k}: {v}")
