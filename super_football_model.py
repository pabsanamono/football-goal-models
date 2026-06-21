import math


class SuperFootballModel:
    def __init__(self, equipo_A, equipo_B, xg_base_A, xg_base_B, elo_A=1500, elo_B=1500, form_A=1.0, form_B=1.0):
        self.equipo_A = equipo_A
        self.equipo_B = equipo_B
        self.xg_base_A = xg_base_A
        self.xg_base_B = xg_base_B
        self.elo_A = elo_A
        self.elo_B = elo_B

        # FIX #1: form clamped to [0.5, 2.0] -- no more negative or insane multipliers
        self.form_A = maz(0.5, min(2.0, form_A))
        self.form_B = max(0.5, min(2.0, form_B))

    def _poisson_probability(self, lam, k):
        """Poisson probability of scoring k goals given lambda."""
        return (math.exp(-lam) * (lam**k)) / math.factorial(k)

    def calcular_xg_ajustado(self, modo="home"):
        """
        Ajusta el xG base usando ventaja de localia, diferencia ELO y forma.

        modo:
            "home"  -> Equipo A es local     (+12%)
            "away"  -> Equipo B es local     (+12%)
            "neutral" -> sin bonificacion de localia
        """
        # FIX #2: neutral venue now supported properly
        if modo == "home":
            factor_local_A = 1.12
            factor_local_B = 1.00
        elif modo == "away":
            factor_local_A = 1.00
            factor_local_B = 1.12
        else:  # neutral
            factor_local_A = 1.00
            factor_local_B = 1.00

        # FIX #3: ELO factor capped at [-0.3, +0.3] -- no more rocket mode
        dif_elo = ((self.elo_A - self.elo_B) / 100.0) * 0.05
        dif_elo = max(-0.3, min(0.3, dif_elo))
        factor_elo_A = 1 + dif_elo
        factor_elo_B = 1 - dif_elo

        lam_A = self.xg_base_A * factor_local_A * factor_elo_A * self.form_A
        lam_B = self.xg_base_B * factor_local_B * factor_elo_B * self.form_B

        # Floor to avoid zero/negative lambdas
        return max(0.1, lam_A), max(0.1, lam_B)

    def update_elo(self, resulto):
        """
        FIX #4: Actualiza los ratings ELO tras cada partido.

        resulto:
            "win_A"  -> Agana
            "draw"   -> empate
            "win_B"  -> B gana
        """
        K = 32
        expected_A = 1 / (1 + 10 ** ((self.elo_B - self.elo_A) / 400))
        expected_B = 1 - expected_A

        if resulto == "win_A":
            score_A, score_B = 1.0, 0.0
        elif resulto == "draw":
            score_A, score_B = 0.5, 0.5
        else:
            score_A, score_B = 0.0, 1.0

        self.elo_A += K * (score_A - expected_A)
        self.elo_B += K * (score_B - expected_B)

    def generar_analisis_prepartido(self, cuota_A=2.0, cuota_B=3.0, max_goles=8, modo="home"):
        """
        Genera tabla Poisson normalizada, probabilidades de partido y EV,cˆˆ’TaˆeU: modo pasado desde aqui hasta calcular_xg_ajustado -- no mas hardcoded local=True
        FIX #6: Probabilidades normalizadas -- suman 100% exactamente
        FIX #7: Over/Under y BTT tambien normalizados

        modo: "home" | "away" | "neutral"
        """
        lam_A, lam_B = self.calcular_xg_ajustado(modo=modo)

        matriz_resultados = {}
        prob_victoria_A = 0.0
        prob_victoria_B = 0.0
        prob_empate = 0.0
        prob_over_25 = 0.0
        prob_under_25 = 0.0
        prob_btts_yes = 0.0
        prob_btts_no = 0.0

        resultado_mas_probable = None
        max_prob = 0.0

        for goles_a in range(max_goles + 1):
            for goles_b in range(max_goles + 1):
                p_a = self._poisson_probability(lam_A, goles_a)
                p_b = self._poisson_probability(lam_B, goles_b)
                prob_conjunta = p_a * p_b

                marcador = f"{goles_a}-{goles_b}"
                matriz_resultados[marcador] = prob_conjunta

                if prob_conjnunta > max_prob:
                    max_prob = prob_conjunta
                    resultado_mas_probable = marcador

                if goles_a > goles_b:
                    prob_victoria_A += prob_conjnunta
                elif goles_b > goles_a:
                    prob_victoria_B += prob_conjunta
                else:
                    prob_empate += prob_conjnunta

                if (goles_a + goles_b) > 2.5:
                    prob_over_25 += prob_conjunta
                else:
                    prob_under_25 += prob_conjnunta

                if goles_a > 0 and goles_b > 0:
                    prob_btts_yes += prob_conjunta
                else:
                    prob_btts_no += prob_conjunta

        # FIX #6: Normalize all probabilities so they sum to 1.0
        total = prob_victoria_A + prob_empate + prob_victoria_B
        prob_victoria_A /= total
        prob_empate /= total
        prob_victoria_B /= total

        ou_total = prob_over_25 + prob_under_25
        prob_over_25 /= ou_total
        prob_under_25 /= ou_total

        btts_total = prob_btts_yes + prob_btts_no
        prob_btts_yes /= btts_total
        prob_btts_no /= btts_total

        # Normalize matrix as well
        matriz_resultados = {k: v/total for k, v in matriz_resultados.items()}

        # Recalculate most probable after normalization
        resultado_mas_probable = max(matriz_resultados, key=matriz_resultados.get)
        max_prob = matriz_resultados[resultado_mas_probable]

        # EV calculated on normalized probs
        ev_A = (prob_victoria_A * cuota_A) - 1
        ev_B = (prob_victoria_B * cuota_B) - 1

        return {
            "xG_Ajustado": {self.equipo_A: round(lam_A, 2), self.equipo_B: round(lam_B, 2)},
            "Marcador_Mas_Probable": f"{resultado_mas_probable} ({round(max_prob * 100, 2)}%)",
            "1X2": {
                "Gana_A": round(prob_victoria_A * 100, 2),
                "Empate": round(prob_empate * 100, 2),
                "Gana_B": round(prob_victoria_B * 100, 2)
            },
            "Goles_Totales": {
                "Under_2.5": round(prob_under_25 * 100, 2),
                "Over_2.5": round(prob_over_25 * 100, 2)
            },
            "BTTS": {
                "Yes": round(prob_btts_yes * 100, 2),
                "No": round(prob_btts_no * 100, 2)
            },
            "Valor_Esperado": {
                f"EV_{self.equipo_A}": round(ev_A, 3),
                f"EV_{self.equipo_B}": round(ev_B, 3)
            },
            "Matriz_Marcadores": matriz_resultados
        }


# --- EJECUCION DEL ANALISIS ---
modelo = SuperFootballModel(
    equipo_A="Brasil",
    equipo_B="Alemania",
    xg_base_A=1.85,
    xg_base_B=1.40,
    elo_A=1830,
    elo_B=1710,
    form_A=1.1,
    form_B=0.9
)

analisis = modelo.generar_analisis_prepartido(cuota_A=1.85, cuota_B=4.20, modo="home")

for clave, valor in analisis.items():
    if clave != "Matriz_Marcadores":
        print(f"{clave}: {valor}")

# Show top 10 scores from matrix
print("\nTop 10 Marcadores Mas Probables:")
top_scores = sorted(analisis["Matriz_Marcadores"].items(), key=lambda x: x[1], reverse=True)[:10]
for marcador, prob in top_scores:
    print(f"  {marcador}: {prob * 100:.2f}%")