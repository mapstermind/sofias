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
> Última actualización: 2026-07-05.
>
> **Fuente única de verdad:** `docs/internal/roadmap_context/Guias de Referencia.md`.
> Todos los datos de calificación (ítems invertidos, agrupación y umbrales) se
> transcriben de ahí; si otro documento la contradice, prevalece la fuente de verdad.

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
  por separado una **marca binaria** (positivo / no positivo) según el criterio
  oficial de la norma; una persona positiva requiere valoración clínica.

---

## 2. Puntos a validar

### 2.1 Lista de ítems invertidos 🟢
Confirmar **cuáles ítems se califican al revés**.

- **Guía III (72 ítems, empresas grandes) 🟢 transcrita** de la tabla de valores de
  las *Guías de Referencia* (los dos grupos de puntaje 0→4 y 4→0); reconcilia además
  con el *Ejemplo Reporte Resultados*.
- **Guía II (46 ítems, empresas pequeñas) 🟢 transcrita** de la tabla de valores de
  la Guía II en las *Guías de Referencia*: los ítems **18–33** se califican 0→4 y el
  resto 4→0. Sustituye la reconstrucción provisional anterior.

### 2.2 Tablas de umbrales (Niveles de Riesgo) 🟢
Confirmar los **rangos de puntaje** que definen cada Nivel de Riesgo, por **Dominio**,
por **Categoría** y **final**.

- **Guía III 🟢 transcrita** de las tablas oficiales (final: <50 Nulo, 50–75 Bajo,
  75–99 Medio, 99–140 Alto, ≥140 Muy alto; más las tablas por categoría y por
  dominio). Los conteos de ítems cuadran con cada tabla.
- **Guía II 🟢 transcrita** de las tablas oficiales de la Guía II (final: <20 Nulo,
  20–45 Bajo, 45–70 Medio, 70–90 Alto, ≥90 Muy alto; más categoría y dominio).
  Sustituye los umbrales proporcionales provisionales.
- **Convención de frontera 🟢 resuelta:** las tablas de la fuente de verdad ya no
  dejan huecos; cada banda inferior es "< X" y el nivel más alto es "≥", de modo que
  un puntaje justo en el límite cae en el nivel **más alto**. (La fuente corrigió el
  hueco de 7–8 del dominio Liderazgo de la Guía II y los bordes "> X".)

### 2.3 Nivel de Riesgo por Dimensión — no se calcula 🟢
La metodología oficial de la NOM-035 **solo publica tablas de umbrales por Dominio,
por Categoría y final**; **no existe una tabla por Dimensión** (confirmado en la
fuente de verdad).

- **Decisión:** la Dimensión se usa únicamente para **organizar** los ítems, pero
  **no se le asigna un Nivel de Riesgo**.
- **Pendiente menor:** indicar el criterio oficial solo si en el futuro se deseara un
  nivel por dimensión.

### 2.4 Agrupación Categoría → Dominio → Ítem 🟢
Confirmar a qué **Dominio y Categoría** pertenece cada ítem.

- **Guía III 🟢 transcrita** de la tabla Categoría/Dominio/Dimensión → ítems de las
  *Guías de Referencia*.
- **Guía II 🟢 transcrita** de esa misma tabla en la Guía II. Nota: la Guía II **no**
  incluye la categoría "Entorno organizacional" (son 4 categorías y 8 dominios).
  Sustituye la reconstrucción anterior.

### 2.4 Bloques que no aplican a todos (jefes / atención a clientes) 🟡
Algunas personas **no responden ciertos bloques** (por ejemplo, quien no es jefe o
no atiende clientes no ve esas preguntas).

- **Supuesto actual:** sumamos solamente los ítems que la persona **sí** respondió,
  pero comparamos esa suma contra los **umbrales completos**. Esto puede **subestimar
  el riesgo** de quienes no respondieron todos los bloques.
- **Lo que necesitamos:** confirmar cómo trata la norma estos casos (¿umbrales
  ajustados?, ¿promedios?, ¿se excluye la dimensión?).

### 2.5 Canalización de la Guía I 🟢
La Guía I genera una **marca binaria** (positivo / no positivo), no un puntaje ni una
gradación de severidad.

- **Criterio oficial (de las *Guías de Referencia*):** una persona resulta
  **positiva** —requiere valoración clínica— cuando respondió **"Sí"** a la pregunta
  inicial (Sección I, acontecimiento traumático severo) **y además** cumple al menos
  uno de:
  - alguna "Sí" en la **Sección II** (recuerdos persistentes),
  - **3 o más** "Sí" en la **Sección III** (evitación), o
  - **2 o más** "Sí" en la **Sección IV** (afectación).
- En la plataforma, a las personas positivas se les muestra el texto
  **«Usuario positivo a un acontecimiento traumático severo.»**
- Se **eliminó** la gradación de severidad inventada previamente (ninguna/baja/media/
  alta): la norma define un resultado binario.

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
| 2026-07-05 | — | Se adopta `docs/internal/roadmap_context/Guias de Referencia.md` como **fuente única de verdad** para toda la analítica NOM-035. |
| 2026-07-05 | 2.1 / 2.2 / 2.4 | **Guía II** reemplazada por los datos oficiales de la fuente de verdad (taxonomía, ítems invertidos y umbrales); se descartan la reconstrucción y los umbrales proporcionales provisionales. |
| 2026-07-05 | 2.2 / 2.3 | La fuente corrigió los huecos de umbrales (dominio Liderazgo Guía II 7–8; bordes "> X") y confirma que no hay tabla por dimensión. |
| 2026-07-05 | 2.5 | **Guía I** pasa a la regla oficial binaria por secciones (II/III/IV); se elimina la severidad. Texto para positivos: «Usuario positivo a un acontecimiento traumático severo.» |
