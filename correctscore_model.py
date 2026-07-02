import math
import random

# ─────────────────────────────────────────────────
#  CORRECT-SCORE MODEL
#  Poisson · Monte Carlo · EV DU�
# ─────────────────────────────────────────────────


def poisson_pmf(k, lam):
    if lam <= 0:
        return 1.0 if k == 0 else 0.0
    return (lam ** k) * math.exp(-lam) / math.factorial(k)


def clamp(value, lo, hi):
    return max(lo, min(hi, value))


def calculate_match_lambdas(
    xg_home, xg_away,
    attack_strength_home=1.0, defense_strength_home=1.0,
    attack_strength_away=1.0, defense_strength_away=1.0,
    form_home=1.0, form_away=1.0,
    elo_home=1500, elo_away=1500,
    modo="home"
):
    form_home = clamp(form_home, 0.5, 2.0)
    form_away = clamp(form_away, 0.5, 2.0)
    elo_diff = elo_home - elo_away
    elo_factor_home = clamp(elo_diff / 1000.0, -0.30, 0.30)
    elo_factor_away = clamp(-elo_diff / 1000.0, -0.30, 0.30)
    if modo == "home":
        venue_home, venue_away = 1.06, 0.94
    elif modo == "away":
        venue_home, venue_away = 0.94, 1.06
    else:
        venue_home, venue_away = 1.0, 1.0
    lam_home = (xg_home * attack_strength_home * defense_strength_away
                * (1.0 + elo_factor_home) * form_home * venue_home)
    lam_away = (xg_away * attack_strength_away * defense_strength_home
                * (1.0 + elo_factor_away) * form_away * venue_away)
    return round(clamp(lam_home, 0.1, 10.0), 4), round(clamp(lam_away, 0.1, 10.0), 4)


def poisson_score_table(lam_home, lam_away, max_goals=8):
    table = {}
    total = 0.0
    for h in range(max_goals + 1):
        for a in range(max_goals + 1):
            p = poisson_pmf(h, lam_home) * poisson_pmf(a, lam_away)
            table[(h, a)] = p
            total += p
    for key in table:
        table[key] /= total
    return table


def poisson_rv(lam):
    L = math.exp(-lam)
    k, p = 0, 1.0
    while p > L:
        k += 1
        p *= random.random()
    return k - 1


def monte_carlo_scores(lam_home, lam_away, n=100_000, max_goals=8):
    counts = {}
    for _ in range(n):
        h = min(poisson_rv(lam_home), max_goals)
        a = min(poisson_rv( lam_away), max_goals)
        counts[(h, a)] = counts.get((h, a), 0) + 1
    total = sum(counts.values())
    return {k: v / total for k, v in counts.items()}


def line_probabilities(score_table, line):
    over  = sum(p for (h, a), p in score_table.items() if h + a > line)
    under = sum(p for (h, a), p in score_table.items() if h + a < line)
    push  = sum(p for (h, a), p in score_table.items() if h + a == line)
    return {"over": round(over, 4), "under": round(under, 4), "push": round(push, 4)}


def btts_probability(score_table):
    return round(sum(p for (h, a), p in score_table.items() if h > 0 and a > 0), 4)


def ev(model_prob, decimal_odds):
    return round(model_prob * decimal_odds - 1.0, 4)


