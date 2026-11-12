# Taller HandsOnLab1 – Julián Ruiz

Pipeline sencillo de datos en AWS: se lee un CSV desde S3, se convierte cada fila en un JSON con una función Lambda, se cataloga con un crawler de Glue y se consulta con SQL en Athena.

```
S3 (input: CSV) ──► Lambda (CSV → JSON) ──► S3 (output: JSON) ──► Glue Crawler (Data Catalog) ──► Athena (SQL)
```

## 1. Lambda: de CSV a JSON

La función `bld-tseed-workshop-julian-ruiz` lee `sample_users.csv` del bucket `bld-tseed-workshop-input-semillero-2026-q4-b` y escribe un archivo por usuario en `bld-tseed-workshop-output-semillero-2026-q4-b/julian_ruiz/`, usando el `user_id` como nombre.

Código: [`lambda/lambda_function.py`](lambda/lambda_function.py)

![Lambda](imagenes/02_lambda.png)

Cada JSON se escribe en una sola línea para que Athena pueda leerlo. Ejemplo ([`csv-json/10.json`](csv-json/10.json)):

```json
{"user_id": "10", "name": "Andrés Gómez", "country": "México", "city": "Santiago", "role": "Engineer", "department": "IT", "education": "PhD", "age": "39", "languages": "French", "salary": "98688", ...}
```

**Permisos:** se agregó al rol de la Lambda una política inline con `s3:GetObject` sobre el CSV de entrada y `s3:PutObject` sobre `julian_ruiz/*` en el bucket de salida.

**Resultado:** 100 archivos JSON en la carpeta `julian_ruiz/`.

![Salida en S3](imagenes/01_s3_salida.png)

## 2. Glue: catálogo de datos

Se creó la base de datos `bld-tseed-workshop-julianruiz` y un crawler *on demand* apuntando a `s3://bld-tseed-workshop-output-semillero-2026-q4-b/julian_ruiz/`. El crawler generó la tabla `julian_ruiz` (clasificación JSON) con las 17 columnas del CSV.

![Catálogo en Glue](imagenes/03_glue_catalogo.png)

## 3. Athena: consultas SQL

### Cómo se ejecutaron

1. En la consola de **Athena → Editor de consultas**, se configuró la ubicación de resultados en *Configuración de consultas* (Athena la exige antes de ejecutar).
2. En el panel **Datos** se dejó el origen `AwsDataCatalog`. Como la base seleccionada por defecto era otra (`competenciasmayo2025`), cada consulta usa el nombre completo de la tabla: `"AwsDataCatalog"."bld-tseed-workshop-julianruiz"."julian_ruiz"`.
3. Se escribió cada consulta en el editor y se ejecutó con **Ejecutar** (o `Ctrl + Enter`).
4. En **Resultados de la consulta** se descargó el resultado como CSV, que es el archivo enlazado en la tabla de abajo.

El crawler dejó todas las columnas como `string`, por eso `age` se convierte con `CAST` para comparar números, y `languages` se filtra con `LIKE` porque una persona puede tener varios idiomas en el mismo campo (por ejemplo, `"Spanish, English"`).

![Consulta en Athena](imagenes/04_athena_consulta.png)

### Consulta 1: vista general de la tabla

Sirve para comprobar que Athena lee bien los JSON y que las columnas salen correctas.

```sql
SELECT *
FROM "AwsDataCatalog"."bld-tseed-workshop-julianruiz"."julian_ruiz";
```

Resultado: 68 filas → [`consulta1_general.csv`](csv-json/Consulta1.csv)

### Consulta 2: personas de Berlín con educación Bachelor

```sql
SELECT *
FROM "AwsDataCatalog"."bld-tseed-workshop-julianruiz"."julian_ruiz"
WHERE city LIKE '%Berlin%'
  AND education LIKE '%Bachelor%';
```

Resultado: 0 filas → [`consulta2_berlin_bachelor.csv`](csv-json/Consulta2.csv). No hay usuarios en Berlín; las ciudades del dataset son Bogotá, Medellín, Lima, Santiago, Buenos Aires, Ciudad de México, Madrid y Barcelona.

### Consulta 3: personas que hablan inglés y tienen más de 35 años

```sql
SELECT *
FROM "AwsDataCatalog"."bld-tseed-workshop-julianruiz"."julian_ruiz"
WHERE CAST(age AS integer) > 35
  AND languages LIKE '%English%';
```

Resultado: 19 filas → [`consulta3_ingles_mayores_35.csv`](csv-json/Consulta3.csv)

## Problemas resueltos en el camino

- **`AccessDenied` en `GetObject`/`PutObject`:** la política del rol usaba nombres de bucket genéricos; se corrigió con los ARN exactos.
- **Clave sin `/`:** el prefijo `julian_ruiz` sin barra generaba `julian_ruiz1.json`, fuera del permiso; se corrigió a `julian_ruiz/`.
- **`HIVE_CURSOR_ERROR` en Athena:** los JSON con `indent=2` ocupaban varias líneas; se cambió a un JSON por línea.
- **`SCHEMA_NOT_FOUND`:** se usó el nombre completo `"AwsDataCatalog"."bld-tseed-workshop-julianruiz"."julian_ruiz"`.

## Estructura

```
├── README.md
├── lambda/
│   └── lambda_function.py
├── csv-json/          # JSON de ejemplo y CSV exportados desde Athena
│   ├── 10.json
│   ├── consulta1_general.csv
│   ├── consulta2_berlin_bachelor.csv
│   └── consulta3_ingles_mayores_35.csv
└── imagenes/          # Pantallazos de S3, Lambda, Glue y Athena
```
