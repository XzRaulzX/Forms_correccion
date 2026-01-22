import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import googleapiclient.discovery
import datetime
from google.oauth2.service_account import Credentials
from google.oauth2.service_account import Credentials
# --- CONFIGURACIÓN ---
FOLDER_ID = "1bN9bMKTFH_Gt7yqdjhmamhj87ZAn2991"  # ID de la carpeta de Google Drive
SCOPES = ["https://www.googleapis.com/auth/drive.readonly",
          "https://www.googleapis.com/auth/spreadsheets"]

creds_dict = {
  "type": "service_account",
  "project_id": "serene-utility-485116-s6",
  "private_key_id": "9e67b455097bf7659e90cc0d4c212f63aff5a812",
  "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQDQIP4qIn9lgpWL\ntI4Ysk2h9KDG03iVL40C33Y/nATpZQKQKuOgSI4Lsh6Q/DF0qvRfCsUns7XNwit5\nFikrpFrHm0mF4y3PYWNitC8unta+ylqWN3wIrQ8fD/pM9JTh9iFK+FkrWzO5MLZ0\nNbAtZaHELQbGY/CyHmnYaH4fiYKvzSQ4vwLLq1DgSSZWjXZrpHmfaNQonkN5VYp0\n7INT7UiZf4l2B0eB01mZaVmlZs+noWS+CAWBY3Xh0P9BY4Dz3/+5I9oeCGIsbdrC\nz6f5XE3Hm2zJQ+D7Wm1nrIDz7jy+Wa1881AjSuDIEPQWeBEPKARWkCTR216nNKo0\nX/jPxxA7AgMBAAECggEAXsDOhcc74a6AP+C9GnA+mL+i3LIVATJrS8YJcy8oK0ux\nzYnBJM0zYg6/DLnMGDXmWEiydn9CA0FlglR8/OHv9FT1tY82YWYQlbS7kEl/MdA1\nSpNLFDYZnsYq6ZMmHvNrt9J14h+83hBX2HNC2IAfFA19up9wSt8+x+fWl6wGg9sa\nRL37Ann6O7xn83LFGQUJRVxj4lDkr+ErOdvOTQp2l7qPF6Z3rHwrHNb5OgLAHd/R\nJNdl3YNxg/Lq8j7oaVpq7M7oYM6ZGcusAdMEN2CRQlJcLi3wP7U6UdGzcqrFLoRI\nRjCmiyPJuzdEKWBG4kVl2RlQmoj5WmlSQturGxXGSQKBgQDxGv6uMwtLGH+3qkgp\n5UAa4pGiK/9v4eK+OmCtwQdZ/Ymsm8dTcLn1MKxWEGCTBelPrVIZ0ireuDfBpfv5\nRSrTvRS+KrfeU3ZWFTRX2U767zG76nH+gCq9ZMywbCQOJaaw0AGonEsaMrMKdncp\nXLLzHAuIhbDZT3168IdzwzR5CQKBgQDc/HvvtR+9YlArETwtii3VHjx1sMhqCo04\nIblHAh6jAzzaBgrHnjaL6oY/Jkoz9eCj5qr1Mj2hi5r1I17BaVA4ZwC0tWewzuIG\n3kXVXLPKBhnQglezUcdovGj6XAm6PUY286locsKXmDPc05rRHkA65L/+9QAQL8yp\n1Z0V8XtkIwKBgQCDvBwrUfh5r4kY8RE80uWTyveHhEKs/t7E0WDBjxZVNRJkHTlr\nfcwdC9sdqxUZP8GapziUoyCJUF4mkGp8aC5eQpFy1iRgdXnSzwMqfLGKqeaiphZi\n1+SCVvD/9BY/JJNPSFefqMXgKpNoxBGXp+6eplQm4+Uc1zHYWlOoDKA/AQKBgQDJ\n542893mmaPriPn8DBKrXeya2SOzzpexdCsLjU9Z2DfE9KiQTOkSQFZjOfcdyLgYu\n+gPcvyh8Prc3njdm8zeuML3+XXf9nSf6Kn8Xb/l8bZKMZWqHlgJheTNY+1qP5IgQ\nkROJMMEGDLPl4RgkVEVPCc05vtNt9p5B1cAOWnHojQKBgGnkYRv1b35j3JB0UJ23\nhi49rfxbA//umbmznRldChGo60my8UzpRxfNXeNrKz1sUKqbcEp5rS1UlMUvwKje\nSn4WW3gSDRjExx8yB0IiuyhsC0DKQOGblF6SVa6zQX6ROB790pXnnE3H7PYY3Mlh\na9zTdWoHw4OpkbzAfPqfVKnk\n-----END PRIVATE KEY-----\n",
  "client_email": "listener-sheet@serene-utility-485116-s6.iam.gserviceaccount.com",
  "client_id": "106896905130582640780",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/listener-sheet%40serene-utility-485116-s6.iam.gserviceaccount.com",
  "universe_domain": "googleapis.com"
}

#Opcion de produccion 
creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)

#Opcion para desarrollo, descomentar una u otra linea
#creds = Credentials.from_service_account_file("credentials.json", scopes=SCOPES)
print(creds.valid)

def respuesta_valida(respuesta):
    if respuesta is None:
        return False
    if isinstance(respuesta, float) and pd.isna(respuesta):
        return False
    texto = str(respuesta).strip()
    if texto == "" or texto == "(Vacío)":
        return False
    return True