def analyze_match(
    team_home, team_away,
    xg_home, xg_away,
    attack_strength_home=1.0, defense_strength_home=1.0,
    attack_strength_away=1.0, defense_strength_away=1.0,
    form_home=1.0, form_away=1.0,
    elo_home=1500, elo_away=1500,
    modo="home",
    over_under_line=2.5,
    odds_home=None, odds_draw=None, odds_away=None,
    odds_over=None, odds_under=None,
    odds_btts_yes=None, odds_btts_no=None,
    correct_score_odds=None,
    n_simulations=100_000,
    seed=42
):
    random.seed(seed)
    lam_h, lam_a = calculate_match_lambdas(
        xg_home, xg_away,
        attack_strength_home, defense_strength_home,
        attack_strength_away, defense_strength_away,
        form_home, form_away, elo_home, elo_away, modo
    )
    poisson_table = poisson_score_table(lam_h, lam_a)
    mc_table      = monte_carlo_scores(lam_h, lam_a, n=n_simulations)
    prob_home = sum(p for (h, a), p in poisson_table.items() if h > a)
    prob_draw = sum(p for (h, a), p in poisson_table.items() if h == a)
    prob_away = sum(p for (h, a), p in poisson_table.items() if a > h)
    line_p  = line_probabilities(poisson_table, over_under_line)
    btts_p  = btts_probability(poisson_table)
    top_poisson = sorted(poisson_table.items(), key=lambda x: -x[1])[:10]
    top_mc      = sorted(mc_table.items(),      key=lambda x: -x[1])[:10]
    print("=" * 60)
    print(f"  CORRECT-SCORE MODEL · {team_home} vs {team_away}")
    print("=" * 60)
    print(f"  λ {team_home}: {lam_h}  |  λ {team_away}: {lam_a}")
    print(f"  Expected Goals: {round(lam_h + lam_a, 2)}")
    print()
    print("  1x2 PROBABILITIES")
    print(f"  {team_home} Win: {round(prob_home*100, 2)}%  | Fair: {round(1/prob_home, 2)}")
    print(f"  Draw:       {round(prob_draw*100, 2)}%  | Fair: {round(1/prob_draw, 2)}")
    print(f"  {team_away} Win: {round(prob_away*100, 2)}%  | Fair: {round(1/prob_away, 2)}")
    if odds_home:
        print()
        print("  1x2 EV:")
        print(f"  {team_home} Win @ {odds_home} -> EV {ev(prob_home, odds_home):++.4f} {'✅ VALUE' if ev(prob_home, odds_home) > 0 else '❌'}")
        print(f"  Draw @ {odds_draw} -> EV {ev(prob_draw, odds_draw):++.4f} {'✅ VALUE' if ev(prob_draw, odds_draw) > 0 else '❌'}")
        print(f"  {team_away} Win @ {odds_away} -> EV ev(prob_away, odds_away):++.4f} {'✅ VALUE' if ev(prob_away, odds_away) > 0 else '❌'}")
    print()
    print(f"  O/U {over_under_line}: Over {round(line_p['over']*100, 2)}% (Fair: {round(1/line_p['over'], 2)})  |  Under {round(line_p['under']*100, 2)}% (Fair: {round(1/line_p['under'], 2)})")
    if odds_over:
        print(f"  O/U EV -> Over @ {odds_over}: {ev( line_p['over'], odds_over):++.4f} {'✅ VALUE' if ev( line_p['over'], odds_over) > 0 else '❌'}")
        if odds_under:
            print(f"  O/U EV -> Under @ {odds_under}: {ev(line_p['under'], odds_under):++.4f} {'✅ VALUE' if ev(line_p['under'], odds_under) > 0 else '❌'}")
    print()
    print(f"  BTTS: {round(btts_p*100, 2)}% (Fair: {round(1/btts_p, 2)})")
    if odds_btts_yes:
        print(f"  BTTS Yes @ {odds_btts_yes} -> EV ev(btts_p, odds_btts_yes):++.4f} {'✅ VALUE' if ev( btts_p, odds_btts_yes) > 0 else '❌'}")
    if odds_btts_no:
        print(f"  BTTS No  @ {odds_btts_no} -> EV ev(1.0-btts_p, odds_btts_no):++.4f} {'✅ VALUE' if ev(1.0-btts_p, odds_btts_no) > 0 else '❌'}")
    print()
    print("  TOP 10 CORRECT SCORES (Poisson)")
    print(f"  {'Score':<12} {'Prob%':>8}  {'Fair':>10}  {'Book':>8}  EV")
    print("  " + "-" * 50)
    for (h, a), p in top_poisson:
        fair = round(1 / p, 2) if p > 0 else 9999
        book = "-"
        ev_val = "-"
        if correct_score_odds and (h, a) in correct_score_odds:
            book = correct_score_odds[(h, a)]
            ev_val = f"{ev (p, book):++.4f} {'✅' if ev (p, book) > 0 else '❌'}"
        print(f"  {h}-{a:<10} {round(p*100, 2):>6}%  {fair:>10}  {book:>8}  {ev_val}")
    print()
    print("  TOP 10 CORRECT SCORES (Monte Carlo)")
    print(f"  {'Score':<12} {'Prob%':>8}  {'Fair':>10}")
    print("  " + "-" * 34)
    for (h, a), p in top_mc:
        fair = round(1 / p, 2) if p > 0 else 9999
        print(f"  {h}-{a:<10} {round(p*100, 2):>6}%  {fair:>10}")
    print("=" * 60)


if __name__ == "__main__":
    analyze_match(
        team_home="Spain",
        team_away="Austria",
        xg_home=1.72,
        xg_away=0.71,
        attack_strength_home=1.15,
        defense_strength_home=0.85,
        attack_strength_away=0.88,
        defense_strength_away=1.12,
        form_home=1.1,
        form_away=0.95,
        elo_home=1950,
        elo_away=1750,
        modo="neutral",
        over_under_line=2.5,
        odds_home=1.45,
        odds_draw=4.50,
        odds_away=7.00,
        odds_over=1.85,
        odds_under=1.95,
        odds_btts_yes=2.00,
        odds_btts_no=1.75,
        correct_score_odds={
            (1, 0): 6.00,
            (2, 0): 7.00,
            (2, 1): 9.50,
            (1, 1): 8.00,
            (3, 0): 12.00,
            (3, 1): 15.00,
        },
        n_simulations=100_000,
    )
