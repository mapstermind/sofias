# Valoración NOM-035 — Supuestos y puntos por validar

## Propósito

Este documento reúne, **en lenguaje no técnico**, los supuestos que aún debemos
**confirmar con la persona experta** en la norma.

Los datos de calificación ya confirmados —ítems invertidos, agrupación
Categoría/Dominio, tablas de umbrales por dominio/categoría/final y la regla de
canalización de la Guía I— se transcribieron de la fuente única de verdad
(`docs/internal/roadmap_context/Guias de Referencia.md`) y se consideran resueltos;
su detalle vive en `docs/platform/nom-035-analytics.md`. Aquí quedan únicamente los
**puntos abiertos**.

> 🟡 = por validar. Última actualización: 2026-07-09.

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
