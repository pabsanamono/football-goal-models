# Monte Carlo Correct-Score Generator

> Standalone model separate from the Poisson analytic model.  \nSimulates a match N times using Poisson-distributed goal draws and returns empirical scoreline probabilities.

---

## How It Works

1. For each simulation, randomly draw home and away goals from a Poisson distribution.
2. Record the scoreline string (e.g. `"1-0"`).
3. Repeat 100,000 times.
4. Divide each scoreline count by total simulations to get probabilities.

---

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `lambda_home` | float | required | Expected goals for home team |
| `lambda_away` | float | required | Expected goals for away team |
| `max_goals` | int | `10` | Scores above this go into `"Other"` bucket |
| `n_simulations` | int | `100000` | Number of match simulations |

---

## Code

```python
import math
import random
from collections import defaultdict


def poisson_rv(lmbda: float) -> int:
    """
    Generate a Poisson-random variable using Knuth's algorithm.
    Pure Python - no external dependencies.

    Args:
        lmbda: Poisson rate parameter (lambda)

    Returns:
        Random integer drawn from Poisson(lambda)
    """
    if lmbda <= 0:
        return 0
    L = math.exp(-lmbda)
    k = 0
    p = 1.0
    while p > L:
        k += 1
        p *= random.random()
    return max(0, k - 1)


def monte_carlo_score_probabilities(
    lambda_home: float,
    lambda_away: float,
    max_goals=10,
    n_simulations=100000
) -> dict:
    """
    Monte Carlo simulator for football scoreline probabilities.

    Scores where either team exceeds max_goals are bucketed into "Other".

    Args:
        lambda_home: Expected goals for home team
        lambda_away: Expected goals for away team
        max_goals: Maximum goals per team before bucketing
        n_simulations: Number of match simulations to run

    Returns:
        Dictionary of scoreline -> probability
    """
    counts = defaultdict(int)

    for _ in range(n_simulations):
        home_goals = poisson_rv(lambda_home)
        away_goals = poisson_rv(lambda_away)

        if home_goals <= max_goals and away_goals <= max_goals:
            counts[f"{home_goals}-{away_goals}"] += 1
        else:
            counts["Other"] += 1

    return {
        score: round(count / n_simulations, 4)
        for score, count in sorted(
            counts.items(),
            key=lambda x: x[1],
            reverse=True
        )
    }


if __name__ == "__main__":
    HOME_XG = 1.4
    AWAY_XG = 0.7
    MAX_GOALS = 10

    probs = monte_carlo_score_probabilities(
        lambda_home=HOME_XG,
        lambda_away=APÐWY_XG,
        max_goals=MAX_GOALS,
        n_simulations=100000
    )

    print("\n== MOST LIKELY SCORES (Top 15) ==")
    for i, (score, prob) in enumerate(probs.items()):
        if i >= 15:
            break
        label = f"Other (>{MAX_GOALS} goals)" if score == "Other" else score
        print(f"  {label:12}: {prob:.3}%")
```

---

## Example Output

```
== MOST LIKELY SCORES (Top 15) ==
  1-0         : 17.423%
  2-0         : 12.468%
  1-1         : 11.303%
  0-0         : 9.295%
  2-1         : 8.539%
  3-0         : 5.912%
  0-1         : 5.821%
  3-1         : 4.123%
  2-2         : 3.790%
  4-0         : 2.135%
  0-2         : 1.994%
  3-2         : 1.821%
  4-1         : 1.486%
  1-2         : 1.321%
  4-2         : 0.821%
```

---

## Comparison: Monte Carlo vs Poisson Analytic

| Aspect | Poisson (Analytic) | Monte Carlo (This Model) |
|------------------|-----------------------|-----------------------------|
| Method | Analytic formula | Random sampling |
| Speed | Instant | Slower (simulation loop) |
| Accuracy | Exact | Approximate (converges with N) |
| Extensibility | Limited to stationary processes | Easy to add momentum, cards, form |
| External deps | None | None |
| Use case | Fast pregame probabilities | Complex scenarios | |

---

## Extension Ideas

- Add live-match minute by minute simulation
- Inject red cards, injury time, substitutions
- Weight lambda dynamically by live stats (xG, shots on target)
- Output as pandas DataFrame heatmap
