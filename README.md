# football-ml-predictor

Pipeline no interactivo para ingestión de datos de fútbol, persistencia en SQLite, entrenamiento/versionado de modelos y generación de predicciones reproducibles.

## Objetivo

Este proyecto construye un flujo batch de Machine Learning orientado a resultados:

- descarga o simula datos de partidos
- actualiza una base SQLite evitando duplicados
- genera features históricas sin data leakage
- reentrena un modelo clasificatorio
- versiona artefactos entrenados
- registra métricas y reportes
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
- `app/ingestion`: interfaces para clientes externos y mocks iniciales.
- `app/features`: construcción de dataset histórico y features para partidos futuros.
- `app/training`: entrenamiento temporal, evaluación y registro/versionado.
- `app/prediction`: carga del modelo activo y generación de probabilidades.
- `app/pipelines`: ejecución batch de actualización diaria o reentrenamiento total.
- `app/reports`: exportación de métricas en JSON.

## Instalación

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

## Configuración

Variables relevantes:

- `DATABASE_URL`: URL SQLite.
- `MODEL_DIR`: carpeta de modelos.
- `REPORTS_DIR`: carpeta de reportes.
- `TEST_SIZE`: proporción temporal para test.
- `MIN_TRAINING_ROWS`: mínimo de filas para entrenar.
- `ENABLE_MOCK_INGESTION`: habilita fuentes mock de arranque.

## Base de datos y Alembic

El proyecto usa SQLAlchemy ORM y deja la base lista mediante `init_db()`. También incluye dependencias para Alembic para que puedas evolucionar el esquema con migraciones formales; la primera versión prioriza rapidez operativa del pipeline.

## Carga de datos iniciales

La primera versión usa clientes mock con interfaces claras:

- `MockMatchDataClient`
- `MockPlayerStatusClient`
- `MockWeatherClient`

Estos clientes no inventan atributos fuera del dataset definido. Si una fuente no provee lesiones, clima o stats, el sistema guarda `NULL` o defaults controlados.

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
- evita leakage calculando estadísticas solo con historial previo
- usa `RandomForestClassifier` como baseline
- usa `XGBoost` si está instalado y disponible

Métricas generadas:

- accuracy
- log loss
- f1 macro
- classification report

## Predicción

La predicción carga el último modelo activo y construye features del partido futuro desde el historial disponible.

Ejemplo esperado:

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

Los factores explicativos son heurísticos y no equivalen a SHAP o interpretabilidad causal.

## Versionado de modelos

Cada entrenamiento guarda:

- `models/versions/model_YYYYMMDD_HHMMSS.pkl`
- `models/latest/model.pkl`

Además registra la versión activa en la tabla `model_versions`.

## Limitaciones

- La fuente de datos inicial es mock.
- Alembic todavía no incluye una secuencia completa de migraciones versionadas.
- La explicación de factores es heurística.
- No hay scraping real en esta primera versión.
- El modelo trabaja con un dataset pequeño de demostración.

## Próximas mejoras

- conectar APIs reales de fixtures, ratings y lesiones
- incorporar validación temporal rolling window
- agregar calibración de probabilidades
- sumar mejores features por competición y contexto
- incluir migraciones Alembic iniciales y seeds reproducibles