# --- CARGA DE TODOS LOS SHEETS ---
@st.cache_data
def load_all_sheets():
    creds = Credentials.from_service_account_file(
        "credentials.json",
        scopes=SCOPES
    )
    client = gspread.authorize(creds)
    drive_service = googleapiclient.discovery.build('drive', 'v3', credentials=creds)

    query = f"'{FOLDER_ID}' in parents and mimeType='application/vnd.google-apps.spreadsheet'"
    results = drive_service.files().list(q=query, fields="files(id, name)").execute()
    files = results.get('files', [])

    all_data = []
    hoy = datetime.datetime.now()

    for f in files:
        try:
            sheet = client.open_by_key(f['id'])
            ws = sheet.get_worksheet(0)
            values = ws.get_all_values()
            if not values:
                continue

            # Hacer headers únicos
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

            # Rellenar filas vacías
            rows = []
            for row in values[1:]:
                row_filled = row + ['(Vacío)'] * (len(unique_headers) - len(row))
                rows.append(row_filled)

            df = pd.DataFrame(rows, columns=unique_headers)

            # Convertir timestamp a datetime y filtrar últimos 14 días
            if 'Timestamp' in df.columns:
                df['Timestamp'] = pd.to_datetime(df['Timestamp'], errors='coerce')
                df = df[df['Timestamp'] >= (hoy - datetime.timedelta(days=14))]

            # Añadir metadatos
            df['__origen_sheet__'] = f['name']
            df['__fecha_sheet__'] = f['name'].replace('Respuestas - ', '')
            all_data.append(df)

        except Exception as e:
            st.warning(f"No se pudo leer {f['name']}: {e}")

    if all_data:
        return pd.concat(all_data, ignore_index=True)
    else:
        return pd.DataFrame()

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

# --- FUNCION PARA GUARDAR CORRECCIONES ---
def guardar_correcciones(df_corr, sheet_name="Correcciones"):
    try:
        creds = Credentials.from_service_account_file("credentials.json", scopes=SCOPES)
        client = gspread.authorize(creds)
        # Buscar si existe el sheet
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

# --- VISUALIZACIÓN Y CORRECCIÓN ---
preguntas = [c for c in df_fecha.columns if c not in [
    "Timestamp","Email Address","Nombre de tu usuario de Discord",
    "Fecha de tu nacimiento","Dinos tu ID64 de Steam","__origen_sheet__","__fecha_sheet__"
]]

correcciones_totales = {}  # {usuario: {pregunta: correccion}}
# --- INICIALIZAR CORRECCIONES EN SESSION_STATE ---
if "correcciones" not in st.session_state:
    st.session_state.correcciones = {}  # { "usuario_pregunta": "correcto" }

# --- VISUALIZACIÓN Y CORRECCIÓN ---
for idx, user in df_usuarios.iterrows():
    st.subheader(f"Usuario: {user['Nombre de tu usuario de Discord']} (Sheet: {user['__origen_sheet__']})")
    for pregunta in preguntas:

        respuesta = user.get(pregunta, "(Vacío)")

        # 🔥 FILTRO DEFINITIVO
        if not respuesta_valida(respuesta):
            continue

        with st.expander(f"❓ {pregunta}"):

            key = f"{user['Nombre de tu usuario de Discord']}_{pregunta}"
            estado = st.session_state.correcciones.get(key, "")

            colores = {
                "correcto": "rgba(212, 237, 218, 0.5)",
                "atencion": "rgba(255, 243, 205, 0.5)",
                "incorrecto": "rgba(248, 215, 218, 0.5)"
            }

            color = colores.get(estado, "rgba(255,255,255,0)")

            st.markdown(
                f"<div style='background-color:{color};padding:10px;border-radius:5px;'>{respuesta}</div>",
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


# --- EVALUACIÓN Y GUARDADO ---
if st.button("📊 Evaluar y Guardar Correcciones"):
    lista_corr = []
    for k, valor in st.session_state.correcciones.items():
        usuario, pregunta = k.split("_", 1)
        lista_corr.append({
            "Usuario": usuario,
            "Pregunta": pregunta,
            "Correccion": valor,
            "Fecha": fecha_seleccionada
        })

    df_corr_guardar = pd.DataFrame(lista_corr)
    guardar_correcciones(df_corr_guardar)

    # Mostrar resumen tipo formulario para copiar a Taiga
    st.subheader("📝 Resumen de Correcciones (para Taiga)")
    for usuario in df_usuarios["Nombre de tu usuario de Discord"].unique():
        user_info = df_usuarios[df_usuarios["Nombre de tu usuario de Discord"]==usuario].iloc[0]
        corr_usuario = df_corr_guardar[df_corr_guardar["Usuario"]==usuario]
        score = sum(
            1 if v=="correcto" else 0.5 if v=="atencion" else 0
            for v in corr_usuario["Correccion"]
        ) / len(corr_usuario)
        aprobado = score >= 0.7

        st.markdown(f"**Usuario:** {usuario}  |  **Score:** {round(score*100,2)}%  |  {'Aprobado ✅' if aprobado else 'No aprobado ❌'}")
        st.markdown(f"""

Mail: {user_info.get('Email Address','N/A')}  
Edad: {user_info.get('Fecha de tu nacimiento','N/A')}  
ID64: {user_info.get('Dinos tu ID64 de Steam','N/A')}  
---------------------
""")
        for _, row in corr_usuario.iterrows():
            st.markdown(f"- **{row['Pregunta']}** → {row['Correccion'].capitalize()}")

