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
Confirmar **cuáles ítems se califican al revés**.

- **Guía III (72 ítems, empresas grandes) 🟢 transcrita:** la lista proviene
  directamente de la tabla de valores del *Ejemplo Reporte Resultados* (los dos
  grupos de puntaje 0→4 y 4→0). Pendiente solo una revisión de confirmación.
- **Guía II (46 ítems, empresas pequeñas) 🟡 reconstruida:** las Guías de Referencia
  entregadas no traían esta tabla en forma utilizable, así que reconstruimos la lista
  a partir de la estructura estándar de la Guía II. **Requiere validación ítem por
  ítem.**

### 2.2 Tablas de umbrales (Niveles de Riesgo) 🟡
Confirmar los **rangos de puntaje** que definen cada Nivel de Riesgo, por **Dominio**,
por **Categoría** y **final**.

- **Guía III 🟢 transcrita:** usamos las tablas oficiales del ejemplo de reporte
  (final: <50 Nulo, 50–75 Bajo, 75–99 Medio, 99–140 Alto, >140 Muy alto; más las
  tablas por categoría y por dominio). Los conteos de ítems cuadran con cada tabla.
- **Guía II 🟡 provisional (placeholder):** como no contamos con sus tablas, los
  umbrales de la Guía II se **calcularon de forma proporcional** al máximo posible de
  cada grupo. **Son provisionales** y deben reemplazarse por las tablas oficiales.
- **Convención de frontera:** cuando un puntaje cae justo en el límite entre dos
  niveles, lo asignamos al nivel **más alto** (criterio nuestro, a confirmar).

### 2.3 Nivel de Riesgo por Dimensión — no se calcula 🟡
La metodología oficial de la NOM-035 **solo publica tablas de umbrales por Dominio,
por Categoría y final**; **no existe una tabla por Dimensión**.

- **Decisión actual:** la Dimensión se usa únicamente para **organizar** los ítems,
  pero **no se le asigna un Nivel de Riesgo**. El reporte de ejemplo tampoco clasifica
  a nivel de dimensión.
- **Lo que necesitamos:** confirmar que basta con Dominio/Categoría/Final, o indicar
  el criterio oficial si en el futuro se desea un nivel por dimensión.

### 2.4 Agrupación Categoría → Dominio → Ítem 🟡
Confirmar a qué **Dominio y Categoría** pertenece cada ítem.

- **Guía III 🟢 transcrita** del ejemplo de reporte (tabla Categoría/Dominio/Dimensión
  → ítems).
- **Guía II 🟡 reconstruida** de la estructura estándar; validar el mapa completo.

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
| 2026-06-21 | 2.1 / 2.2 / 2.4 | Guía III transcrita (autoritativa) del Ejemplo Reporte; ítems invertidos, agrupación y umbrales por dominio/categoría/final confirmados contra los conteos de ítems. |
| 2026-06-21 | 2.1 / 2.2 / 2.4 | Guía II reconstruida de la estructura estándar con umbrales proporcionales provisionales (las Guías entregadas no traían sus tablas). Pendiente validación. |
| 2026-06-21 | 2.3 | Se decide **no** calcular Nivel de Riesgo por Dimensión (la NOM-035 no define umbrales por dimensión). |
