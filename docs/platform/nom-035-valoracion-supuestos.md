# Valoración NOM-035 — Supuestos y puntos a validar

## Propósito de este documento

Este documento reúne, **en lenguaje no técnico**, los supuestos que tomamos para
poner en marcha la valoración automática de la NOM-035 dentro de la plataforma, y
las **preguntas que necesitamos confirmar con la persona experta** en la norma.

La primera versión es un **MVP** ("producto que ya funciona, aún por afinar"): nos
permite ver resultados de punta a punta aunque algunos datos de calificación estén
basados en supuestos. Conforme se validen, los corregiremos y **actualizaremos este
documento**.

> Estado de cada punto: 🟡 por validar · 🟢 validado · 🔵 ajustado tras revisión.
> Última actualización: 2026-06-21.

---

## 1. Cómo se calcula hoy (resumen no técnico)

- Cada respuesta de la escala (Siempre, Casi siempre, Algunas veces, Casi nunca,
  Nunca) vale un número del 0 al 4.
- Algunos ítems están redactados "en positivo" y se califican **al revés**
  (invertidos).
- Los ítems se suman por **Dimensión**, las dimensiones por **Dominio**, los
  dominios por **Categoría**, y todo junto da una **calificación final**.
- Cada suma se compara con una **tabla de umbrales** para asignar un **Nivel de
  Riesgo**: Nulo, Bajo, Medio, Alto o Muy alto.
- La **Guía I** (acontecimientos traumáticos) **no** entra en ese puntaje: genera
  por separado una **señal de canalización** (posible necesidad de atención).

---

## 2. Puntos a validar

### 2.1 Lista de ítems invertidos 🟡
Necesitamos confirmar **cuáles ítems se califican al revés**, tanto para la
**Guía II** (46 ítems, empresas pequeñas) como para la **Guía III** (72 ítems,
empresas grandes).

- **Supuesto actual:** transcribimos la lista a partir de las Guías de Referencia;
  donde hubo duda, marcamos el ítem según nuestro mejor criterio.
- **Lo que necesitamos:** una confirmación ítem por ítem de cuáles son invertidos.

### 2.2 Tablas de umbrales (Niveles de Riesgo) 🟡
Necesitamos confirmar los **rangos de puntaje** que definen cada Nivel de Riesgo,
en cada nivel: por **Dimensión**, por **Dominio**, por **Categoría** y **final**.

- **Supuesto actual:** usamos la tabla final conocida (por ejemplo, final: menos de
  50 = Nulo; 50–75 = Bajo; 75–99 = Medio; 99–140 = Alto; más de 140 = Muy alto) y
  derivamos las demás del ejemplo de reporte. **La Guía II tiene sus propias tablas,
  distintas a las de la Guía III**, y esas son las que más necesitamos confirmar.
- **Lo que necesitamos:** las tablas oficiales completas para Guía II y Guía III.

### 2.3 Agrupación Categoría → Dominio → Dimensión → Ítem 🟡
Necesitamos confirmar a qué **Dimensión, Dominio y Categoría** pertenece cada ítem.

- **Supuesto actual:** transcribimos la agrupación de las Guías de Referencia.
- **Lo que necesitamos:** validar el mapa completo, sobre todo en los ítems que
  cambian entre Guía II y Guía III.

### 2.4 Bloques que no aplican a todos (jefes / atención a clientes) 🟡
Algunas personas **no responden ciertos bloques** (por ejemplo, quien no es jefe o
no atiende clientes no ve esas preguntas).

- **Supuesto actual:** sumamos solamente los ítems que la persona **sí** respondió,
  pero comparamos esa suma contra los **umbrales completos**. Esto puede **subestimar
  el riesgo** de quienes no respondieron todos los bloques.
- **Lo que necesitamos:** confirmar cómo trata la norma estos casos (¿umbrales
  ajustados?, ¿promedios?, ¿se excluye la dimensión?).

### 2.5 Señal de canalización de la Guía I 🟡
La Guía I genera una **señal**, no un puntaje.

- **Supuesto actual:**
  - Si la persona responde **"Sí"** a la pregunta inicial (vivió un acontecimiento),
    se levanta la señal.
  - Contamos cuántas preguntas de seguimiento respondió "Sí" y con eso asignamos una
    **severidad** (ninguna / baja / media / alta).
  - Los **cortes de severidad** los definimos nosotros como punto de partida.
- **Lo que necesitamos:** confirmar el criterio correcto para decidir cuándo una
  persona **requiere canalización** según la Guía I, y los cortes de severidad.

### 2.6 Caso de ejemplo para validar el cálculo 🟡
Para asegurarnos de que el cálculo es correcto, necesitamos **al menos un caso
resuelto** (un cuestionario con sus respuestas y el Nivel de Riesgo final ya
calculado, como en el ejemplo de reporte).

- **Lo que necesitamos:** un ejemplo completo y su resultado esperado, para
  comprobar que la plataforma llega exactamente al mismo número y nivel.

---

## 3. Qué NO incluye esta primera versión

- Gráficas o tableros visuales (solo texto por ahora).
- Reporte descargable / PDF oficial.
- Que cada colaborador vea su propio resultado (los resultados solo los ven los
  perfiles autorizados).

Estos puntos llegarán en fases posteriores y **no afectan** la validación de los
supuestos anteriores.

---

## 4. Bitácora de cambios

| Fecha | Punto | Cambio |
|---|---|---|
| 2026-06-21 | — | Versión inicial del documento (MVP). |
