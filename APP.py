import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta
import time
import os
import extra_streamlit_components as stx

# --- 1. CONFIGURACIÓN E IDENTIDAD ---
st.set_page_config(page_title="Agua Control", page_icon="logo.png", layout="wide")

# ESTILOS CSS
st.markdown("""
<style>
    footer {visibility: hidden;}
    header {visibility: visible;}
    
    .block-container { 
        max-width: 800px; 
        margin: auto; 
        padding-top: 3.5rem !important; 
    }
    
    [data-testid="column"] { min-width: 10px !important; padding: 0 2px !important; }
    
    /* ESTILO PARA LOS FORMULARIOS PRINCIPALES (Vender, Login) */
    [data-testid="stForm"] { 
        background-color: white; 
        border: 1px solid #e0e0e0; 
        border-radius: 12px; 
        padding: 10px !important; 
        box-shadow: 0 2px 4px rgba(0,0,0,0.05); 
        margin-bottom: 8px;
    }
    
    /* BOTONES GIGANTES (Solo para Agregar y Confirmar) */
    /* Apuntamos específicamente a los botones dentro de formularios para que sean grandes */
    [data-testid="stForm"] button { 
        background-color: #0078D7 !important; 
        color: white !important; 
        border: none !important; 
        border-radius: 8px !important; 
        font-weight: 800 !important; 
        height: 45px !important; 
        margin-top: 2px !important;
    }
    [data-testid="stForm"] button:active { 
        background-color: #005a9e !important; 
        transform: scale(0.98); 
    }
    
    /* BOTÓN DE BORRAR (Pequeño y Rojo) */
    /* Este estilo aplicará al botón de basura que está FUERA de un form */
    div.stButton > button {
        border-radius: 8px !important;
        font-weight: bold !important;
        border: 1px solid #ff4b4b !important; /* Borde rojo suave */
        color: #ff4b4b !important;
        background-color: transparent !important;
        height: 40px !important;
    }
    div.stButton > button:active {
        background-color: #ff4b4b !important;
        color: white !important;
    }
    
    /* Textos */
    .prod-name { font-weight: 700; font-size: 15px; color: #333; margin-bottom: 0px;}
    .prod-details { font-size: 13px; color: #666; }
    .prod-price { font-weight: 800; font-size: 15px; color: #0078D7; }
    
    div[data-testid="stNumberInput"] input { font-size: 22px; font-weight: bold; text-align: center; }
</style>
""", unsafe_allow_html=True)

# --- 2. SISTEMA DE SEGURIDAD ---

def get_manager():
    return stx.CookieManager(key="agua_manager_secure")

def check_auth():
    if st.session_state.get('auth_status', False): return True

    cookie_manager = get_manager()
    
    params = st.query_params
    token_url = params.get("token", None)

    if token_url:
        try: tokens_validos = st.secrets["tokens"]
        except: st.error("⚠️ Falta configurar [tokens] en secrets.toml"); st.stop()

        if token_url in tokens_validos:
            st.session_state['auth_status'] = True
            cookie_manager.set("agua_token_secure", token_url, expires_at=datetime.now() + timedelta(days=90))
            st.query_params.clear() 
            st.rerun() 
            return True
        else: st.error("⛔ Enlace inválido."); st.stop()

    cookies = cookie_manager.get_all()
    token_cookie = cookies.get("agua_token_secure")
    
    if token_cookie:
        try:
            tokens_validos = st.secrets["tokens"]
            if token_cookie in tokens_validos or token_cookie == "admin_manual":
                st.session_state['auth_status'] = True
                return True
        except: pass

    c1, c2, c3 = st.columns([1,2,1])
    if os.path.exists("logo.png"): 
        with c2: st.image("logo.png", use_container_width=True)
    
    st.markdown("### 🔒 Acceso")
    with st.form("login_manual"):
        password = st.text_input("Clave Maestra", type="password")
        if st.form_submit_button("Entrar", use_container_width=True):
            if password == st.secrets["passwords"]["main"]:
                st.session_state['auth_status'] = True
                cookie_manager.set("agua_token_secure", "admin_manual", expires_at=datetime.now() + timedelta(days=1))
                st.rerun()
            else: st.error("Incorrecto")
    return False

if not check_auth(): st.stop()

# ========================================================
# 🚀 APLICACIÓN
# ========================================================

if 'carrito' not in st.session_state: st.session_state.carrito = {}

