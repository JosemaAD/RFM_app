import streamlit as st
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import numpy as np
import pyrebase
# from firebase_config import firebaseConfig  # Eliminado, ahora se usa st.secrets

firebaseConfig = st.secrets["firebaseConfig"]
firebase = pyrebase.initialize_app(firebaseConfig)
auth = firebase.auth()

st.set_page_config(page_title="Disruptivos - RFM", layout="wide")

def perform_rfm_analysis(df):
    if df.empty:
        return None, None
    now = df['Fecha de última compra'].max() + pd.Timedelta(days=1)
    rfm = df.groupby('Correo electrónico').agg({
        'Fecha de última compra': lambda date: (now - date.max()).days,
        'Total de compras': 'sum',
        'Importe total': 'sum'
    })
    rfm.columns = ['Recency', 'Frequency', 'Monetary']
    rfm = rfm[(rfm['Frequency'] > 0) & (rfm['Monetary'] > 0)]
    if rfm.empty:
        return None, None
    scaler = StandardScaler()
    rfm_scaled = scaler.fit_transform(np.log1p(rfm))
    n_clusters = 5
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init='auto')
    rfm['Cluster'] = kmeans.fit_predict(rfm_scaled)
    cluster_analysis = rfm.groupby('Cluster').agg({
        'Recency': 'mean',
        'Frequency': 'mean',
        'Monetary': 'mean',
        'Cluster': 'size'
    }).rename(columns={'Cluster': 'Count'})
    cluster_analysis = cluster_analysis.sort_values(by=['Recency', 'Frequency', 'Monetary'], ascending=[True, False, False])
    return cluster_analysis, rfm

def generate_report_text(cluster_analysis):
    report_lines = ["# Informe de Análisis de Segmentación de Clientes RFM\n\n"]
    report_lines.append("## Resumen de los Segmentos\n")
    report_lines.append(cluster_analysis.to_markdown(index=False))
    report_lines.append("\n\n## Propuestas de Acción por Segmento\n")
    segment_names_list = ["Clientes Campeones", "Clientes Leales", "Potencialmente Leales", "Clientes en Riesgo", "Clientes Dormidos"]
    for i, (cluster_id, data) in enumerate(cluster_analysis.iterrows()):
        segment_name = segment_names_list[i] if i < len(segment_names_list) else f"Segmento {i+1}"
        report_lines.append(f"### {segment_name} ({int(data['Count'])} clientes)\n")
        report_lines.append(f"- **Características:** Recencia media de **{int(data['Recency'])} días**, Frecuencia media de **{data['Frequency']:.1f} compras**, Gasto medio de **{data['Monetary']:.2f} €**.\n")
        report_lines.append("\n")
    return "\n".join(report_lines)

def reset_analysis():
    st.session_state.analysis_done = False
    st.session_state.results = None

