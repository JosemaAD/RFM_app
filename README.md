# Análisis de Segmentación de Clientes RFM

Este repositorio contiene un análisis de segmentación de clientes para el ecommerce, enfocado en los clientes suscritos a la newsletter.

## 1. Objetivo

El objetivo de este análisis es identificar distintos grupos de clientes con comportamientos de compra similares para poder dirigir acciones de marketing y CRM personalizadas y más efectivas.

## 2. Metodología

Se ha utilizado un modelo de **segmentación RFM** combinado con un algoritmo de clustering **K-Means**.

-   **RFM** es un método de segmentación basado en el comportamiento del cliente que agrupa a los usuarios en función de tres variables:
    -   **Recencia (R):** ¿Cuán recientemente ha comprado un cliente?
    -   **Frecuencia (F):** ¿Con qué frecuencia compra?
    -   **Monetario (M):** ¿Cuánto dinero gasta?
-   **K-Means** es un algoritmo de Machine Learning que agrupa los datos en un número predefinido de clusters (en este caso, 5) basándose en la similitud de sus características RFM.

## 3. Resumen de los Segmentos Identificados

A continuación se muestra una tabla resumen con los 5 segmentos de clientes identificados, ordenados del más al menos valioso.

| Nombre del Segmento     | Nº Clientes | Recencia Media | Frecuencia Media | Gasto Medio |
| ----------------------- | ----------- | -------------- | ---------------- | ----------- |
| **Clientes Leales**     | 2,069       | 92 días        | 17.5 compras     | 949.76 €    |
| **Clientes Campeones**  | 2,061       | 79 días        | 3.2 compras      | 143.46 €    |
| **Potencialmente Leales** | 3,004       | 912 días       | 8.3 compras      | 356.95 €    |
| **Clientes en Riesgo**  | 4,272       | 1375 días      | 2.5 compras      | 100.22 €    |
| **Clientes Dormidos**   | 3,452       | 1634 días      | 1.2 compras      | 21.56 €     |

---

## 4. Propuestas de Acción por Segmento

### 1. Clientes Leales
-   **Quiénes son:** Tu activo más valioso. Compran muy a menudo, han comprado hace relativamente poco y gastan mucho. Son el pilar de tu negocio.
-   **Acciones recomendadas:**
    -   **Up-selling y Cross-selling:** Ofrecer productos complementarios o versiones de mayor valor.
    -   **Contenido Exclusivo:** Nutrir la relación con contenido de alto valor (masterclasses, recetas avanzadas).
    -   **Fidelización:** Implementar un programa de puntos o un club de fidelización.

### 2. Clientes Campeones
-   **Quiénes son:** Clientes recientes y con un buen ticket medio. Son la cantera de tus futuros clientes leales.
-   **Acciones recomendadas:**
    -   **Programa VIP:** Ofrecer acceso anticipado a nuevos productos o ventas privadas.
    -   **Prueba Social:** Solicitar testimonios y reseñas de productos.
    -   **Programa de Referidos:** Animar a que traigan a sus amigos a cambio de una recompensa.

### 3. Potencialmente Leales
-   **Quiénes son:** Han comprado bastantes veces y gastado una suma considerable, pero hace mucho que no lo hacen (casi 2.5 años de media). Gran potencial de reactivación.
-   **Acciones recomendadas:**
    -   **Incentivo Directo:** Ofrecer un descuento atractivo para incentivar una nueva compra.
    -   **Encuestas:** Preguntar qué echan en falta o por qué no han vuelto.
    -   **Personalización:** Crear campañas de email basadas en su historial de compra.

### 4. Clientes en Riesgo
-   **Quiénes son:** Han comprado pocas veces y su última compra fue hace mucho tiempo (más de 3 años y medio). Están a punto de convertirse en clientes perdidos.
-   **Acciones recomendadas:**
    -   **Campaña de Reactivación:** Email con un asunto tipo "Te echamos de menos" y una oferta potente.
    -   **Recordatorio de Valor:** Recordarles la propuesta de valor de la marca.
    -   **Descuento Agresivo:** Utilizar un descuento importante para intentar recuperarlos.

### 5. Clientes Dormidos
-   **Quiénes son:** El grupo menos activo. Compraron una o dos veces hace muchísimo tiempo y gastaron muy poco. Es muy difícil recuperarlos.
-   **Acciones recomendadas:**
    -   **Campaña de "Última Oportunidad":** Una última comunicación con una oferta muy atractiva.
    -   **Limpieza de Lista:** Si no reaccionan, reducir drásticamente la frecuencia de envíos para proteger la reputación del dominio.

