# Valoración NOM-035 — Supuestos y puntos por validar

> 🟡 = por validar. Última actualización: 2026-10-12.

---

## 1. Bloques que no aplican a todos (jefes / atención a clientes) 🟡

Algunas personas **no responden ciertos bloques** (por ejemplo, quien no es jefe o
no atiende clientes no ve esas preguntas).

- **Supuesto actual:** sumamos solamente los ítems que la persona **sí** respondió,
  pero comparamos esa suma contra los **umbrales completos**. Esto puede
  **subestimar el riesgo** de quienes no respondieron todos los bloques.
- **Lo que necesitamos:** confirmar cómo trata la norma estos casos (¿umbrales
  ajustados?, ¿promedios?, ¿se excluye la dimensión?).

## 2. Grupos pequeños y límite conocido 🟡

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

## 3. Quiénes se cuentan 🟡

- **Supuesto actual:** las gráficas de **sexo** y **edad** y la tabla **por área**
  cuentan a **quienes respondieron la encuesta seleccionada**, no a toda la
  plantilla; la tabla por área muestra al lado cuántas personas están
  registradas en cada área. Los datos faltantes —y los cuestionarios de cuentas
  eliminadas— se agrupan como **"Sin dato"** (sexo y edad) o **"Sin área"**. La
  **edad se calcula a la fecha de consulta**, no a la fecha en que se respondió: la
  misma consulta puede dar otro reparto por edad un año después.
- **Lo que necesitamos:** confirmar que así debe leerse el perfil de quienes
  respondieron, y si la edad debería fijarse a la fecha de respuesta.

## 4. Reporte: grupos pequeños también para Administración 🟡

- **Supuesto actual:** el Reporte de resultados se calcula **siempre** con la
  regla de grupos pequeños del punto 2, también en la vista previa de
  Administración. Así existe una sola versión del reporte y quien lo redacta ve
  exactamente las cifras que recibirá la empresa. Solo afecta a lo que se
  muestra **por área** (participación, distribuciones y Guía I por área).
- **Lo que necesitamos:** confirmar si el reporte entregado debería mostrar
  **todos los grupos sin ocultar**, como creemos que corresponde. Si es así,
  falta decidir quién lo recibe y si el Ejecutivo principal seguiría viendo la
  versión con grupos ocultos.

## 5. Reporte: texto del Objetivo 🟡

- **Supuesto actual:** la sección **Objetivo** es un texto fijo, igual para todos
  los reportes, y por ahora es un texto provisional.
- **Lo que necesitamos:** el texto definitivo, y confirmar si basta con un texto
  fijo o si debe cambiar según el tamaño de la empresa y las guías aplicadas
  (Guía I con Guía II o con Guía III).

## 6. Reporte: cómo describir la calificación final 🟡

- **Supuesto actual:** el reporte resume la calificación final agrupando niveles:
  *"De los N colaboradores evaluados, el X % presentó niveles de riesgo Nulo o
  Bajo; el Y % restante, Medio, Alto o Muy alto."*
- **Lo que necesitamos:** confirmar si es preferible describir el porcentaje de
  **cada nivel por separado**, sin agruparlos (por ejemplo, *"48 % Nulo, 28 %
  Bajo, 14 % Medio, 8 % Alto y 2 % Muy alto"*).

## 7. Encuesta: instrucciones para quien responde 🟡

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

## 8. Qué abarca una empresa y su reporte 🟡

- **Supuesto actual:** cada empresa registrada en la plataforma tiene su propio
  código de empresa, sus colaboradores, su página de Resultados y **un solo
  Reporte de resultados**, que la cubre completa.
  - **Varias razones sociales:** cada razón social se registra como una
    **empresa distinta**. Dos razones sociales de un mismo grupo no comparten
    tablero ni reporte.
  - **Varias localidades:** una empresa puede registrar varias localidades y
    filtrar por localidad en la página de Resultados, pero el reporte es uno
    solo para toda la empresa. Si se necesita un reporte separado por localidad
    (por ejemplo, un centro de trabajo por planta), cada localidad se registra
    como una **empresa distinta**.
- **Lo que necesitamos:** confirmar que así debe ser en los dos sentidos:
  - si un grupo con varias razones sociales necesita verse también en conjunto;
  - si un solo reporte por empresa es aceptable para la norma cuando hay varias
    localidades, o si cada centro de trabajo debe tener su propio reporte.

## 9. Puesto al activar la cuenta 🟡

- **Supuesto actual:** al activar su cuenta, la persona puede escribir su
  **puesto**, pero el campo es **opcional**. El puesto solo aparece en la lista
  de colaboradores y en su página de detalle; no se usa en la valoración, en los
  filtros de Resultados ni en el Reporte.
- **Lo que necesitamos:** confirmar si el puesto sirve para algo. Si sirve, lo
  hacemos **obligatorio** al activar la cuenta. Si no sirve, **lo quitamos** del
  formulario para pedir un dato menos.
