import streamlit as st
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import numpy as np

st.title("Análisis de Segmentación de Clientes de El Amasadero")
st.write("Sube tu archivo CSV de clientes suscritos a la newsletter para analizar los segmentos.")

uploaded_file = st.file_uploader("Selecciona el archivo CSV", type=["csv"])

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)
    except Exception as e:
        st.error(f"Error al leer el archivo: {e}")
        st.stop()

    # 1. Limpieza y Preprocesamiento
    if 'Suscrito a newsletter' in df.columns:
        df = df[df['Suscrito a newsletter'] == 'Si'].copy()
    else:
        st.warning("No se encontró la columna 'Suscrito a newsletter'. Se analizarán todos los registros.")

    if 'Fecha de última compra' in df.columns:
        df['Fecha de última compra'] = pd.to_datetime(df['Fecha de última compra'], dayfirst=True, errors='coerce')
        df.dropna(subset=['Fecha de última compra'], inplace=True)
    else:
        st.error("El archivo debe contener la columna 'Fecha de última compra'.")
        st.stop()

    for col in ['Importe total', 'Total de compras']:
        if col in df.columns:
            if df[col].dtype == 'object':
                df[col] = df[col].str.replace('.', '', regex=False).str.replace(',', '.', regex=False).astype(float)
            else:
                df[col] = df[col].astype(float)
        else:
            st.error(f"El archivo debe contener la columna '{col}'.")
            st.stop()

    # 2. Cálculo de RFM
    now = df['Fecha de última compra'].max() + pd.Timedelta(days=1)
    rfm = df.groupby('Correo electrónico').agg({
        'Fecha de última compra': lambda date: (now - date.max()).days,
        'Total de compras': 'sum',
        'Importe total': 'sum'
    })
    rfm.columns = ['Recency', 'Frequency', 'Monetary']
    rfm = rfm[rfm['Frequency'] > 0]
    rfm = rfm[rfm['Monetary'] > 0]

    # 3. Segmentación con K-Means
    scaler = StandardScaler()
    rfm_scaled = scaler.fit_transform(np.log1p(rfm))
    n_clusters = 5
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    rfm['Cluster'] = kmeans.fit_predict(rfm_scaled)

    # 4. Análisis de los Segmentos
    cluster_analysis = rfm.groupby('Cluster').agg({
        'Recency': 'mean',
        'Frequency': 'mean',
        'Monetary': 'mean',
        'Cluster': 'size'
    }).rename(columns={'Cluster': 'Count'})
    cluster_analysis = cluster_analysis.sort_values(by=['Recency', 'Frequency', 'Monetary'], ascending=[True, False, False])

    st.subheader("Resumen de Segmentos Identificados")
    st.dataframe(cluster_analysis.style.format({
        'Recency': '{:.0f} días',
        'Frequency': '{:.1f} compras',
        'Monetary': '{:.2f} €',
        'Count': '{:.0f}'
    }))

    # Gráfica de barras de segmentos
    chart_data = cluster_analysis.reset_index()
    chart_data['Segmento'] = chart_data.index.map(lambda i: segment_names.get(i, f"Segmento {i+1}"))
    st.bar_chart(chart_data, x="Segmento", y="Count")

    segment_names = {
        0: "Clientes Campeones",
        1: "Clientes Leales",
        2: "Potencialmente Leales",
        3: "Clientes en Riesgo",
        4: "Clientes Dormidos"
    }

    st.subheader("Propuestas de Acción por Segmento")
    for i, (cluster_id, data) in enumerate(cluster_analysis.iterrows()):
        segment_name = segment_names.get(i, f"Segmento {i+1}")
        st.markdown(f"**{segment_name} (Cluster {cluster_id})**")
        st.write(f"- Características: Recencia baja ({data['Recency']:.0f} días), Frecuencia alta ({data['Frequency']:.1f} compras), Gasto alto ({data['Monetary']:.2f} €).")
        st.write(f"- Número de clientes: {int(data['Count'])}")
        if segment_name == "Clientes Campeones":
            st.write("  - Recompensar su lealtad con acceso anticipado a productos, descuentos exclusivos o un programa VIP.")
            st.write("  - Solicitar testimonios o reseñas de productos.")
            st.write("  - Fomentar la recomendación a través de un programa de referidos.")
        elif segment_name == "Clientes Leales":
            st.write("  - Ofrecer productos complementarios (cross-selling) o versiones premium (up-selling).")
            st.write("  - Mantener el engagement con contenido de valor sobre panadería y recetas.")
            st.write("  - Programas de puntos o fidelización para incentivar la recurrencia.")
        elif segment_name == "Potencialmente Leales":
            st.write("  - Ofrecer descuentos especiales o promociones para incentivar una nueva compra.")
            st.write("  - Realizar encuestas para conocer mejor sus intereses y necesidades.")
            st.write("  - Crear campañas de email marketing personalizadas basadas en sus compras anteriores.")
        elif segment_name == "Clientes en Riesgo":
            st.write("  - Campañas de reactivación con ofertas atractivas ('Te echamos de menos').")
            st.write("  - Enviar comunicaciones personalizadas para recordarles el valor de la marca.")
            st.write("  - Ofrecer un descuento significativo en su próxima compra para recuperarlos.")
        elif segment_name == "Clientes Dormidos":
            st.write("  - Realizar una campaña de 'última oportunidad' antes de moverlos a una lista de baja frecuencia de envío.")
            st.write("  - Intentar reactivarlos con una oferta muy potente o un regalo.")
            st.write("  - Si no responden, reducir la frecuencia de comunicación para no afectar la entregabilidad general.")
    st.info("Nota: Los nombres de los segmentos son interpretaciones basadas en los datos de RFM.")