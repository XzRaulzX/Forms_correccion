import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import googleapiclient.discovery
import datetime
import io
import requests

# --- CONFIGURACIÓN ---
FOLDER_ID = "1bN9bMKTFH_Gt7yqdjhmamhj87ZAn2991"
SCOPES = [
    "https://www.googleapis.com/auth/drive.readonly",
    "https://www.googleapis.com/auth/spreadsheets"
]

#! Opcion de produccion
# sa_info = st.secrets["google_service_account"]
# creds = Credentials.from_service_account_info(sa_info, scopes=SCOPES)


# Credenciales Desarrollo
creds = Credentials.from_service_account_file("credentials.json", scopes=SCOPES)
print(creds.valid)


TAIGA_API_URL = "https://api.taiga.io/api/v1"
TAIGA_PROJECT_ID = "1768152"

# TAIGA_TOKEN = st.secrets["taiga"]["token"]
# TAIGA_PROJECT_ID = st.secrets["taiga"]["project_id"]

TAIGA_USERNAME = "HyDr4"
TAIGA_PASSWORD = "Demian2003+-*"

# --- AUTENTICACIÓN TAIGA ---
def obtener_token_taiga(username=TAIGA_USERNAME, password=TAIGA_PASSWORD):
    """
    Autentica en Taiga y devuelve el token.
    Guarda el token en st.session_state['taiga_token'] para uso posterior.
    """
    if "taiga_token" in st.session_state:
        return st.session_state.taiga_token  # Ya tenemos token

    url = f"{TAIGA_API_URL}/auth"
    payload = {
        "type": "normal",
        "username": username,
        "password": password
    }
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
        token = data.get("auth_token")
        if token:
            st.session_state.taiga_token = token
            st.session_state.taiga_user_id = data.get("id")
            st.success("🔑 Autenticación Taiga exitosa")
            return token
        else:
            st.error("No se recibió token de Taiga")
            return None
    except requests.exceptions.RequestException as e:
        st.error(f"Error autenticando en Taiga: {e}")
        return None

# --- CREAR UNA CARD INDIVIDUAL EN TAIGA ---
def crear_card_taiga(title, body, project_id=TAIGA_PROJECT_ID):
    """
    Crea un user story (card) en Taiga usando el token almacenado.
    """
    token = obtener_token_taiga()
    if not token:
        st.error("No hay token de Taiga disponible")
        return None

    url = f"{TAIGA_API_URL}/userstories"
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "project": project_id,
        "subject": title,
        "description": body
    }
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error creando card en Taiga: {e}")
        return None

# --- SUBIR VARIAS CARDS A TAIGA ---
def subir_cards_taiga(cards):
    """
    Recibe un diccionario {usuario: {"title":..., "body":...}} y sube cada card a Taiga.
    Retorna un diccionario con el resultado por usuario.
    """
    resultados = {}
    for usuario, card in cards.items():
        try:
            resp = crear_card_taiga(card["title"], card["body"])  # CORREGIDO: usar crear_card_taiga
            if resp and "id" in resp:
                resultados[usuario] = {"success": True, "card_id": resp["id"]}
            else:
                resultados[usuario] = {"success": False, "error": "No se obtuvo ID de la card"}
        except Exception as e:
            resultados[usuario] = {"success": False, "error": str(e)}
    return resultados

# --- FUNCIONES AUXILIARES ---
def respuesta_valida(respuesta):
    """
    Determina si la respuesta es válida.
    """
    if respuesta is None:
        return False
    if isinstance(respuesta, float) and pd.isna(respuesta):
        return False
    texto = str(respuesta).strip()
    if texto == "" or texto == "(Vacío)":
        return False
    return True