def main_app():
    st.title("Disruptivos - RFM")
    st.markdown("""
    ### Instrucciones para subir tu archivo CSV
    1. El archivo debe tener al menos las siguientes columnas:
       - **Correo electrónico**
       - **Fecha de última compra**
       - **Importe total**
       - **Total de compras**
       - **Suscrito a newsletter**
    2. Puedes descargar un ejemplo de archivo CSV aquí:
    """)
    with open("ejemplo_clientes.csv", "rb") as f:
        st.download_button(
            label="📥 Descargar ejemplo de CSV",
            data=f,
            file_name="ejemplo_clientes.csv",
            mime="text/csv"
        )
    st.markdown("""
    3. Si tus columnas tienen otros nombres, podrás mapearlas en la app.
    4. El formato de los datos debe ser similar a este:
    
    | Correo electrónico      | Fecha de última compra | Importe total | Total de compras | Suscrito a newsletter |
    |------------------------|-----------------------|---------------|------------------|-----------------------|
    | cliente1@email.com     | 12/03/2024            | 120,50        | 3                | Si                    |
    | cliente2@email.com     | 05/01/2023            | 45,00         | 1                | No                    |
    | cliente3@email.com     | 20/06/2024            | 300,00        | 7                | Si                    |
    """)
    uploaded_file = st.file_uploader("1. Elige un fichero CSV", type="csv", on_change=reset_analysis)
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            st.success("Fichero cargado. Por favor, mapea las columnas.")
            st.header("2. Mapeo de Columnas")
            st.write("Asigna las columnas de tu fichero a los campos requeridos por la aplicación.")
            file_columns = df.columns.tolist()
            col1, col2, col3 = st.columns(3)
            with col1:
                email_col = st.selectbox("Columna de Correo Electrónico", file_columns, index=0)
                date_col = st.selectbox("Columna de Fecha de Última Compra", file_columns, index=1)
            with col2:
                monetary_col = st.selectbox("Columna de Importe Total", file_columns, index=2)
                frequency_col = st.selectbox("Columna de Total de Compras", file_columns, index=3)
            with col3:
                newsletter_col = st.selectbox("Columna de 'Suscrito a Newsletter'", file_columns, index=4)
            if st.button("🚀 Realizar Análisis"):
                df_mapped = df[[email_col, date_col, monetary_col, frequency_col, newsletter_col]].copy()
                df_mapped.columns = ['Correo electrónico', 'Fecha de última compra', 'Importe total', 'Total de compras', 'Suscrito a newsletter']
                df_mapped = df_mapped[df_mapped['Suscrito a newsletter'] == 'Si'].copy()
                df_mapped['Fecha de última compra'] = pd.to_datetime(df_mapped['Fecha de última compra'], dayfirst=True, errors='coerce')
                df_mapped.dropna(subset=['Fecha de última compra'], inplace=True)
                for col in ['Importe total', 'Total de compras']:
                    if df_mapped[col].dtype == 'object':
                        df_mapped[col] = df_mapped[col].str.replace('.', '', regex=False).str.replace(',', '.', regex=False).astype(float)
                    else:
                        df_mapped[col] = df_mapped[col].astype(float)
                cluster_analysis, rfm_data = perform_rfm_analysis(df_mapped)
                st.session_state.results = (cluster_analysis, rfm_data)
                st.session_state.analysis_done = True
                st.rerun()
        except Exception as e:
            st.error(f"Ha ocurrido un error al procesar el fichero: {e}")
    if st.session_state.analysis_done:
        st.header("3. Resultados del Análisis")
        if st.session_state.results:
            cluster_analysis, rfm_data = st.session_state.results
            if cluster_analysis is None or rfm_data is None:
                st.warning("No se encontraron clientes suscritos a la newsletter con datos válidos para analizar con el mapeo proporcionado.")
            else:
                st.write("La siguiente tabla muestra los 5 segmentos de clientes identificados, ordenados del más al menos valioso según sus características de compra.")
                st.table(cluster_analysis.style.format({
                    'Recency': '{:.0f} días',
                    'Frequency': '{:.1f} compras',
                    'Monetary': '{:.2f} €',
                    'Count': '{:,.0f} clientes'
                }))
                # Gráfica de barras de segmentos
                segment_names_list = ["Clientes Campeones", "Clientes Leales", "Potencialmente Leales", "Clientes en Riesgo", "Clientes Dormidos"]
                chart_data = cluster_analysis.reset_index()
                chart_data['Segmento'] = chart_data.index.map(lambda i: segment_names_list[i] if i < len(segment_names_list) else f"Segmento {i+1}")
                st.bar_chart(chart_data, x="Segmento", y="Count")

                # Gráfica de pastel para distribución porcentual
                import plotly.express as px
                pie_fig = px.pie(chart_data, names="Segmento", values="Count", title="Distribución porcentual de los segmentos")
                st.plotly_chart(pie_fig, use_container_width=True)
                segment_names_list = ["Clientes Campeones", "Clientes Leales", "Potencialmente Leales", "Clientes en Riesgo", "Clientes Dormidos"]
                sorted_cluster_ids = cluster_analysis.index.tolist()
                cluster_id_to_name_map = {cluster_id: segment_names_list[i] for i, cluster_id in enumerate(sorted_cluster_ids)}
                rfm_data['Segmento'] = rfm_data['Cluster'].map(cluster_id_to_name_map)
                st.subheader("Descargas")
                col1, col2 = st.columns(2)
                with col1:
                    report_text = generate_report_text(cluster_analysis)
                    st.download_button(label="📥 Descargar Informe de Análisis", data=report_text, file_name="informe_segmentacion_rfm.md", mime="text/markdown")
                with col2:
                    csv_export = rfm_data.reset_index()[['Correo electrónico', 'Segmento']].to_csv(index=False).encode('utf-8')
                    st.download_button(label="📧 Descargar CSV con Correos por Segmento", data=csv_export, file_name="correos_por_segmento.csv", mime="text/csv")
                st.subheader("Propuestas de Acción por Segmento")
                for i, (cluster_id, data) in enumerate(cluster_analysis.iterrows()):
                    segment_name = segment_names_list[i] if i < len(segment_names_list) else f"Segmento {i+1}"
                    with st.expander(f"Acciones para: **{segment_name}** ({int(data['Count'])} clientes)"):
                        st.markdown(f"""
                        - **Características:** 
                            - Han comprado por última vez hace **{int(data['Recency'])} días** (media).
                            - Han realizado **{data['Frequency']:.1f} compras** (media).
                            - Han gastado un total de **{data['Monetary']:.2f} €** (media).
                        """)

def login_form():
    st.title('Login')
    email = st.text_input('Email')
    password = st.text_input('Contraseña', type='password')
    if st.button('Iniciar sesión'):
        try:
            user = auth.sign_in_with_email_and_password(email, password)
            st.session_state['user'] = user
            st.success('¡Login correcto!')
            st.rerun()
        except Exception as e:
            st.error('Usuario o contraseña incorrectos')

def register_form():
    st.title('Registro')
    name = st.text_input('Nombre')
    email = st.text_input('Email', key='reg_email')
    password = st.text_input('Contraseña', type='password', key='reg_pass')
    if st.button('Crear cuenta'):
        try:
            user = auth.create_user_with_email_and_password(email, password)
            # Guardar el nombre en el perfil de usuario
            auth.update_profile(user['idToken'], display_name=name)
            st.success('Usuario creado. Ahora puedes iniciar sesión.')
        except Exception as e:
            st.error('Error al crear usuario: ' + str(e))

def logout():
    if st.button('Cerrar sesión'):
        st.session_state.pop('user', None)
        st.rerun()

# --- Lógica principal de la aplicación ---
if 'analysis_done' not in st.session_state:
    st.session_state.analysis_done = False
if 'results' not in st.session_state:
    st.session_state.results = None

if 'user' not in st.session_state:
    menu = st.sidebar.selectbox('Acción', ['Login', 'Registro'])
    if menu == 'Login':
        login_form()
    else:
        register_form()
else:
    st.sidebar.write(f"Usuario: {st.session_state['user']['email']}")
    logout()
    main_app()