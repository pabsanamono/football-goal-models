import math

def live_model(
    xg_a: float,
    xg_b: float,
    odds_a: float,
    odds_b: float,
    minute: int,
    score_a: int = 0,
    score_b: int = 0,
    is_home_a: bool = True,
    shots_a: float = None,
    shots_b: float = None
) -> dict:
    """
    Live (in-play) next-goal probability model.
    Adjusts xG with dynamic motivation based on score and minute.

    Args:
        xg_a: Expected goals for team A.
        xg_b: Expected goals for team B.
        odds_a: Decimal odds for next goal by team A.
        odds_b: Decimal odds for next goal by team B.
        minute: Current match minute (0-90).
        score_a: Current goals scored by team A.
        score_b: Current goals scored by team B.
        is_home_a: Whether team A is home (default True).
        shots_a: Real-time shots for team A (optional).
        shots_b: Real-time shots for team B (optional).

    Returns:
        dict with Prob_A, Prob_B, EV_A, EV_B, motivation_a, motivation_b
    """
    # Home advantage
    home_factor_a = 1.1 if is_home_a else 0.9
    home_factor_b = 0.9 if is_home_a else 1.1

    # Real-time stats adjustment
    if shots_a is not None and shots_b is not None and (shots_a + shots_b) > 0:
        shot_ratio_a = shots_a / (shots_a + shots_b)
        shot_ratio_b = shots_b / (shots_a + shots_b)
        xg_a = xg_a * (0.5 + shot_ratio_a)
        xg_b = xg_b * (0.5 + shot_ratio_b)

    # Offensive power
    off_a = xg_a * home_factor_a
    off_b = xg_b * home_factor_b

    # Dynamic motivation based on score & minute
    diff = score_a - score_b
    urgency = minute / 90

    if diff < 0:  # Team A losing
        motivation_a = 1.0 + (0.3 * urgency * abs(diff))
        motivation_b = 1.0
    elif diff > 0:  # Team B losing
        motivation_a = 1.0
        motivation_b = 1.0 + (0.3 * urgency * abs(diff))
    else:  # Draw
        motivation_a = 1.0
        motivation_b = 1.0

    off_a *= motivation_a
    off_b *= motivation_b

    total = off_a + off_b
    if total == 0:
        return {"Prob_A": 0.5, "Prob_B": 0.5, "EV_A": 0, "EV_B": 0}

    prob_a = off_a / total
    prob_b = off_b / total

    ev_a = (prob_a * odds_a) - 1
    ev_b = (prob_b * odds_b) - 1

    return {
        "Prob_A": round(prob_a, 4),
        "Prob_B": round(prob_b, 4),
        "EV_A": round(ev_a, 4),
        "EV_B": round(ev_b, 4),
        "motivation_a": round(motivation_a, 4),
        "motivation_b": round(motivation_b, 4)
    }


if __name__ == "__main__":
    result = live_model(
        xg_a=1.5,
        xg_b=1.0,
        odds_a=2.0,
        odds_b=2.5,
        minute=45,
        score_a=0,
        score_b=1,
        is_home_a=True
    )
    print("=== LIVE MODEL OUTPUT (team A losing 0-1 at '45) ===")
    for k, v in result.items():
        print(f"  {k}: {v}")
