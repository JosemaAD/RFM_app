import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import numpy as np

# Cargar los datos
try:
    df = pd.read_csv("Amasadero_audit_master - BBDD Final.csv")
except FileNotFoundError:
    print("Error: No se encontró el archivo 'Amasadero_audit_master - BBDD Final.csv'")
    exit()

# 1. Limpieza y Preprocesamiento
# Filtrar por suscritos a la newsletter
df = df[df['Suscrito a newsletter'] == 'Si'].copy()

# Convertir la columna 'Fecha de última compra' a datetime
# Usamos dayfirst=True para interpretar formatos como DD/MM/YYYY
df['Fecha de última compra'] = pd.to_datetime(df['Fecha de última compra'], dayfirst=True, errors='coerce')

# Eliminar filas donde la fecha de última compra no se pudo convertir
df.dropna(subset=['Fecha de última compra'], inplace=True)

# Limpiar y convertir columnas numéricas
for col in ['Importe total', 'Total de compras']:
    if df[col].dtype == 'object':
        df[col] = df[col].str.replace('.', '', regex=False).str.replace(',', '.', regex=False).astype(float)
    else:
        df[col] = df[col].astype(float)


# 2. Cálculo de RFM
# Tomamos una fecha de referencia para calcular la recencia (un día después de la última fecha registrada)
now = df['Fecha de última compra'].max() + pd.Timedelta(days=1)

# Calcular Recencia, Frecuencia y Gasto Monetario
rfm = df.groupby('Correo electrónico').agg({
    'Fecha de última compra': lambda date: (now - date.max()).days,
    'Total de compras': 'sum',
    'Importe total': 'sum'
})

# Renombrar columnas
rfm.columns = ['Recency', 'Frequency', 'Monetary']

# Nos aseguramos que no haya valores negativos o cero en Frequency y Monetary para la transformación logarítmica
rfm = rfm[rfm['Frequency'] > 0]
rfm = rfm[rfm['Monetary'] > 0]


# 3. Segmentación con K-Means
# Normalizar los datos
scaler = StandardScaler()
rfm_scaled = scaler.fit_transform(np.log1p(rfm)) # Usamos log1p para manejar la asimetría

# Encontrar el número óptimo de clusters (Método del Codo)
# Por simplicidad, usaremos un número fijo de clusters, por ejemplo 5
n_clusters = 5
kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
rfm['Cluster'] = kmeans.fit_predict(rfm_scaled)


# 4. Análisis de los Segmentos y Propuesta de Acciones
# Calcular la media de R, F, M para cada cluster
cluster_analysis = rfm.groupby('Cluster').agg({
    'Recency': 'mean',
    'Frequency': 'mean',
    'Monetary': 'mean',
    'Cluster': 'size'
}).rename(columns={'Cluster': 'Count'})

# Ordenar los clusters de mejor a peor (bajo R, alta F y M es mejor)
cluster_analysis = cluster_analysis.sort_values(by=['Recency', 'Frequency', 'Monetary'], ascending=[True, False, False])

print("Análisis de Segmentos de Clientes (Suscritos a Newsletter)")
print("==========================================================")
print(cluster_analysis)
print("\nPropuestas de Acciones por Segmento:")
print("--------------------------------------\n")

# Asignar nombres a los segmentos basados en sus características
segment_names = {
    0: "Clientes Campeones",
    1: "Clientes Leales",
    2: "Potencialmente Leales",
    3: "Clientes en Riesgo",
    4: "Clientes Dormidos"
}

# Iterar sobre los segmentos ordenados y proponer acciones
for i, (cluster_id, data) in enumerate(cluster_analysis.iterrows()):
    segment_name = segment_names.get(i, f"Segmento {i+1}")
    print(f"--- {segment_name} (Cluster {cluster_id}) ---")
    print(f"  - Características: Recencia baja ({data['Recency']:.0f} días), Frecuencia alta ({data['Frequency']:.1f} compras), Gasto alto ({data['Monetary']:.2f} €).")
    print(f"  - Número de clientes: {int(data['Count'])}")

    if segment_name == "Clientes Campeones":
        print("  - Propuestas de Acción:")
        print("    - Recompensar su lealtad con acceso anticipado a productos, descuentos exclusivos o un programa VIP.")
        print("    - Solicitar testimonios o reseñas de productos.")
        print("    - Fomentar la recomendación a través de un programa de referidos.\n")
    elif segment_name == "Clientes Leales":
        print("  - Propuestas de Acción:")
        print("    - Ofrecer productos complementarios (cross-selling) o versiones premium (up-selling).")
        print("    - Mantener el engagement con contenido de valor sobre panadería y recetas.")
        print("    - Programas de puntos o fidelización para incentivar la recurrencia.\n")
    elif segment_name == "Potencialmente Leales":
        print("  - Propuestas de Acción:")
        print("    - Ofrecer descuentos especiales o promociones para incentivar una nueva compra.")
        print("    - Realizar encuestas para conocer mejor sus intereses y necesidades.")
        print("    - Crear campañas de email marketing personalizadas basadas en sus compras anteriores.\n")
    elif segment_name == "Clientes en Riesgo":
        print("  - Propuestas de Acción:")
        print("    - Campañas de reactivación con ofertas atractivas ('Te echamos de menos').")
        print("    - Enviar comunicaciones personalizadas para recordarles el valor de la marca.")
        print("    - Ofrecer un descuento significativo en su próxima compra para recuperarlos.\n")
    elif segment_name == "Clientes Dormidos":
        print("  - Propuestas de Acción:")
        print("    - Realizar una campaña de 'última oportunidad' antes de moverlos a una lista de baja frecuencia de envío.")
        print("    - Intentar reactivarlos con una oferta muy potente o un regalo.")
        print("    - Si no responden, reducir la frecuencia de comunicación para no afectar la entregabilidad general.\n")

print("\nNota: Los nombres de los segmentos son interpretaciones basadas en los datos de RFM.")