@st.cache_data
def load_all_sheets():
    
    client = gspread.authorize(creds)
    drive_service = googleapiclient.discovery.build('drive', 'v3', credentials=creds)
    query = f"'{FOLDER_ID}' in parents and mimeType='application/vnd.google-apps.spreadsheet'"
    results = drive_service.files().list(q=query, fields="files(id, name)").execute()
    files = results.get('files', [])
    all_data = []
    hoy = datetime.datetime.now()
    
    for f in files:
        # Solo procesamos archivos que comiencen con "Respuestas"
        if not f['name'].startswith("Respuestas"):
            continue  # Saltamos archivos que no empiecen con "Respuestas"
        
        try:
            sheet = client.open_by_key(f['id'])
            ws = sheet.get_worksheet(0)
            values = ws.get_all_values()
            if not values:
                continue

            headers = values[0]
            seen = {}
            unique_headers = []
            for h in headers:
                if h in seen:
                    seen[h] += 1
                    unique_headers.append(f"{h} ({seen[h]})")
                else:
                    seen[h] = 0
                    unique_headers.append(h)

            rows = []
            for row in values[1:]:
                row_filled = row + ['(Vacío)'] * (len(unique_headers) - len(row))
                rows.append(row_filled)

            df = pd.DataFrame(rows, columns=unique_headers)
            if 'Timestamp' in df.columns:
                df['Timestamp'] = pd.to_datetime(df['Timestamp'], errors='coerce')
                df = df[df['Timestamp'] >= (hoy - datetime.timedelta(days=14))]

            df['__origen_sheet__'] = f['name']
            df['__fecha_sheet__'] = f['name'].replace('Respuestas - ', '')
            all_data.append(df)

        except Exception as e:
            st.warning(f"No se pudo leer {f['name']}: {e}")

    return pd.concat(all_data, ignore_index=True) if all_data else pd.DataFrame()

def guardar_correcciones(df_corr, sheet_name="Correcciones"):
    try:
        client = gspread.authorize(creds)
        try:
            corr_sheet = client.open(sheet_name).sheet1
        except gspread.SpreadsheetNotFound:
            corr_sheet = client.create(sheet_name).sheet1

        values = [df_corr.columns.tolist()] + df_corr.values.tolist()
        corr_sheet.clear()
        corr_sheet.update(values)
        st.success("Correcciones guardadas correctamente ✅")
    except Exception as e:
        st.error(f"No se pudo guardar correcciones: {e}")

# --- CARGAR DATOS ---
df = load_all_sheets()

st.title("📋 Corrección de Formularios - Varios Sheets")

if df.empty:
    st.warning("No hay datos disponibles.")
    st.stop()

# --- SELECCIÓN DE FECHA ---
fechas = df['__fecha_sheet__'].unique()
fecha_seleccionada = st.selectbox(
    "Selecciona fecha (última por defecto)", 
    sorted(fechas, reverse=True)
)
df_fecha = df[df['__fecha_sheet__'] == fecha_seleccionada]

# --- SELECCIÓN DE USUARIOS ---
usuarios_disponibles = df_fecha["Nombre de tu usuario de Discord"].drop_duplicates().tolist()
usuarios_seleccionados = st.multiselect(
    "Selecciona usuario(s) a revisar",
    options=usuarios_disponibles,
    default=usuarios_disponibles[:1]
)
df_usuarios = df_fecha[df_fecha["Nombre de tu usuario de Discord"].isin(usuarios_seleccionados)]

# --- PREGUNTAS ---
preguntas = [c for c in df_fecha.columns if c not in [
    "Timestamp","Email Address","Nombre de tu usuario de Discord",
    "Fecha de tu nacimiento","Dinos tu ID64 de Steam","__origen_sheet__","__fecha_sheet__"
]]

# --- SESSION STATE ---
if "correcciones" not in st.session_state:
    st.session_state.correcciones = {}

if "taiga_cards" not in st.session_state:
    st.session_state.taiga_cards = {}

