# Valoración NOM-035 — Supuestos y puntos por validar

> 🟡 = por validar. Última actualización: 2026-10-17.

---

## 1. Grupos pequeños y límite conocido 🟡

En la página de Resultados se pueden filtrar los resultados por sexo, edad, área
y localidad. Un grupo filtrado muy pequeño permitiría reconocer a las personas
(por ejemplo, "las dos mujeres de Almacén"). Ocultar los grupos pequeños no
basta: si un filtro deja fuera a muy pocas personas, restar ese grupo de la
vista completa revelaría a quienes quedaron fuera.

- **Supuesto actual:** el **Ejecutivo principal** ve los resultados de un grupo
  filtrado solo si reúne **al menos 5 cuestionarios** y no deja fuera **de 1 a 4
  personas** (por ejemplo, "todos menos Dirección" cuando Dirección tiene dos
  personas). Si no se cumple, la página muestra *"Grupo muy pequeño: ocultamos
  sus resultados para no identificar a nadie (mínimo 5 personas)."* La misma regla
  se aplica a cada renglón de la tabla por área. **Administración** (el equipo
  que opera la plataforma) puede verlos sin límite. La **vista completa de la
  encuesta**, sin filtros, siempre se muestra, aunque tenga menos de 5
  cuestionarios.
- **Dentro de la misma página:** la calificación final del grupo se muestra con
  sus conteos exactos, así que restarle los renglones visibles de la tabla por
  área revelaría a las áreas ocultas (por ejemplo, dos áreas de 6 personas y
  Dirección con una sola). Por eso, cuando las áreas ocultas suman **de 1 a 4
  personas**, se ocultan también las áreas más pequeñas hasta que lo oculto
  sume al menos 5 personas. Las áreas ocultas siguen mostrando cuántas personas
  están registradas y cuántas respondieron, pero no su distribución.
- **Límite conocido:** restar **dos vistas distintas** entre sí sigue siendo
  posible, y **una de ellas puede ser la vista completa, sin filtros**. Por
  ejemplo, con dos áreas de 6 personas y Dirección con una sola, la vista
  completa oculta una de las áreas de 6 junto con Dirección; pero al filtrar por
  esa área se ve su distribución completa (6 personas, y quedan fuera 7), y
  entonces la vista completa menos esa área menos la otra revela el resultado de
  Dirección. Lo mismo ocurre entre dos vistas filtradas (por ejemplo,
  "Operaciones" menos "Operaciones, 25–29 años"). Evitarlo por completo exigiría
  ocultar muchas combinaciones útiles; hoy lo documentamos como límite conocido.
- **Lo que necesitamos:** confirmar el **umbral de 5** y la **excepción** para
  Administración y para la vista completa; y confirmar si el límite conocido es
  aceptable, o si preferimos que al filtrar por un área también se oculte cuando
  esa área quedó oculta en la vista completa (más protección, pero el Ejecutivo
  principal vería menos áreas).

## 2. Reporte: texto del Objetivo 🟡

- **Supuesto actual:** la sección **Objetivo** es un texto fijo, igual para todos
  los reportes, y por ahora es un texto provisional.
- **Lo que necesitamos:** el texto definitivo. Ya está decidido que el texto es
  fijo y no cambia según el tamaño de la empresa ni las guías aplicadas.

## 3. Encuesta: instrucciones para quien responde 🟡

- **Supuesto actual:** la primera vez que alguien abre la encuesta ve unas
  instrucciones redactadas a partir de los puntos que la propia norma pide
  explicar (Guía II/III, *cómo aplicarse*): pensar en los **dos últimos meses**,
  que **no hay respuestas correctas ni incorrectas**, contestar con sinceridad y
  todas las preguntas, y que los datos se manejan con **privacidad y
  confidencialidad** y solo para mejorar el ambiente de trabajo. El enlace al
  video apunta, por ahora, a la página principal de YouTube.
- **Confidencialidad:** el texto **no promete** que la empresa vea solo
  resultados de grupo, porque no es así: el **Ejecutivo principal** ve el nivel
  de riesgo de cada colaborador (y si requiere valoración clínica por la Guía I)
  en su página de detalle, y **Administración** ve además sus respuestas.
- **A quién acudir:** cuando a alguien le falta un código o no tiene acceso, la
  aplicación le dice que lo pida a **"quien te invitó"**.
- **Lo que necesitamos:** el texto definitivo de las instrucciones y el video;
  confirmar que la redacción sobre
  confidencialidad es aceptable, o si el Ejecutivo principal debería dejar de ver
  el nivel de riesgo individual; y si "quien te invitó" basta o
  conviene nombrar un área (por ejemplo, Recursos Humanos).

## 4. Reporte por localidad 🟡

- **Supuesto actual:** cada empresa registrada en la plataforma tiene **un solo
  Reporte de resultados**, que la cubre completa. Una empresa puede registrar
  varias localidades y filtrar por localidad en la página de Resultados, pero el
  reporte es uno solo para toda la empresa. Si se necesita un reporte separado
  por localidad (por ejemplo, un centro de trabajo por planta), cada localidad se
  registra como una **empresa distinta**. Cada razón social también se registra
  como una empresa distinta.
- **Lo que necesitamos:** confirmar si un solo reporte por empresa es aceptable
  para la norma cuando hay varias localidades, o si cada centro de trabajo debe
  tener su propio reporte.
