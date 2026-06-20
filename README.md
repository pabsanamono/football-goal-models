# 🚅 football-goal-models

Modelos de probabilidad para el proximo gol en un partido de futbol, basados en xG (expected goals) odds del mercado.

Se compone de dos modelos independientes:

- `pregame_model.py` — Analisis pre-partido (minuto 0)
- `live_model.py` — Analisis en vivo (in-play)

---

## 📠 Prerequisitos

Solo se necesita Python 3.x+. No requiere librerias externas.

```bash
git clone https://github.com/pabsanamono/football-goal-models.git
cd football-goal-models
```

---

## 📋 `pregame_model.py` — Modelo Pre-Partido

### ¡Para que sirve?

Calcula la probabilidad de que el proximo gol lo meta el equipo A o el equipo B, antes de que comience el partido. Usa xG y ventaja de local. No incluye motivacion dinamica.

### Parametros

| Parametro | Tipo | Descripcion |
|---|---|---|
| `xg_a` | float | Expected goals del equipo A (lambda del modelo Poisson) |
| `xg_b` | float | Expected goals del equipo B |
| `odds_a` | float | Odds decimales para proximo gol del equipo A |
| `odds_b` | float | Odds decimales para proximo gol del equipo B |
| `is_home_a` | bool | Si el equipo A es local (default: True) |

### Estructura interna

1. Se aplica el factor de localia (+10% local, -10% visitante)
2. Se calcula el poder ofensivo de cada equipo
3. Se normaliza para obtener probabilidades
4. Se calcula el EV contra las odds del mercado

### Exemplo de uso

```python
from pregame_model import pregame_model

result = pregame_model(
    xg_a=1.5,            # lambda estimada equipo A
    xg_b=1.0,            # lambda estimada equipo B
    odds_a=2.0,          # odds proximo gol equipo A
    odds_b=2.5,          # odds proximo gol equipo B
    is_home_a=True       # equipo A es local
)

print(result)
```

### Salida esperada

```python
{
    "Prob_A": 0.6216,
    "Prob_B": 0.3784,
    "EV_A": 0.2432,
    "EV_B": -0.054,
    "xg_a": 1.5,
    "xg_b": 1.0
}
```

| Campo | Descripcion |
|---|---|
| `Prob_A` | Probabilidad del proximo gol para el equipo A |
| `Prob_B` | Probabilidad del proximo gol para el equipo B |
| `EV_A` | Valor esperado apostando al equipo A (+ = valor) |
| `EV_B` | Valor esperado apostando al equipo B (+ = valor) |
| `xg_a` | xG entrada equipo A |
| `xg_b` | xG entrada equipo B |

---

## 📹 `live_model.py` — Modelo En Vivo

### ¡Para que sirve?

Calcula la probabilidad del proximo gol durante el partido, ajustando la motivacion de cada equipo segun el marcador y el minuto actual. Opcionalmente usa estadisticas en vivo (tiros).

### Parametros

| Parametro | Tipo | Descripcion |
|---|---|---|
| `xg_a` | float | xG base del equipo A |
| `xg_b` | float | xG base del equipo B |
| `odds_a` | float | Odds decimales proximo gol equipo A |
| `odds_b` | float | Odds decimales proximo gol equipo B |
| `minute` | int | Minuto actual del partido (0-90) |
| `score_a` | int | Goles actuales equipo A (default: 0) |
| `score_b` | int | Goles actuales equipo B (default: 0) |
| `is_home_a` | bool | Si el equipo A es local (default: True) |
| `shots_a` | float | Tiros en lo que va del partido (opcional) |
| `shots_b` | float | Tiros en lo que va del partido (opcional) |

### Logica de motivacion

El modelo aumenta el poder ofensivo del equipo que va perdiendo, en funcion del minuto y la diferencia en el marcador:

```
motivation = 1.0 + (0.3 * urgency * gol_difference)
```

- A mas minutos y mayor diferencia -> mayor motivacion
- Si van empatados -> motivacion neutra (1.0)

### Ejemplo basico

```python
from live_model import live_model

# Equipo A perdiendo 0-1 al minuto 60
result = live_model(
    xg_a=1.5,
    xg_b=1.0,
    odds_a=2.0,
    odds_b=3.0,
    minute=60,
    score_a=0,
    score_b=1,
    is_home_a=True
)

print(result)
```

### Ejemplo con stats en vivo

```python
# Usando tiros reales del partido
result = live_model(
    xg_a=1.5,
    xg_b=1.0,
    odds_a=2.0,
    odds_b=3.0,
    minute=60,
    score_a=0,
    score_b=1,
    is_home_a=True,
    shots_a=8,           # tiros reales equipo A
    shots_b=3            # tiros reales equipo B
)

print(result)
```

### Salida esperada

```python
{
    "Prob_A": 0.7235,
    "Prob_B": 0.2765,
    "EV_A": 0.447,
    "EV_B": -0.17,
    "motivation_a": 1.2,
    "motivation_b": 1.0
}
```

| Campo | Descripcion |
|---|---|
| `Prob_A` | Probabilidad del proximo gol para el equipo A |
| `Prob_B` | Probabilidad del proximo gol para el equipo B |
| `EV_A` | Valor esperado apostando al equipo A (+ = valor) |
| `EV_B` | Valor expectado apostando al equipo B (+ = valor) |
| `motivation_a` | Multiplicador de motivacion aplicado al equipo A |
| `motivation_b` | Multiplicador de motivacion aplicado al equipo B |

---

## 📅 Cuando usar cada modelo?

| Situacion | Modelo recomendado |
|---|---|
| Antes del partido (lineas pre-match) | `pregame_model` |
| Durante el partido, mercado, in-play | `live_model` |
| Analisis de halftime (min. 45) | `live_model` |
| Sin datos en vivo disponibles | `pregame_model` |

---

## 💡 Interpretacion del EV

- **EV > 0**: Hay valor apostando a ese equipo
- **EV = 0**: Apoesta justa, sin ventaja
- **EV < 0**: La casa tiene ventaja, no hay valor

> Por ejemplo: EV_A = 0.2432 significa que por cada $100 apostado, se espera ganar $24.32 a largo plazo.

---

## 💡 Licencia

MIT – Libre para uso personal y comercial.
