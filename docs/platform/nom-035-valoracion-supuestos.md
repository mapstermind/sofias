# Valoración NOM-035 — Supuestos y puntos por validar

## Propósito

Este documento reúne, **en lenguaje no técnico**, los supuestos que aún debemos
**confirmar con la persona experta** en la norma.

Los datos de calificación ya confirmados —ítems invertidos, agrupación
Categoría/Dominio, tablas de umbrales por dominio/categoría/final y la regla de
canalización de la Guía I— se transcribieron de la fuente única de verdad
(`docs/internal/Guias de Referencia.md`) y se consideran resueltos;
su detalle vive en `docs/platform/nom-035-analytics.md`. La página de
**Resultados** de cada empresa se describe en
`docs/platform/nom-035-results-dashboard.md`. Aquí quedan únicamente los
**puntos abiertos**.

> 🟡 = por validar. Última actualización: 2026-09-21.

---

## 1. Bloques que no aplican a todos (jefes / atención a clientes) 🟡

Algunas personas **no responden ciertos bloques** (por ejemplo, quien no es jefe o
no atiende clientes no ve esas preguntas).

- **Supuesto actual:** sumamos solamente los ítems que la persona **sí** respondió,
  pero comparamos esa suma contra los **umbrales completos**. Esto puede
  **subestimar el riesgo** de quienes no respondieron todos los bloques.
- **Lo que necesitamos:** confirmar cómo trata la norma estos casos (¿umbrales
  ajustados?, ¿promedios?, ¿se excluye la dimensión?).

## 2. Caso de ejemplo para validar el cálculo 🟡

Para asegurarnos de que el cálculo es correcto necesitamos **al menos un caso
resuelto**: un cuestionario con sus respuestas y el Nivel de Riesgo final ya
calculado (como en el ejemplo de reporte oficial).

- **Estado actual:** las pruebas automáticas validan la consistencia interna del
  motor (casos construidos y las bandas de umbral documentadas), pero **no** contra
  un caso oficial resuelto de forma independiente.
- **Lo que necesitamos:** un ejemplo completo y su resultado esperado, para comprobar
  que la plataforma llega exactamente al mismo número y nivel.

## 3. Calificación general de la empresa y del área 🟡

La plataforma **no muestra un nivel de riesgo ni un texto de acción** por área ni
por empresa. La norma define los niveles de riesgo para **cada cuestionario**, y
un área o una empresa reúne personas en **distintos niveles**; la norma **no
indica** cómo resumirlas en un solo nivel.

- **Lo que mostramos en su lugar:** para la calificación final, cada categoría y
  cada dominio, la **distribución** de los cuestionarios en los cinco niveles
  (Nulo, Bajo, Medio, Alto, Muy alto) y la **estadística** de los puntajes:
  promedio, mediana, mínimo y máximo, dibujados sobre las bandas oficiales de
  cada nivel. Ninguno de esos valores lleva una etiqueta de nivel.
- **Lo que necesitamos:** saber si la norma o la práctica piden una calificación
  general de la empresa o del área y, si es así, **cómo se obtiene**: ¿se clasifica
  el promedio con la tabla oficial?, ¿la mediana?, ¿basta con que **una** persona
  esté en el nivel más alto?, ¿o depende de una **proporción** (p. ej. "≥30% en
  Alto/Muy alto")?

## 4. Grupos pequeños 🟡

En la página de Resultados se pueden filtrar los resultados por sexo, edad, área
y localidad. Un grupo filtrado muy pequeño permitiría reconocer a las personas
(por ejemplo, "las dos mujeres de Almacén").

- **Supuesto actual:** el **Ejecutivo principal** ve los resultados de un grupo
  filtrado solo si reúne **al menos 5 cuestionarios**; si no, la página muestra
  *"Grupo demasiado pequeño para mostrar resultados sin identificar a las
  personas (mínimo 5)"*. La misma regla se aplica a cada renglón de la tabla por
  área. **Administración** (el equipo que opera la plataforma) puede verlos sin
  límite. La **vista completa de la encuesta**, sin filtros, siempre se muestra,
  aunque tenga menos de 5 cuestionarios.
- **Lo que necesitamos:** confirmar el **umbral de 5** y la **excepción** para
  Administración y para la vista completa.

## 5. Complementos y límite conocido 🟡

Ocultar los grupos pequeños no basta: si un filtro deja fuera a muy pocas
personas, restar ese grupo de la vista completa revelaría a quienes quedaron
fuera.

- **Supuesto actual:** también se oculta un grupo que deja fuera **de 1 a 4
  personas** (por ejemplo, "todos menos Dirección" cuando Dirección tiene dos
  personas).
- **Límite conocido:** restar **dos vistas filtradas distintas** entre sí sigue
  siendo posible (por ejemplo, "Operaciones" menos "Operaciones, 25–29 años").
  Evitarlo por completo exigiría ocultar muchas combinaciones útiles; lo
  documentamos como límite conocido.
- **Lo que necesitamos:** confirmar que este límite es aceptable.

## 6. Quiénes se cuentan 🟡

- **Supuesto actual:** las gráficas de **sexo** y **edad** y la tabla **por área**
  cuentan a **quienes respondieron la encuesta seleccionada**, no a toda la
  plantilla; la tabla por área muestra al lado cuántas personas están
  registradas en cada área. Los datos faltantes —y los cuestionarios de cuentas
  eliminadas— se agrupan como **"Sin dato"** (sexo y edad) o **"Sin área"**. La
  **edad se calcula a la fecha de consulta**, no a la fecha en que se respondió: la
  misma consulta puede dar otro reparto por edad un año después.
- **Lo que necesitamos:** confirmar que así debe leerse el perfil de quienes
  respondieron, y si la edad debería fijarse a la fecha de respuesta.

## 7. Guía I: tres resultados 🟡

- **Supuesto actual:** cada cuestionario queda en uno de tres resultados: **sin
  acontecimiento** (la Sección I no se respondió "Sí"), **acontecimiento sin requerir
  valoración** (la Sección I se respondió "Sí", pero no se alcanzó ningún umbral
  de las Secciones II a IV) y **requiere valoración clínica**. La página muestra
  cuántas personas hay en cada uno, sin nombres. Guardamos si ocurrió el
  acontecimiento, además del resultado de canalización, porque sin ese dato no
  se distingue a quien no vivió un acontecimiento de quien lo vivió sin requerir
  valoración.
- **Lo que necesitamos:** confirmar que estos tres resultados son la lectura
  correcta de la Guía I para la empresa.
