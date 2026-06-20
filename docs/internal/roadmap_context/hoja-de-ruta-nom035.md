# Hoja de Ruta de Producto — Plataforma SOFIA-S
### Evolución de la plataforma para el cumplimiento de la NOM-035-STPS-2018

---

## 1. Contexto

Hoy la plataforma permite crear y administrar los cuestionarios de la NOM-035, invitar a los
colaboradores de cada empresa, recolectar sus respuestas y dar seguimiento al avance de llenado
desde un panel por empresa.

Esta hoja de ruta describe las **tres siguientes capacidades** que llevarán a la plataforma de
"recolectar respuestas" a **"diagnosticar, reportar y acompañar"** todo el proceso NOM-035:

1. **Sistema de Valoración de Respuestas** — convertir cada respuesta en un puntaje y un Nivel de
   Riesgo, conforme a la metodología oficial.
2. **Reportes y Tableros** — explotar esos puntajes en dos formatos: tableros interactivos dentro de
   la plataforma y un reporte estático descargable que la empresa archiva como evidencia oficial.
3. **Checklist del Proceso** — integrar a la plataforma la lista de verificación que hoy se lleva en
   hoja de cálculo, para acompañar al administrador desde el onboarding hasta la entrega final.

---

## 2. Resumen ejecutivo

| Iniciativa | Valor para el negocio | Esfuerzo (calendario) |
|---|---|---|
| 1. Sistema de Valoración | Diagnóstico automático y sin errores manuales; base de todo lo demás | ~2–2.5 semanas |
| 2. Reportes y Tableros | Entregable de cara al cliente; evidencia oficial; menos trabajo manual de armado | ~4–5 semanas |
| 3. Checklist del Proceso | Estandariza y profesionaliza el servicio; nada se queda sin hacer | ~2–3 semanas |

**Secuencia recomendada:** 1 → 2 → 3. La Iniciativa 1 es el cimiento (sin puntajes no hay reportes);
la Iniciativa 2 los consume; la Iniciativa 3 es independiente y puede adelantarse como victoria
temprana. **Cronograma total estimado: ~10–12 semanas** al ritmo actual de dirección (ver §6).

---

## 3. Iniciativa 1 — Sistema de Valoración de Respuestas

### Objetivo de negocio
Hoy una respuesta es solo un dato ("Casi siempre"). El objetivo es que **cada respuesta sume hacia un
puntaje** que se traduzca automáticamente en un **Nivel de Riesgo (NDR)**, replicando con exactitud
el mecanismo de calificación de la NOM-035 — sin intervención manual y sin posibilidad de error de
captura.

### Cómo funciona (lógica de negocio)
La calificación de la NOM-035 (Guías de Referencia II y III) se basa en cuatro reglas que el motor
reproducirá:

