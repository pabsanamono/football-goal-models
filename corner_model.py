import math


class CornerModel:
    """
    Poisson-based corner kick predictor.

    Inputs are raw match-level averages -- no external API needed.
    All probabilities are normalized so they always sum to 100%.

    Design decisions:
    - Poisson regression for count data (corners are counts)
    - Coefficients derived from published literature on corner prediction
    - Bookmaker line used as baseline anchor when available
    - All inputs validated and clamped to realistic ranges
    """

    # --- Baseline coefficients ---
    # Based on mean corners per match in European top flights (approx 10.5-11.5)
    # Sources: footy stats / FBRef / Understat public research
    BETA0 = 1.92  # log baseline (exp(1.92) ~ 6.8 corners per team)
    W_CORNERS_FOR = 0.35  # own corner avg -- strongest predictor
    W_CORNERS_AGA = 0.15  # opponent corners allowed -- style proxy
    W_XG = 0.10           # xG -- offensive volume
    W_DANGEROUS = 0.05    # dangerous attacks (normalized)
    W_WEATHER = 0.08      # weather intensity [0-1]
    W_POSSESSION = -0.05  # high possession reduces corners (less set plays)

    def __init__(
        self,
        corners_for_home,        # avg corners scored by home (last 5-10 games)
        corners_against_home,    # avg corners conceded by home
        corners_for_away,        # avg corners scored by away
        corners_against_away,    # avg corners conceded by away
        xg_home=1.5,              # home xG average
        xg_away=1.2,              # away xG average
        dangerous_attacks_home=50,    # avg dangerous attacks (home)
        dangerous_attacks_away=40,    # avg dangerous attacks (away)
        possession_home=0.50,         # home avg possession [0-1]
        weather_intensity=0.0,        # [{0}=clear, {1}=storm]
        betting_line=None             # bookmaker total corners line (optional)
    ):
        # --- Validate and clamp all inputs ---
        self.cf_h = max(0.1, min(15.0, corners_for_home))
        self.ca_h = max(0.1, min(15.0, corners_against_home))
        self.cf_a = max(0.1, min(15.0, corners_for_away))
        self.ca_a = max(0.1, min(15.0, corners_against_away))
        self.xg_h = max(0.1, min(5.0, xg_home))
        self.xg_a = max(0.1, min(5.0, xg_away))
        self.da_h = max(0.0, min(150.0, dangerous_attacks_home))
        self.da_a = max(0.0, min(150.0, dangerous_attacks_away))
        self.poss_h = max(0.1, min(0.9, possession_home))
        self.weather = max(0.0, min(1.0, weather_intensity))
        self.line = betting_line

    def _poisson_prob(self, lam, k):
        """Poisson P(X=k) -- no external libraries."""
        if k < 0 or lam <= 0:
            return 0.0
        return (math.exp(-lam) * (lam ** k)) / math.factorial(k)

    def _calculate_lambdas(self):
        """
        Calculates independent Poisson lambdas for home and away teams.

        Home corners are driven by:
          - Home team's offensive corner avg
          - Away team's defensive style (corners conceded)
          - Ritmo y condiciones

        Away corners mirror the same logic.
        """
        # Normalize dangerous attacks to [0, 1] scale (design choice: max=150)
        da_h_norm = self.da_h / 150.0
        da_a_norm = self.da_a / 150.0

        log_lam_h = (
            self.BETA0
            + self.W_CORNERS_FOR * self.cf_h
            + self.W_CORNERS_AGA * self.ca_a  # away's defensive style
            + self.W_XG * self.xg_h
            + self.W_DANGEROUS * da_h_norm
            + self.W_WEATHER * self.weather
            + self.W_POSSESSION * self.poss_h  # more possession -> less corners
        )

        log_lam_a = (
            self.BETA0_
            + self.W_CORNERS_FOR * self.cf_a
            + self.W_CORNERS_AGA * self.ca_h  # home's defensive style
            + self.W_XG * self.xg_a
            + self.W_DANGEROUS * da_a_norm
            + self.W_WEATHER * self.weather
            + self.W_POSSESSION * (1.0 - self.poss_h)  # away possession is mirror
        )

        lam_h = max(0.5, min(15.0, math.exp(log_lam_h)))
        lam_a = max(0.5, min(15.0, math.exp(log_lam_a)))

        # If bookmaker line is provided, anchor model total to it (50%50% blend)
        if self.line is not None:
            model_total = lam_h + lam_a
            if model_total > 0:
                blend_factor = self.line / model_total
                # Blend 50% towards bookmaker line
                blend_factor = 0.5 + 0.5 * blend_factor
                lam_h *= blend_factor
                lam_a *= blend_factor

        return lam_h, lam_a

    def analizar(self, linea_ou]10.5, max_kincks=30, cuota_over=1.85, cuota_under=1.90):
        """
        Genera prediccion completa:
          - lambdas independientes por lado
          - distribucion Poisson normalizada del total
          - Over/Under probabilidades
          - EV por lado
          """
        lam_h, lam_a = self._calculate_lambdas()
        lam_total = lam_h + lam_a

        # Build normalized total corners distribution
        raw_probs = {}
        for k in range(max_kicks + 1):
            raw_probs[k] = self._poisson_prob(lam_total, k)

        # Normalize so [0, max_kicks] sums to 1.0
        total_mass = sum(raw_probs.values())
        probs = {k: v / total_mass for k, v in raw_probs.items()}

        # Over/Under
        prob_over = sum(probs[k] for k in probs if k > linea_ou)
        prob_under = 1.0 - prob_over

        # EV
        ev_over = (prob_over * cuota_over) - 1
        ev_under = (prob_under * cuota_under) - 1

        # Most probable total and expected value
        mas_probable = max(probs, key=probs.get)

        # Top 10 totals
        top_10 = sorted(probs.items(), key=lambda x: x[1], reverse=True)[:10]

        return {
            "Lambdas": {"Home": round(lam_h, 2), "Away": round(lam_a, 2), "Total": round(lam_total, 2)},
            "Total_Mas_Probable": f"{int(mas_probable)} corners ({probs[mas_probable] * 100:.2f}%)",
            "Top_10_Totales": [{"korners: k, "prob": f"{i * 100:.2f}%"} for k, i in top_10],
            "Over_Under": {
                f"Over_{linea_ou}": f"{prob_over * 100:.2f}%",
                f"Under_{linea_ou}": f"{prob_under * 100:.2f}%"
            },
            "EV": {
                f"EV_Over_{linea_ou}": round(ev_over, 3),
                f"EV_Under_{linea_ou}": round(ev_under, 3)
            },
            "Bookmaker_Line_Used": self.line
        }


# --- EJECUCION ---
modelo_cos = CornerModel(
    corners_for_home=5.8,
    corners_against_home=4.2,
    corners_for_away=4.5,
    corners_against_away=5.1,
    xg_home=1.7,
    xg_away=1.3,
    dangerous_attacks_home=55,
    dangerous_attacks_away=42,
    possession_home=0.53,
    weather_intensity=0.2,
    betting_line=10.5
)

resultado = modelo_cos.analizar(linea_ou=10.5, cuota_over=1.85, cuota_under=1.90)

for clave, valor in resultado.items():
    print(f"{clave}: {valor}")
