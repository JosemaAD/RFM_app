import streamlit as st
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import numpy as np
import pyrebase
import requests
import urllib.parse
# from firebase_config import firebaseConfig  # Eliminado, ahora se usa st.secrets

firebaseConfig = st.secrets["firebaseConfig"]
firebase = pyrebase.initialize_app(firebaseConfig)
auth = firebase.auth()

st.set_page_config(page_title="Disruptivos - RFM", layout="wide")

MAILCHIMP_CLIENT_ID = "318515731707"
MAILCHIMP_CLIENT_SECRET = "a163ec7c2f489974127531b280fa648b4f15f21d4f3797d2c8"
MAILCHIMP_REDIRECT_URI = "https://rfmapp-88bqkopqyfker y4iuprbfs.streamlit.app/"  # Cambia esto por la URL real de tu app en Streamlit Cloud
MAILCHIMP_AUTH_URL = "https://login.mailchimp.com/oauth2/authorize"
MAILCHIMP_TOKEN_URL = "https://login.mailchimp.com/oauth2/token"
MAILCHIMP_METADATA_URL = "https://login.mailchimp.com/oauth2/metadata"

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
    uploaded_file = st.file_uploader("1. Elige un fichero CSV o Excel", type=["csv", "xlsx"], on_change=reset_analysis)
    if uploaded_file is not None:
        # Detectar tipo de archivo y leerlo
        try:
            if uploaded_file.name.endswith(".csv"):
                df = pd.read_csv(uploaded_file)
                st.success("Archivo CSV cargado correctamente.")
            elif uploaded_file.name.endswith(".xlsx"):
                df = pd.read_excel(uploaded_file)
                st.success("Archivo Excel cargado correctamente.")
            else:
                st.error("Formato de archivo no soportado. Sube un archivo .csv o .xlsx.")
                st.stop()
        except Exception as e:
            st.error(f"Error al leer el archivo: {e}")
            st.stop()

        # Validación previa de columnas necesarias
        required_cols = [
            "Correo electrónico",
            "Fecha de última compra",
            "Importe total",
            "Total de compras",
            "Suscrito a newsletter"
        ]
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            st.error(f"Faltan las siguientes columnas obligatorias en tu archivo: {', '.join(missing_cols)}")
            st.stop()

        # Validación de datos vacíos
        if df[required_cols].isnull().any().any():
            st.warning("Hay celdas vacías en las columnas obligatorias. Por favor, revisa tu archivo antes de continuar.")
            st.dataframe(df[df[required_cols].isnull().any(axis=1)])
            st.stop()

        # Validación de formato de fecha
        try:
            fechas = pd.to_datetime(df["Fecha de última compra"], dayfirst=True, errors="coerce")
            if fechas.isnull().any():
                st.warning("Algunas fechas no tienen el formato correcto (deben ser DD/MM/AAAA o similar). Revisa las filas resaltadas:")
                st.dataframe(df[fechas.isnull()])
                st.stop()
        except Exception as e:
            st.error(f"Error en el formato de la columna 'Fecha de última compra': {e}")
            st.stop()

        st.success("Archivo validado correctamente. Ahora puedes mapear las columnas y lanzar el análisis.")

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
                        # Recomendaciones automáticas
                        recomendaciones = []
                        if data['Recency'] > 365:
                            recomendaciones.append("Campaña de reactivación: muchos clientes llevan más de un año sin comprar. Usa emails personalizados y ofertas atractivas.")
                        if data['Frequency'] < 2:
                            recomendaciones.append("Campaña de cross-selling o up-selling: intenta aumentar la frecuencia de compra con productos complementarios o packs.")
                        if data['Monetary'] < 50:
                            recomendaciones.append("Campaña de ticket medio: incentiva el aumento del gasto con descuentos por compras superiores a cierto importe.")
                        if not recomendaciones:
                            recomendaciones.append("Fideliza a este segmento con contenido exclusivo y programas VIP.")
                        st.info("\n".join(recomendaciones))

                # Simulador de campañas
                st.subheader("Simulador de impacto de campaña por segmento")
                sim_segmento = st.selectbox("Selecciona un segmento para simular la campaña", segment_names_list)
                sim_tipo = st.selectbox("Tipo de campaña", ["Descuento directo", "Email personalizado", "Cross-selling", "Última oportunidad"])
                sim_conversion = st.slider("% estimado de conversión o reactivación", min_value=1, max_value=100, value=10)
                sim_data = cluster_analysis.reset_index().iloc[segment_names_list.index(sim_segmento)]
                n_clientes = int(sim_data['Count'])
                clientes_impactados = int(n_clientes * sim_conversion / 100)
                gasto_medio = sim_data['Monetary']
                ingreso_estimado = clientes_impactados * gasto_medio
                st.markdown(f"**Impacto estimado:** Si lanzas una campaña de tipo *{sim_tipo}* al segmento *{sim_segmento}* y logras un {sim_conversion}% de conversión, impactarás a **{clientes_impactados} clientes** y podrías generar aproximadamente **{ingreso_estimado:,.2f} €** en ingresos.")

                # Exportar segmento a Mailchimp
                mailchimp_export_segment(rfm_data, segment_names_list)

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