# --- CORRECCIÓN Y TAIGA POR USUARIO SELECCIONADO ---
for usuario in usuarios_seleccionados:
    user_info = df_fecha[df_fecha["Nombre de tu usuario de Discord"] == usuario].iloc[0]
    st.subheader(f"Usuario: {usuario} (Sheet: {user_info['__origen_sheet__']})")

    # Inicializar card
    if usuario not in st.session_state.taiga_cards:
        # El cuerpo ahora toma la columna "Proceso de wl"
        body_texto = user_info.get("Proceso de wl", "")
        st.session_state.taiga_cards[usuario] = {
            "title": usuario,
            "body": f"Mail: {user_info.get('Email Address','N/A')}\n"
                    f"Edad: {user_info.get('Fecha de tu nacimiento','N/A')}\n"
                    f"ID64: {user_info.get('Dinos tu ID64 de Steam','N/A')}\n"
                    
        }

    # Inputs persistentes
    st.session_state.taiga_cards[usuario]["title"] = st.text_input(
        f"📌 Título de la card para {usuario}",
        value=st.session_state.taiga_cards[usuario]["title"],
        key=f"title_{usuario}"
    )

    st.session_state.taiga_cards[usuario]["body"] = st.text_area(
        f"📝 Cuerpo de la card para {usuario}",
        value=st.session_state.taiga_cards[usuario]["body"],
        height=150,
        key=f"body_{usuario}"
    )

    # Botón Subir tarjeta Taiga
    if st.button(f"📤 Subir tarjeta Taiga - {usuario}", key=f"taiga_{usuario}"):
        title = st.session_state.taiga_cards[usuario]["title"]
        body = st.session_state.taiga_cards[usuario]["body"]
        resultado = crear_card_taiga(title, body)
        if resultado and "id" in resultado:
            st.success(f"Card enviada a Taiga ✅\nID: {resultado['id']}\n**Title:** {title}\n**Body:**\n{body}")
        else:
            st.error("Contacta con el DEV: No se pudo crear la card en Taiga. Revisa el token y el ID del proyecto.")


    # Expander con preguntas y botones de corrección
    preguntas_usuario = [c for c in preguntas if respuesta_valida(user_info.get(c))]
    with st.expander("🔍 Ver preguntas del formulario"):
        for pregunta in preguntas_usuario:
            key = f"{usuario}_{pregunta}"
            estado = st.session_state.correcciones.get(key, "")

            colores = {
                "correcto": "rgba(212, 237, 218, 0.5)",
                "atencion": "rgba(255, 243, 205, 0.5)",
                "incorrecto": "rgba(248, 215, 218, 0.5)"
            }
            color = colores.get(estado, "rgba(255,255,255,0)")

            st.markdown(
                f"**Pregunta:** {pregunta}\n\n"
                f"<div style='background-color:{color};padding:10px;border-radius:5px;'>{user_info.get(pregunta)}</div>",
                unsafe_allow_html=True
            )

            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("✅ Correcto", key=f"{key}_ok"):
                    st.session_state.correcciones[key] = "correcto"
            with col2:
                if st.button("⚠️ Atención", key=f"{key}_mid"):
                    st.session_state.correcciones[key] = "atencion"
            with col3:
                if st.button("❌ Incorrecto", key=f"{key}_bad"):
                    st.session_state.correcciones[key] = "incorrecto"

    # Calcular score individual
    corr_usuario = {k:v for k,v in st.session_state.correcciones.items() if k.startswith(f"{usuario}_")}
    score = sum(1 if v=="correcto" else 0.5 if v=="atencion" else 0 for v in corr_usuario.values())
    score = score / len(corr_usuario) if corr_usuario else 0
    aprobado = score >= 0.7
    st.markdown(f"**Score:** {round(score*100,2)}%  |  {'Aprobado ✅' if aprobado else 'No aprobado ❌'}")

# --- BOTÓN EXPORTAR EXCEL ---
if st.button("📊 Exportar Excel con ID y Respuestas"):
    export_data = []
    for idx, row in df_usuarios.iterrows():
        u = row["Nombre de tu usuario de Discord"]
        data_row = {"Usuario": u, **{p: row.get(p) for p in preguntas}}
        export_data.append(data_row)

    df_export = pd.DataFrame(export_data)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df_export.to_excel(writer, index=False, sheet_name="Respuestas")
    excel_data = output.getvalue()

    st.download_button(
        label="📥 Descargar Excel",
        data=excel_data,
        file_name=f"respuestas_{fecha_seleccionada}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
