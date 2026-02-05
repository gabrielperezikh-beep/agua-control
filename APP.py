import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta
import time
import os
import extra_streamlit_components as stx # LIBRERÍA PARA COOKIES

# --- 1. CONFIGURACIÓN INICIAL ---
st.set_page_config(page_title="Agua Control", page_icon="💧", layout="wide")

# --- 2. CSS PERSONALIZADO ---
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    [data-testid="column"] { width: 50% !important; flex: 1 1 50% !important; min-width: 50px !important; padding: 0 4px !important; }
    
    [data-testid="stForm"] { background-color: white; border: 1px solid #e0e0e0; border-radius: 12px; padding: 10px !important; box-shadow: 0 2px 4px rgba(0,0,0,0.05); margin-bottom: 5px; }
    
    [data-testid="stForm"] div.stButton > button {
        background-color: #0078D7 !important; color: white !important; border: none !important; border-radius: 8px !important;
        font-weight: 800 !important; width: 100% !important; height: 40px !important; margin-top: 5px !important; box-shadow: 0 2px 0 #005a9e !important;
    }
    [data-testid="stForm"] div.stButton > button:active { background-color: #005a9e !important; transform: translateY(2px); box-shadow: none !important; }

    .product-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 2px; font-family: sans-serif; }
    .prod-name { font-weight: 700; font-size: 14px; color: #333; }
    .prod-price { font-weight: 800; font-size: 15px; color: #0078D7; }

    .block-container { max-width: 800px; margin: auto; padding-top: 1rem; }
    div[data-testid="stNumberInput"] input { font-size: 20px; font-weight: bold; text-align: center; }
    div[data-testid="stVerticalBlock"] > div { align-items: center; }
</style>
""", unsafe_allow_html=True)

# --- 3. SISTEMA DE LOGIN INTELIGENTE (CORREGIDO - SIN CACHÉ EN WIDGETS) ---

# ELIMINAMOS @st.cache_resource AQUÍ PORQUE DABA ERROR
def get_manager():
    return stx.CookieManager(key="agua_manager")

def check_password():
    cookie_manager = get_manager()
    
    # Intentamos leer la cookie
    try:
        cookies = cookie_manager.get_all()
        auth_token = cookies.get("agua_auth_token")
    except:
        auth_token = None

    # VALIDACIÓN DIRECTA
    if auth_token == st.secrets["passwords"]["main"]:
        st.session_state['password_correct'] = True
        return True
    
    # PANTALLA DE LOGIN
    if not st.session_state.get('password_correct', False):
        c1, c2, c3 = st.columns([1,1,1])
        if os.path.exists("logo.png"):
            with c2: st.image("logo.png", width=150)
            
        st.markdown("### 🔒 Iniciar Sesión")
        
        with st.form("login_form"):
            password = st.text_input("Contraseña", type="password")
            mantener = st.checkbox("Mantener sesión abierta (30 días)", value=True)
            
            if st.form_submit_button("Ingresar"):
                if password == st.secrets["passwords"]["main"]:
                    st.session_state['password_correct'] = True
                    
                    if mantener:
                        cookie_manager.set(
                            "agua_auth_token", 
                            password, 
                            expires_at=datetime.now() + timedelta(days=30)
                        )
                    
                    st.success("¡Bienvenido!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("⛔ Contraseña incorrecta")
        return False
    
    return True

if not check_password():
    st.stop()

# ========================================================
# 🚀 APLICACIÓN PRINCIPAL
# ========================================================

# --- 4. GESTIÓN DE ESTADO ---
if 'carrito' not in st.session_state: st.session_state.carrito = {}

def agregar_producto(nombre):
    st.session_state.carrito[nombre] = st.session_state.carrito.get(nombre, 0) + 1
    st.toast(f"✅ Agregado: {nombre}", icon="🛒")

def limpiar_carrito():
    st.session_state.carrito = {}

# --- 5. CONEXIÓN BLINDADA ---

@st.cache_resource
def obtener_conexion():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = dict(st.secrets["gcp_service_account"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    return client.open("Gestion_Ventas_Agua")

@st.cache_data(ttl=3600) 
def cargar_datos_maestros():
    try:
        libro = obtener_conexion()
        conf = libro.worksheet("Configuracion").get_all_records()
        cargas = libro.worksheet("Cargas").get_all_records()
        ventas = libro.sheet1.get_all_records()
        return conf, cargas, ventas
    except: return [], [], []

def procesar_precios(datos_conf):
    productos_dict = {}
    for fila in datos_conf:
        precio = float(str(fila['Precio_Actual']).replace(',', '.')) if fila['Precio_Actual'] else 0.0
        litros = float(str(fila['Litros']).replace(',', '.')) if fila['Litros'] else 0.0
        productos_dict[fila['Producto']] = {"precio": precio, "litros": litros}
    return productos_dict

def calcular_stock(datos_cargas, datos_ventas):
    ent = pd.DataFrame(datos_cargas)['Litros'].sum() if datos_cargas else 0
    sal = pd.DataFrame(datos_ventas)['Total_Litros'].sum() if datos_ventas else 0
    return ent - sal

# --- INICIALIZACIÓN ---
try:
    datos_conf, datos_cargas, datos_ventas = cargar_datos_maestros()
    productos_disponibles = procesar_precios(datos_conf)
    stock = calcular_stock(datos_cargas, datos_ventas)
    
    libro_actual = obtener_conexion()
    sheet_ventas = libro_actual.sheet1
    try: sheet_cargas = libro_actual.worksheet("Cargas")
    except: sheet_cargas = None
    
except Exception as e:
    st.error("⚠️ Conectando...")
    if st.button("Reintentar"): st.cache_data.clear(); st.rerun()
    st.stop()

# --- 6. BARRA LATERAL ---
with st.sidebar:
    if os.path.exists("logo.png"):
        st.image("logo.png", use_container_width=True)
    
    st.write("### Panel de Control")
    st.divider()
    
    if st.button("🔒 Cerrar Sesión"):
        cookie_manager = get_manager()
        cookie_manager.delete("agua_auth_token")
        st.session_state['password_correct'] = False
        st.rerun()
        
    st.caption("v3.2 - Stable")

# --- 7. INTERFAZ ---
color_st = "#D32F2F" if stock < 200 else "#0078D7"

st.markdown(f"""
<div style="display:flex; justify-content:space-between; align-items:center; padding:12px; background:white; border-radius:12px; margin-bottom:10px; border-bottom:3px solid #eee;">
    <h2 style="margin:0; color:#333; font-size:24px;">💧 Control</h2>
    <div style="text-align:right;">
        <div style="font-size:10px; color:#888; font-weight:bold;">TANQUE</div>
        <div style="font-size:22px; font-weight:900; color:{color_st};">{stock:,.0f} L</div>
    </div>
</div>
""", unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs(["🛒 VENDER", "📊 DIARIO", "🚛 CISTERNA", "📅 SEMANAL"])

# TAB 1: VENDER
with tab1:
    if not productos_disponibles:
        st.warning("⚠️ Sin productos.")
        if st.button("Recargar"): st.cache_data.clear(); st.rerun()
    else:
        nombres = list(productos_disponibles.keys())
        for i in range(0, len(nombres), 2):
            col1, col2 = st.columns(2)
            p1 = nombres[i]
            info1 = productos_disponibles[p1]
            n1 = p1.replace("Recarga", "").replace("Botellón", "Bot.").strip()
            pr1 = f"{info1['precio']:g}"
            with col1:
                with st.form(key=f"f_{p1}", clear_on_submit=True):
                    st.markdown(f"""<div class="product-row"><span class="prod-name">{n1}</span><span class="prod-price">Bs {pr1}</span></div>""", unsafe_allow_html=True)
                    if st.form_submit_button("AGREGAR +", use_container_width=True):
                        agregar_producto(p1); st.rerun()
            if i + 1 < len(nombres):
                p2 = nombres[i+1]
                info2 = productos_disponibles[p2]
                n2 = p2.replace("Recarga", "").replace("Botellón", "Bot.").strip()
                pr2 = f"{info2['precio']:g}"
                with col2:
                    with st.form(key=f"f_{p2}", clear_on_submit=True):
                        st.markdown(f"""<div class="product-row"><span class="prod-name">{n2}</span><span class="prod-price">Bs {pr2}</span></div>""", unsafe_allow_html=True)
                        if st.form_submit_button("AGREGAR +", use_container_width=True):
                            agregar_producto(p2); st.rerun()

    if st.session_state.carrito:
        st.divider()
        st.markdown("### 🛒 Pedido Actual")
        total_bs = 0; total_l = 0; items_str = []
        keys_carrito = list(st.session_state.carrito.keys())
        for p in keys_carrito:
            q = st.session_state.carrito[p]
            dat = productos_disponibles.get(p, {'precio':0, 'litros':0})
            sub = dat['precio'] * q
            total_bs += sub; total_l += dat['litros'] * q
            items_str.append(f"{q}x {p}")
            c1, c2, c3, c4 = st.columns([3, 1, 1.5, 0.5])
            c1.write(f"**{p.replace('Recarga','')}**")
            c2.write(f"x{q}")
            c3.write(f"**Bs {sub:g}**")
            if c4.button("🗑️", key=f"del_{p}"):
                del st.session_state.carrito[p]; st.rerun()

        st.markdown("---")
        with st.form("cobro_principal"):
            st.markdown(f"#### Total: :blue[Bs {total_bs:,.2f}]")
            c_m, c_v = st.columns(2)
            with c_m: metodo = st.selectbox("Método", ["Pago Móvil", "Efectivo Bs", "Divisas ($)", "Punto de Venta"])
            with c_v: monto = st.number_input("Monto Recibido", value=float(total_bs))
            ref = st.text_input("Ref (4 dígitos)", max_chars=4)
            if st.form_submit_button("✅ CONFIRMAR VENTA", use_container_width=True):
                if ("Móvil" in metodo or "Punto" in metodo) and len(ref)<4: st.error("Falta Referencia")
                else:
                    try:
                        fila = [datetime.now().strftime("%Y-%m-%d"), datetime.now().strftime("%H:%M:%S"), ", ".join(items_str), monto, "USD" if "$" in metodo or "Divisa" in metodo else "VES", metodo, ref if ref else "N/A", total_l]
                        sheet_ventas.append_row(fila)
                        st.cache_data.clear()
                        st.success("¡Venta Registrada!")
                        limpiar_carrito(); time.sleep(1); st.rerun()
                    except: st.error("Error conexión.")

# TAB 2: DIARIO
with tab2:
    if st.button("🔄 Actualizar Datos"): st.cache_data.clear(); st.rerun()
    fecha = st.date_input("Fecha", datetime.now())
    df = pd.DataFrame(datos_ventas)
    if not df.empty:
        df['Fecha'] = pd.to_datetime(df['Fecha']).dt.date
        dia = df[df['Fecha'] == fecha]
        if not dia.empty:
            cstr = dia['Metodo_Pago'].astype(str)
            def suma(x): return dia[cstr.str.contains(x, case=False)]['Monto'].sum()
            k1, k2 = st.columns(2)
            k1.metric("Pago Móvil", f"Bs {suma('Móvil|Movil'):,.0f}")
            k2.metric("Efectivo", f"Bs {suma('Bs|Bolívares'):,.0f}")
            k3, k4 = st.columns(2)
            k3.metric("Divisas $", f"$ {suma('Divisas|Dólares|USD'):,.0f}")
            k4.metric("Punto", f"Bs {suma('Punto|POS'):,.0f}")
            filtro = st.radio("Filtro:", ["Todo", "Pago Móvil", "Efectivo", "Divisas"], horizontal=True)
            if filtro == "Todo": m = dia
            elif filtro == "Pago Móvil": m = dia[cstr.str.contains("Móvil|Movil", case=False)]
            elif filtro == "Efectivo": m = dia[cstr.str.contains("Bs|Bolívares", case=False)]
            elif filtro == "Divisas": m = dia[cstr.str.contains("Divisas|Dólares|USD", case=False)]
            else: m = pd.DataFrame()
            st.dataframe(m[['Hora','Detalles_Compra','Monto','Metodo_Pago', 'Referencia']], hide_index=True, use_container_width=True)
        else: st.info("Sin ventas.")

# TAB 3: CISTERNA
with tab3:
    st.markdown("### 🚛 Registro de Cisterna")
    with st.form("cisterna"):
        c1, c2 = st.columns(2)
        f = c1.date_input("Día", datetime.now())
        h = c2.time_input("Hora", datetime.now())
        l = st.number_input("Litros", 2000, step=100)
        n = st.text_input("Notas / Chofer")
        if st.form_submit_button("GUARDAR ENTRADA", use_container_width=True):
            if sheet_cargas:
                try:
                    sheet_cargas.append_row([str(f), str(h), l, 0, n])
                    st.cache_data.clear()
                    st.success("¡Stock Actualizado!"); time.sleep(1); st.rerun()
                except Exception as e: st.error(f"Error técnico: {e}")

# TAB 4: SEMANAL
with tab4:
    st.markdown("### 📅 Resumen Semanal")
    fecha_ref = st.date_input("Día Referencia:", datetime.now())
    inicio = fecha_ref - timedelta(days=fecha_ref.weekday())
    fin = inicio + timedelta(days=6)
    st.info(f"Semana: **{inicio.strftime('%d/%m')}** al **{fin.strftime('%d/%m')}**")
    df_v = pd.DataFrame(datos_ventas)
    if not df_v.empty:
        df_v['Fecha'] = pd.to_datetime(df_v['Fecha']).dt.date
        mask = (df_v['Fecha'] >= inicio) & (df_v['Fecha'] <= fin)
        df_sem = df_v.loc[mask]
        if not df_sem.empty:
            st.divider()
            st.markdown("#### 💰 Ventas")
            cstr_s = df_sem['Metodo_Pago'].astype(str)
            def suma_s(x): return df_sem[cstr_s.str.contains(x, case=False)]['Monto'].sum()
            c1, c2 = st.columns(2)
            c1.metric("Pago Móvil", f"Bs {suma_s('Móvil|Movil'):,.0f}")
            c2.metric("Efectivo", f"Bs {suma_s('Bs|Bolívares'):,.0f}")
            c3, c4 = st.columns(2)
            c3.metric("Divisas $", f"$ {suma_s('Divisas|Dólares|USD'):,.0f}")
            c4.metric("Punto", f"Bs {suma_s('Punto|POS'):,.0f}")
            st.success(f"💧 Total Vendido: {df_sem['Total_Litros'].sum():,.0f} L")
        else: st.warning("Sin ventas.")
    st.divider()
    st.markdown("#### 🚛 Cisternas")
    if datos_cargas:
        df_c = pd.DataFrame(datos_cargas)
        if not df_c.empty:
            df_c['Fecha'] = pd.to_datetime(df_c['Fecha']).dt.date
            mask_c = (df_c['Fecha'] >= inicio) & (df_c['Fecha'] <= fin)
            df_c_sem = df_c.loc[mask_c]
            if not df_c_sem.empty:
                cols = ['Fecha', 'Hora', 'Litros']
                if 'Notas' in df_c_sem.columns: cols.append('Notas')
                elif 'Chofer' in df_c_sem.columns: cols.append('Chofer')
                elif 'Nota' in df_c_sem.columns: cols.append('Nota')
                st.dataframe(df_c_sem[cols], hide_index=True, use_container_width=True)
                st.info(f"📥 Total Recibido: {df_c_sem['Litros'].sum():,.0f} L")
            else: st.caption("No hubo cargas.")