# --- OAuth Mailchimp ---
def mailchimp_oauth_flow():
    st.subheader("Integración con Mailchimp")
    # Paso 1: Botón para iniciar OAuth
    if "mailchimp_token" not in st.session_state:
        params = {
            "response_type": "code",
            "client_id": MAILCHIMP_CLIENT_ID,
            "redirect_uri": MAILCHIMP_REDIRECT_URI,
        }
        auth_url = f"{MAILCHIMP_AUTH_URL}?{urllib.parse.urlencode(params)}"
        st.markdown(f"[🔗 Conectar con Mailchimp]({auth_url})", unsafe_allow_html=True)
        # Paso 2: Detectar si hay ?code= en la URL
        query_params = st.experimental_get_query_params()
        if "code" in query_params:
            code = query_params["code"][0]
            # Paso 3: Intercambiar code por access token
            data = {
                "grant_type": "authorization_code",
                "client_id": MAILCHIMP_CLIENT_ID,
                "client_secret": MAILCHIMP_CLIENT_SECRET,
                "redirect_uri": MAILCHIMP_REDIRECT_URI,
                "code": code,
            }
            try:
                resp = requests.post(MAILCHIMP_TOKEN_URL, data=data)
                resp.raise_for_status()
                token = resp.json()["access_token"]
                st.session_state["mailchimp_token"] = token
                st.success("¡Conexión con Mailchimp realizada con éxito!")
                # Limpiar el parámetro code de la URL
                st.query_params.clear()
            except Exception as e:
                st.error(f"Error al obtener el token de Mailchimp: {e}")
    else:
        st.success("Cuenta de Mailchimp conectada correctamente.")
        if st.button("Desconectar Mailchimp"):
            del st.session_state["mailchimp_token"]
            st.experimental_rerun()

def mailchimp_export_segment(rfm_data, segment_names_list):
    st.subheader("Exportar segmento a Mailchimp")
    token = st.session_state.get("mailchimp_token")
    if not token:
        st.info("Conecta primero tu cuenta de Mailchimp para exportar segmentos.")
        return
    # 1. Obtener metadata para saber el data center
    try:
        meta_resp = requests.get(MAILCHIMP_METADATA_URL, headers={"Authorization": f"OAuth {token}"})
        meta_resp.raise_for_status()
        api_endpoint = meta_resp.json()["api_endpoint"]
    except Exception as e:
        st.error(f"No se pudo obtener el endpoint de Mailchimp: {e}")
        return
    # 2. Obtener listas (audiencias)
    try:
        lists_resp = requests.get(f"{api_endpoint}/3.0/lists", headers={"Authorization": f"OAuth {token}"})
        lists_resp.raise_for_status()
        lists = lists_resp.json()["lists"]
        if not lists:
            st.warning("No se encontraron listas en tu cuenta de Mailchimp. Crea una lista primero.")
            return
    except Exception as e:
        st.error(f"No se pudieron obtener las listas de Mailchimp: {e}")
        return
    list_options = {l["name"]: l["id"] for l in lists}
    # 3. Seleccionar segmento y lista
    segmento = st.selectbox("Selecciona el segmento a exportar", segment_names_list, key="mailchimp_segment")
    lista_nombre = st.selectbox("Selecciona la lista de Mailchimp (audiencia)", list(list_options.keys()), key="mailchimp_lista")
    lista_id = list_options[lista_nombre]
    st.info(f"Vas a importar el segmento '{segmento}' a la audiencia '{lista_nombre}' (ID: {lista_id}) de Mailchimp.")
    if st.button("Exportar emails a Mailchimp"):
        # Filtrar emails del segmento
        emails = rfm_data[rfm_data["Segmento"] == segmento].index.tolist()
        if not emails:
            st.warning("No hay emails en este segmento para exportar.")
            return
        # 4. Exportar emails a la lista
        errors = 0
        for email in emails:
            data = {"email_address": email, "status": "subscribed"}
            resp = requests.post(f"{api_endpoint}/3.0/lists/{lista_id}/members", headers={"Authorization": f"OAuth {token}"}, json=data)
            if resp.status_code not in (200, 204):
                errors += 1
        if errors == 0:
            st.success(f"Todos los emails del segmento '{segmento}' han sido exportados a la audiencia '{lista_nombre}' de Mailchimp.")
        else:
            st.warning(f"{errors} emails no pudieron ser exportados (puede que ya existan o haya errores de formato).")

# --- Lógica principal de la aplicación ---
if 'analysis_done' not in st.session_state:
    st.session_state.analysis_done = False
if 'results' not in st.session_state:
    st.session_state.results = None

# Mostrar integración Mailchimp siempre, antes del login
mailchimp_oauth_flow()

# Si el usuario está en medio del flujo OAuth (hay parámetro 'code' en la URL), no mostrar login
query_params = st.query_params
if "code" in query_params:
    st.warning("Estás completando la conexión con Mailchimp. Por favor, espera a que termine antes de iniciar sesión en la app.")
    st.stop()

if 'user' not in st.session_state:
    st.info("Para evitar errores, conecta primero tu cuenta de Mailchimp antes de iniciar sesión en la app.")
    menu = st.sidebar.selectbox('Acción', ['Login', 'Registro'])
    if menu == 'Login':
        login_form()
    else:
        register_form()
else:
    st.sidebar.write(f"Usuario: {st.session_state['user']['email']}")
    logout()
    main_app()