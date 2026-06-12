# football-ml-predictor

Pipeline no interactivo para ingesta de datos de futbol, persistencia en SQLite, entrenamiento/versionado de modelos y generacion de predicciones reproducibles.

## Objetivo

Este proyecto construye un flujo batch de Machine Learning orientado a resultados:

- descarga o simula datos de partidos
- actualiza una base SQLite evitando duplicados
- genera features historicas sin data leakage
- reentrena un modelo clasificatorio
- versiona artefactos entrenados
- registra metricas y reportes
- expone predicciones futuras de manera opcional con FastAPI

No es un chatbot ni una IA conversacional.

## Arquitectura

```text
football-ml-predictor/
 app/
    config.py
    main.py
    database/
    ingestion/
    features/
    training/
    prediction/
    pipelines/
    reports/
 data/
 models/
 reports/
 tests/
```

Capas principales:

- `app/database`: engine SQLite, ORM SQLAlchemy y repositorios.
- `app/ingestion`: adapters externos reales y mocks de fallback.
- `app/features`: construccion de dataset historico y features para partidos futuros.
- `app/training`: entrenamiento temporal, evaluacion y registro/versionado.
- `app/prediction`: carga del modelo activo y generacion de probabilidades.
- `app/pipelines`: ejecucion batch de actualizacion diaria o reentrenamiento total.
- `app/reports`: exportacion de metricas en JSON.

## Instalacion

1. Crear entorno virtual:

```bash
python -m venv .venv
```

2. Activarlo.

3. Instalar dependencias:

```bash
pip install -r requirements.txt
```

4. Crear archivo `.env` a partir de `.env.example`.

## Configuracion

Variables relevantes:

- `DATABASE_URL`: URL SQLite.
- `MODEL_DIR`: carpeta de modelos.
- `REPORTS_DIR`: carpeta de reportes.
- `TEST_SIZE`: proporcion temporal para test.
- `MIN_TRAINING_ROWS`: minimo de filas para entrenar.
- `ENABLE_REAL_INGESTION`: habilita adapters reales.
- `ENABLE_PLAYER_STATUS`: habilita proveedor de lesiones/suspendidos.
- `FOOTBALL_DATA_API_KEY`: API key de football-data.org.
- `FOOTBALL_DATA_BASE_URL`: base URL del API de football-data.org.
- `OPEN_METEO_FORECAST_URL`: endpoint de clima futuro.
- `OPEN_METEO_HISTORICAL_URL`: endpoint de clima historico.
- `ELO_RATINGS_URL`: feed configurable para ratings Elo.

## Base de datos y Alembic

El proyecto usa SQLAlchemy ORM y deja la base lista mediante `init_db()`. Tambien incluye Alembic con una migracion inicial. La inicializacion aplica cambios aditivos minimos para no romper una base SQLite ya creada por versiones anteriores.

Tablas principales:

- `teams`
- `venues`
- `matches`
- `team_match_stats`
- `player_status`
- `weather_snapshots`
- `team_ratings`
- `predictions`
- `training_runs`
- `model_versions`

## Carga de datos iniciales

Por defecto el proyecto usa mocks:

- `MockMatchDataClient`
- `MockEloRatingClient`
- `MockWeatherClient`
- `MockPlayerStatusProvider`

Estos clientes no inventan atributos fuera del dataset definido. Si una fuente no provee lesiones, clima, ratings o stats, el sistema guarda `NULL` o defaults controlados.

## Real Data Sources

### football-data.org

Se usa para:

- competiciones
- equipos
- fixtures
- resultados
- partidos historicos
- partidos proximos

Configuracion minima:

```env
ENABLE_REAL_INGESTION=true
FOOTBALL_DATA_API_KEY=tu_api_key
FOOTBALL_DATA_BASE_URL=https://api.football-data.org/v4
FOOTBALL_DATA_COMPETITIONS=WC,EC
```

El adapter `app/ingestion/football_data_client.py` usa `X-Auth-Token`, timeout, manejo de errores HTTP y retry basico frente a `429`.

Como obtener API key:

