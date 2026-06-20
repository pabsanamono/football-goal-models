# 🚅 football-goal-models

Modelos de probabilidad para el proximo gol y marcador correcto en futbol, basados en xG (expected goals) odds del mercado.

---

## 📚 Archivos

| Archivo | Descripcion |
|---|---|
| `pregame_model.py` | Modelo pre-partido | minuto 0, sin motivacion dinamica |
| `live_model.py` | Modelo en vivo | minuto real, score, motivacion dinamica |
| `monte_carlo_model.py` | Simulador Monte Carlo | marcador correcto por simulacion |

---

## 📋 `pregame_model.py` — Modelo Pre-Partido

### ¡Para que sirve?

Calcula la probabilidad de que el proximo gol lo meta el equipo A o el equipo B, antes de que comience el partido. Usa xG y ventaja de local. No incluye motivacion dinamica.

### Parametros

| Parametro | Tipo | Descripcion |
|---|---|---|
| `xg_a` | float | Expected goals del equipo A |
| `xg_b` | float | Expected goals del equipo B |
| `odds_a` | float | Odds decimales proximo gol equipo A |
| `odds_b` | float | Odds decimales proximo gol equipo B |
| `is_home_a` | bool | Si el equipo A es local (default: True) |

### Ejemplo

```python
from pregame_model import pregame_model

result = pregame_model(
    xg_a=1.5,
    xg_b=1.0,
    odds_a=2.0,
    odds_b=2.5,
    is_home_a=True
)
print(result)
```

| Campo | Descripcion |
|---|---|
| `Prob_A` | Probabilidad del proximo gol para el equipo A |
| `Prob_B` | Probabilidad del proximo gol para el equipo B |
| `EV_A` | Valor expectado apostando a A (+ = valor) |
| `EV_B` | Valor expectado apostando a B (+ = valor) |

---

## 📹 `live_model.py` — Modelo En Vivo

### ¡Para que sirve?

Calcula la probabilidad del proximo gol durante el partido, ajustando la motivacion segun el marcador y minuto actual.

### Parametros

| Parametro | Tipo | Descripcion |
|---|---|---|
| `xg_a` | float | xG base del equipo A |
| `xg_b` | float | xG base del equipo B |
| `odds_a` | float | Odds proximo gol equipo A |
| `odds_b` | float | Odds proximo gol equipo B |
| `minute` | int | Minuto actual (0-90) |
| `score_a` | int | Goles actuales equipo A |
| `score_b` | int | Goles actuales equipo B |
| `is_home_a` | bool | Si el equipo A es local |
| `shots_a` | float | Tiros reales equipo A (opcional) |
| `shots_b` | float | Tiros reales equipo B (opcional) |

### Ejemplo

```python
from live_model import live_model

result = live_model(
    xg_a=1.5,
    xg_b=1.0,
    odds_a=2.0,
    odds_b=3.0,
    minute=60,
    score_a=0,
    score_b=1,
    is_home_a=True,
    shots_a=8,
    shots_b=3
)
print(result)
```

| Campo | Descripcion |
|---|---|
| `Prob_A` | Probabilidad del proximo gol para A |
| `Prob_B` | Probabilidad del proximo gol para B |
| `EV_A` | Valor esperado apostando a A |
| `EV_B` | Valor esperado apostando a B |
| `motivation_a` | Multiplicador de motivacion equipo A |
| `motivation_b` | Multiplicador de motivacion equipo B |

---

## 📇 `monte_carlo_model.py` — Simulador Monte Carlo

### ¡Para que sirve?

En lugar de calcular probabilidades con formulas, simula el partido miles de veces y cuenta cuantas veces ocurre cada marcador. El resultado es una distribucion empirica de probabilidades.

### Como funciona

1. Para cada simulacion se generan un numero aleatorio de goles para cada equipo usando la distribucion Poisson
2. Se registra el marcador final de cada simulacion
3. Al final se divide la frecuencia de cada marcador entre el total de simulaciones

> A mayor numero de simulaciones, mayor precision. Recomendado minimo 100,000.

### Parametros

| Parametro | Tipo | Default | Descripcion |
|---|---|---|---|
| `lambda_home` | float | - | Goles esperados equipo local |
| `lambda_away` | float | - | Goles esperados equipo visitante |
| `max_goals` | int | 10 | Maximo de goles registrados individualmente |
| `n_simulations` | int | 100000 | Numero de simulaciones |

### Ejemplo basico

```python
from monte_carlonmodel import monte_carlo_score_probabilities, match_outcomes

score_probs = monte_carlo_score_probabilities(
    lambda_home=1.4,
    lambda_away=0.7,
    n_simulations=100000
)

# Top 15 marcadores mas probables
for score, prob in list(score_probs.items())[:15]:
    print(f"{score}: {prob*100:.3f}%")

# Resultados 1X2
outcomes = match_outcomes(score_probs)
print(outcomes)
```

### Salida esperada

```
Simulando partido con xG local = 1.4 | xG visitante = 0.7
----------------------------------------

== PROBABILIDADES DE MARCADOR (Top 15) ==
  1-0: 17.423%
  2-0: 12.468%
  1-1: 11.303%
  0-0: 9.295%
  2-1: 8.539%
  0-1: 6.123%
  3-0: 5.921%
  ...

== RESULTADOS FINALES 1;X2 ==
  Home_win: 59.81%
  Draw: 21.23%
  Away_win: 18.96%
```

### Funciones incluidas

| Funcion | Descripcion |
|---|---|
| `poisson_rv(lmbda)` | Generador Poisson puro Python sin dependencias externas |
| `monte_carlo_score_probabilities()` | Simulacion principal | devuelve diccionario de marcadores con probabilidades |
| `match_outcomes(score_probs)` | Calcula probabilidad de local gana, empate, visitante gana (1X2) |

---

## 📅 Cuando usar cada modelo

| Situacion | Modelo recomendado |
|---|---|
| Antes del partido (lineas pre-match) | `pregame_model` |
| Durante el partido, mercado in-play | `live_model` |
| Simulacion de marcadores y resultados | `monte_carlo_model` |
| Deteccion de valor con mucha incertidumbre | `monte_carlo_model` |
| Sin datos en vivo disponibles | `pregame_model` |

---

## 💑 Interpretacion del EV

- **EV > 0**: Hay valor apostando a ese resultado
- **EV = 0**: Apuesta justa, sin ventaja
- **EV < 0**: La casa tiene ventaja, no hay valor

---

## 💡 Licencia

MIT – Libre para uso personal y comercial.