1. **Valor de cada respuesta.** Cada opción de la escala vale un número:

   | | Siempre | Casi siempre | Algunas veces | Casi nunca | Nunca |
   |---|---|---|---|---|---|
   | Ítems normales | 0 | 1 | 2 | 3 | 4 |
   | Ítems invertidos | 4 | 3 | 2 | 1 | 0 |

   Algunos ítems se califican "al revés" porque están redactados en positivo (p. ej. *"Mi jefe ayuda
   a solucionar los problemas"*). El motor sabrá, por configuración, qué ítems son invertidos.

2. **Agrupación.** Cada ítem pertenece a una **Dimensión**, que pertenece a un **Dominio**, que
   pertenece a una **Categoría** (Ambiente de trabajo, Factores propios de la actividad, Organización
   del tiempo de trabajo, Liderazgo y relaciones, Entorno organizacional).

3. **Sumas.** Se calcula la calificación del Dominio (Cdom), de la Categoría (Ccat) y la final del
   cuestionario (Cfinal) sumando los ítems correspondientes.

4. **Nivel de Riesgo (NDR).** Cada suma se compara contra tablas de umbrales para clasificarla en
   **Nulo, Bajo, Medio, Alto o Muy alto**. Ejemplo de la tabla final (Guía III):

   | | Nulo | Bajo | Medio | Alto | Muy alto |
   |---|---|---|---|---|---|
   | Cfinal | <50 | 50–75 | 75–99 | 99–140 | >140 |

   (Existen tablas equivalentes por Categoría y por Dominio, ya documentadas a partir del ejemplo de
   reporte.)

### Enfoque técnico (alto nivel)
Se construirá un **motor de valoración genérico y configurable**, no atado a la NOM-035: los valores
por respuesta, los ítems invertidos, la agrupación dimensión/dominio/categoría y las tablas de
umbrales se guardan como **configuración (datos)**, no como código. La **NOM-035 (Guías II y III)
será la primera configuración cargada**. Beneficio: a futuro se podrán valorar otros instrumentos
(clima laboral, encuestas propias validadas) sin reescribir el motor.

### Entregables
- Modelo de configuración de valoración (valores, ítems invertidos, agrupación, umbrales).
- Carga ("seed") de la configuración oficial NOM-035 Guía III (72 ítems) y Guía II (46 ítems).
- Servicio de cálculo que produce, por colaborador y agregado por empresa: puntaje y NDR por
  dimensión, dominio, categoría y final.
- Pruebas automatizadas que validan los puntajes contra casos conocidos.

### Estimación
**10–14 horas-humano → ~2–2.5 semanas** de calendario.

---

## 4. Iniciativa 2 — Reportes y Tableros

### Objetivo de negocio
Transformar los puntajes de la Iniciativa 1 en **resultados presentables**, en dos formatos
complementarios:

- **Tableros interactivos (en plataforma):** gráficas dinámicas para que la empresa y el proveedor
  exploren los resultados (participación, NDR por categoría/dominio/dimensión, comparativos).
- **Reporte estático descargable ("evidencia oficial"):** un documento (PDF) con formato fijo que la
  empresa **descarga y archiva** como constancia del trabajo realizado ante la autoridad.

> *Nota: el archivo `Ejemplo Reporte Resultados.pdf` es la base del reporte estático; su diseño y
> textos cambiarán, pero define la estructura y los contenidos obligatorios.*

### Lógica de negocio (contenido del reporte estático)
El reporte reproduce la estructura del ejemplo oficial:

1. **Portada** — empresa, lugar y fecha, proveedor.
2. **Datos del centro de trabajo** — razón social, domicilio, RFC, giro.
3. **Objetivo y método** — marco NOM-035 y la tabla Categoría → Dominio → Dimensión → Ítems.
4. **Guía de calificación** — tablas de valores y de umbrales (las de la Iniciativa 1).
5. **Selección de la población** — universo invitado, total registrado, % de participación, y
   tamaño mínimo de muestra (la plataforma ya calcula este mínimo representativo).
6. **Resultados globales** — tabla de NDR y puntaje por Categoría y por Dominio.
7. **Resumen por categoría** — para cada nivel de riesgo, la "Necesidad de acción según NOM-035".
8. **Resumen por dimensión** — desglose con calificación por pregunta.
9. **Conclusiones y recomendaciones** — hallazgos y acciones de intervención sugeridas (insumo del
   Plan Bianual de Prevención).
10. **Datos del responsable de la evaluación** y aviso de confidencialidad.

### Lógica de negocio (tableros interactivos)
- Tasa de participación vs. mínimo representativo.
- Distribución de NDR (cuántos colaboradores en Nulo/Bajo/Medio/Alto/Muy alto).
- NDR por Categoría, Dominio y Dimensión, con capacidad de profundizar (drill-down).
- Vista por empresa para el administrador; vista de su propia empresa para el cliente.

### Enfoque técnico (alto nivel)
- La app **`analytics`** concentra la agregación de datos (sumas, promedios, distribución de NDR a
  nivel empresa).
- La app **`reports`** renderiza ambos formatos: vistas + plantillas con gráficas para los tableros,
  y la generación del PDF estático archivable.

### Entregables
- **2A — Tableros interactivos:** vistas, plantillas y gráficas. *(~2 semanas)*
- **2B — Reporte estático descargable:** generación del PDF con la estructura oficial, descarga y
  archivado por empresa. *(~2.5 semanas)*

### Estimación
**24–30 horas-humano → ~4–5 semanas** de calendario.

---

## 5. Iniciativa 3 — Checklist del Proceso (Administrador)

### Objetivo de negocio
Hoy el administrador lleva en una **hoja de cálculo** la lista de verificación de todo el proceso con
cada empresa: desde el onboarding, pasando por la entrega de documentos y capacitaciones, hasta la
entrega final. Integrarla a la plataforma **estandariza el servicio**, evita que se omitan pasos y da
visibilidad del avance por cliente.

### Lógica de negocio
La checklist se organiza en **tres fases** (tal como hoy en la hoja de cálculo):

1. **Primeros pasos: Cliente–Proveedor** (intake) — junta de implementación, solicitud de
   prestaciones, política de prevención / código de ética / RIT, buzón de quejas, revisión del aviso
   de privacidad, base de datos de empleados, definición del servicio de apoyo (ATS).
2. **Siguientes pasos: Proveedor** (ejecución) — crear empresa en plataforma, cargar base de
   trabajadores, determinar el mínimo de muestra, campaña de comunicación, kick-off, carpeta de
   evidencias, aplicación y seguimiento del cuestionario, reporte de resultados, presentación a RH,
   plan bianual, entrega final.
3. **Siguientes pasos: Cliente** — publicación de resultados, referencia de casos positivos (ATS),
   reuniones de diseño del plan bianual.

Cada ítem conserva los campos de la hoja actual: **Concepto, Descripción, Notas, Responsable,
Estado** (Sin empezar / En progreso / Bloqueado / Completado), **archivo adjunto** (evidencia) y
**última actualización**.

### Enfoque técnico (alto nivel)
- Una **plantilla de checklist** estándar (las 3 fases y sus ítems) que se **instancia por empresa**,
  de modo que cada cliente tiene su propia copia con avance independiente.
- Vistas para el administrador: marcar estados, asignar responsable, adjuntar evidencias y notas.

### Entregables
- Modelos de plantilla e instancia de checklist por empresa, con estados, responsables, notas y
  adjuntos.
- Carga de la checklist NOM-035 estándar.
- Vistas de gestión para el administrador.
- Pruebas automatizadas.

### Estimación
**12–16 horas-humano → ~2–3 semanas** de calendario.

---

## 6. Secuencia, cronograma y método de estimación

**Dependencias:** la Iniciativa 2 depende de la 1 (sin puntajes no hay reportes). La Iniciativa 3 es
independiente y puede adelantarse.

**Cronograma sugerido (secuencial):**

| Semanas | Iniciativa |
|---|---|
| 1–2 | Iniciativa 1 (Sistema de Valoración) |
| 3–7 | Iniciativa 2 (Tableros + Reporte estático) |
| 8–10 | Iniciativa 3 (Checklist) |

**Total: ~10–12 semanas.**

**Cómo se calcularon los tiempos.** El desarrollo de código lo ejecuta un **sistema agéntico**, que
acelera notablemente la implementación. El factor limitante no es escribir código, sino el **tiempo
humano de dirección** (redactar instrucciones, planear y revisar), acotado a **6 horas por semana**.
Por eso cada estimación se expresa en horas-humano y en su duración de calendario resultante. Abrir
un segundo frente de trabajo (p. ej. avanzar la Iniciativa 3 en paralelo) acorta el total.

---

## 7. Supuestos y fuera de alcance (esta fase)
- Se replica el procedimiento oficial NOM-035 **sin modificar** preguntas, puntajes ni fórmulas.
- Fuera de alcance por ahora: generación automática del **Plan Bianual** completo, validación
  estadística de cuestionarios propios (alfa de Cronbach, etc.), e integraciones externas. Se anotan
  como posibles fases futuras habilitadas por el motor genérico de la Iniciativa 1.