1. Crear una cuenta en `football-data.org`.
2. Generar una API key desde el panel del usuario.
3. Copiarla al `.env` como `FOOTBALL_DATA_API_KEY`.

### Open-Meteo

Se usa para:

- clima futuro de partidos proximos
- clima historico de partidos ya jugados cuando la sede tiene coordenadas

Configuracion:

```env
OPEN_METEO_FORECAST_URL=https://api.open-meteo.com/v1/forecast
OPEN_METEO_HISTORICAL_URL=https://archive-api.open-meteo.com/v1/archive
```

Si el partido no tiene coordenadas de sede, el sistema no falla. Simplemente deja `weather` como missing.

### Ratings Elo / ranking

El proyecto deja un adapter configurable en `app/ingestion/elo_rating_client.py`. Por defecto usa `ELO_RATINGS_URL=https://www.eloratings.net/World.tsv` y registra la fuente como `world_football_elo`.

Si un rating no existe para un equipo, se deja missing controlado. No se inventan valores.

### Lesiones / suspendidos

La interfaz queda preparada en `app/ingestion/player_status_provider.py`, con:

- adapter mock actual
- placeholder para proveedor pago

Para datos reales de lesiones, alineaciones o suspendidos normalmente hace falta un proveedor con cobertura suficiente, por ejemplo API-Football o Sportmonks.

## Comandos principales

Ejecutar pipeline diario:

```bash
python -m app.pipelines.daily_update_pipeline
```

Ejecutar reentrenamiento completo:

```bash
python -m app.pipelines.full_retrain_pipeline
```

Levantar API opcional:

```bash
uvicorn app.main:app --reload
```

Ejecutar tests:

```bash
pytest
```

Lint:

```bash
ruff check .
```

## Entrenamiento

El entrenamiento:

- construye features desde SQLite
- usa split temporal, no aleatorio
- evita leakage calculando estadisticas solo con historial previo
- usa `RandomForestClassifier` como baseline
- usa `XGBoost` si esta instalado y disponible

Metricas generadas:

- accuracy
- log loss
- f1 macro
- classification report

## Prediccion

La prediccion carga el ultimo modelo activo y construye features del partido futuro desde el historial disponible.

Request esperado en `POST /predict`:

```json
{
  "home_team": "Argentina",
  "away_team": "France",
  "match_date": "2026-06-12T20:00:00",
  "neutral_site": true,
  "venue": "Lusail Stadium",
  "country": "Qatar"
}
```

Respuesta ejemplo:

```json
{
  "home_team": "Argentina",
  "away_team": "France",
  "model_version": "20260612_150000",
  "probabilities": {
    "home_win": 0.41,
    "draw": 0.27,
    "away_win": 0.32
  },
  "predicted_result": "HOME_WIN",
  "confidence": 0.41,
  "main_factors": [
    "Argentina tiene mejor rating Elo",
    "Francia tiene bajas importantes",
    "Partido en sede neutral"
  ]
}
```

Las predicciones son probabilisticas. No deben usarse como garantia de apuestas.

## Versionado de modelos

Cada entrenamiento guarda:

- `models/versions/model_YYYYMMDD_HHMMSS.pkl`
- `models/latest/model.pkl`

Ademas registra la version activa en la tabla `model_versions`.

## Tests

La suite cubre:

- repositorios SQLite
- feature builder
- entrenamiento y guardado del modelo
- carga del ultimo modelo
- prediccion
- pipeline diario
- adapters HTTP simulados con `respx`
- idempotencia de la ingesta

## Limitaciones

- football-data.org no siempre expone el mismo nivel de detalle para todas las competiciones.
- Open-Meteo depende de que la sede tenga coordenadas conocidas.
- lesiones/alineaciones reales requieren un proveedor adicional.
- los factores explicativos son heuristicos; no equivalen a SHAP o interpretabilidad causal.
- el modelo no garantiza resultados deportivos ni retornos economicos.

## Proximas mejoras

- incorporar geocodificacion automatica de sedes faltantes
- agregar proveedores pagos de player status
- incorporar validacion temporal rolling window
- sumar calibracion de probabilidades
- enriquecer features por competicion, contexto y lineups reales