def agregar_producto(nombre):
    st.session_state.carrito[nombre] = st.session_state.carrito.get(nombre, 0) + 1
    st.toast(f"✅ {nombre}", icon="🛒")

def limpiar_carrito(): st.session_state.carrito = {}

@st.cache_resource
def obtener_conexion():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = dict(st.secrets["gcp_service_account"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    return client.open("Gestion_Ventas_Agua")

@st.cache_data(ttl=300)
def cargar_datos_maestros():
    try:
        libro = obtener_conexion()
        return libro.worksheet("Configuracion").get_all_records(), libro.worksheet("Cargas").get_all_records(), libro.sheet1.get_all_records()
    except: return [], [], []

def procesar_precios(datos_conf):
    p = {}
    for f in datos_conf:
        pr = float(str(f['Precio_Actual']).replace(',', '.')) if f['Precio_Actual'] else 0.0
        l = float(str(f['Litros']).replace(',', '.')) if f['Litros'] else 0.0
        p[f['Producto']] = {"precio": pr, "litros": l}
    return p

def calcular_stock(c, v):
    ent = pd.DataFrame(c)['Litros'].sum() if c else 0
    sal = pd.DataFrame(v)['Total_Litros'].sum() if v else 0
    return ent - sal

try:
    datos_conf, datos_cargas, datos_ventas = cargar_datos_maestros()
    productos_disponibles = procesar_precios(datos_conf)
    stock = calcular_stock(datos_cargas, datos_ventas)
    libro_actual = obtener_conexion()
    sheet_ventas = libro_actual.sheet1
    try: sheet_cargas = libro_actual.worksheet("Cargas")
    except: sheet_cargas = None
except:
    st.warning("⚠️ Reconectando..."); time.sleep(1); st.cache_data.clear(); st.rerun()

# --- HEADER ---
color_st = "#D32F2F" if stock < 200 else "#0078D7"
c_logo, c_title, c_logout = st.columns([1.5, 5, 1.5], vertical_alignment="center")

with c_logo:
    if os.path.exists("logo.png"): st.image("logo.png", use_container_width=True)
    else: st.write("💧")

with c_title: 
    st.markdown(f"<h3 style='margin:0; padding:0; text-align:center; color:#333; font-size:20px;'>Control</h3>", unsafe_allow_html=True)

with c_logout:
    if st.button("🔓", key="logout_btn", help="Salir", use_container_width=True):
        get_manager().delete("agua_token_secure")
        st.session_state['auth_status'] = False
        st.query_params.clear()
        st.rerun()

st.markdown(f"""
<div style="padding:15px; background:linear-gradient(90deg, #f8f9fa 0%, #e9ecef 100%); border-radius:12px; margin-bottom:15px; margin-top:10px; border-left:5px solid {color_st}; display:flex; justify-content:space-between; align-items:center;">
    <div style="font-size:12px; color:#555; font-weight:bold;">TANQUE<br>DISPONIBLE</div>
    <div style="font-size:28px; font-weight:900; color:{color_st};">{stock:,.0f} L</div>
</div>
""", unsafe_allow_html=True)

# --- PESTAÑAS ---
tab1, tab2, tab3, tab4 = st.tabs(["🛒 VENDER", "📊 DIARIO", "🚛 CISTERNA", "📅 SEMANAL"])

with tab1:
    if not productos_disponibles:
        st.warning("⚠️ Sin productos.")
        if st.button("Recargar"): st.cache_data.clear(); st.rerun()
    else:
        nombres = list(productos_disponibles.keys())
        for i in range(0, len(nombres), 2):
            col1, col2 = st.columns(2)
            p1 = nombres[i]; info1 = productos_disponibles[p1]
            with col1:
                with st.form(key=f"f_{p1}", clear_on_submit=True):
                    st.markdown(f"""<div style="line-height:1.2; margin-bottom:5px;"><div class="prod-name">{p1.replace("Recarga", "").replace("Botellón", "Bot.").strip()}</div><div class="prod-price">Bs {info1['precio']:g}</div></div>""", unsafe_allow_html=True)
                    if st.form_submit_button("AGREGAR", use_container_width=True): agregar_producto(p1)
            if i + 1 < len(nombres):
                p2 = nombres[i+1]; info2 = productos_disponibles[p2]
                with col2:
                    with st.form(key=f"f_{p2}", clear_on_submit=True):
                        st.markdown(f"""<div style="line-height:1.2; margin-bottom:5px;"><div class="prod-name">{p2.replace("Recarga", "").replace("Botellón", "Bot.").strip()}</div><div class="prod-price">Bs {info2['precio']:g}</div></div>""", unsafe_allow_html=True)
                        if st.form_submit_button("AGREGAR", use_container_width=True): agregar_producto(p2)

    if st.session_state.carrito:
        st.divider(); st.markdown("### 🛒 Pedido Actual")
        total_bs = 0; total_l = 0; items_str = []
        keys_carrito = list(st.session_state.carrito.keys())
        
        # --- CARRITO ESTILO TARJETA ---
        for p in keys_carrito:
            q = st.session_state.carrito[p]
            dat = productos_disponibles.get(p, {'precio':0, 'litros':0})
            sub = dat['precio'] * q
            total_bs += sub; total_l += dat['litros'] * q
            items_str.append(f"{q}x {p}")
            
            # Usamos container(border=True) para la caja blanca sin usar un FORM
            with st.container(border=True):
                # Columnas: Texto (Grande) | Botón (Pequeño)
                col_info, col_btn = st.columns([4, 1], vertical_alignment="center")
                
                with col_info:
                    st.markdown(f"<div class='prod-name'>{p.replace('Recarga','')}</div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='prod-details'>Cant: <b>{q}</b> &nbsp;|&nbsp; Total: <span class='prod-price'>Bs {sub:g}</span></div>", unsafe_allow_html=True)
                
                with col_btn:
                    # Botón normal (fuera de form) -> Hereda el estilo rojo definido en CSS
                    # No usamos use_container_width=True para que se mantenga pequeño y cuadrado
                    if st.button("🗑️", key=f"del_{p}", help="Eliminar"):
                        del st.session_state.carrito[p]
                        st.rerun()

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
                        st.success("¡Venta Exitosa!")
                        limpiar_carrito()
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        if "Rerun" not in str(e): st.error("Error conexión.")

with tab2:
    if st.button("🔄 Actualizar Tabla", use_container_width=True): st.cache_data.clear(); st.rerun()
    fecha = st.date_input("Fecha", datetime.now())
    df = pd.DataFrame(datos_ventas)
    if not df.empty:
        df['Fecha'] = pd.to_datetime(df['Fecha']).dt.date; dia = df[df['Fecha'] == fecha]
        if not dia.empty:
            cstr = dia['Metodo_Pago'].astype(str)
            def suma(x): return dia[cstr.str.contains(x, case=False)]['Monto'].sum()
            k1, k2 = st.columns(2); k1.metric("Pago Móvil", f"Bs {suma('Móvil|Movil'):,.0f}"); k2.metric("Efectivo", f"Bs {suma('Bs|Bolívares'):,.0f}")
            st.dataframe(dia[['Hora','Detalles_Compra','Monto','Metodo_Pago']], hide_index=True, use_container_width=True)
        else: st.info("No hay ventas hoy.")

with tab3:
    st.markdown("### 🚛 Cisterna")
    with st.form("cisterna"):
        c1, c2 = st.columns(2); f = c1.date_input("Día", datetime.now()); h = c2.time_input("Hora", datetime.now())
        l = st.number_input("Litros", 2000, step=100); n = st.text_input("Chofer")
        if st.form_submit_button("GUARDAR ENTRADA", use_container_width=True):
            if sheet_cargas:
                try: sheet_cargas.append_row([str(f), str(h), l, 0, n]); st.cache_data.clear(); st.success("¡Stock Actualizado!"); time.sleep(1); st.rerun()
                except Exception as e: st.error(f"Error: {e}")

with tab4:
    st.markdown("### 📅 Semanal")
    fecha_ref = st.date_input("Día Referencia:", datetime.now()); inicio = fecha_ref - timedelta(days=fecha_ref.weekday()); fin = inicio + timedelta(days=6)
    st.info(f"Semana: **{inicio.strftime('%d/%m')}** al **{fin.strftime('%d/%m')}**")
    df_v = pd.DataFrame(datos_ventas)
    if not df_v.empty:
        df_v['Fecha'] = pd.to_datetime(df_v['Fecha']).dt.date; mask = (df_v['Fecha'] >= inicio) & (df_v['Fecha'] <= fin); df_sem = df_v.loc[mask]
        if not df_sem.empty: st.success(f"💧 Vendido: {df_sem['Total_Litros'].sum():,.0f} L")
        else: st.warning("Cero ventas.")
