import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta
import time
import os
import extra_streamlit_components as stx
import streamlit.components.v1 as components 
import plotly.express as px # Restaurado para el Mapa de Calor

# --- 1. CONFIGURACIÓN E IDENTIDAD ---
st.set_page_config(page_title="Agua Control", page_icon="💧", layout="wide", initial_sidebar_state="expanded")

CARPETA_LOCAL = "image" # Actualizado a tu nueva carpeta
IMAGEN_POR_DEFECTO = "default.png"

if 'modo_vista' not in st.session_state:
    st.session_state.modo_vista = "📱 Móvil (Carrusel por defecto)"

# =====================================================================
# MOTOR INVISIBLE: PARA EL CARRUSEL
# =====================================================================
components.html("""
<script>
function activarCarrusel() {
    const bloques = window.parent.document.querySelectorAll('[data-testid="stHorizontalBlock"]');
    bloques.forEach(bloque => {
        if (bloque.innerHTML.includes('titulo-prod')) {
            bloque.classList.add('carrusel-movil');
            const columnas = bloque.querySelectorAll('[data-testid="column"]');
            columnas.forEach(col => col.classList.add('carrusel-item'));
        }
    });
}
activarCarrusel();
setInterval(activarCarrusel, 1000);
</script>
""", height=0, width=0)

st.markdown("""
<style>
    footer {visibility: hidden;}
    header {visibility: visible;}
    .block-container { max-width: 900px; margin: auto; padding-top: 1rem !important; }
    
    /* CAJAS Y BOTONES GLOBALES */
    [data-testid="stForm"], div.stContainer { background-color: white; border: 1px solid #e0e0e0; border-radius: 12px; padding: 10px !important; box-shadow: 0 2px 4px rgba(0,0,0,0.05); margin-bottom: 8px; }
    [data-testid="stFormSubmitButton"] button { background-color: #0078D7 !important; color: white !important; border: none !important; border-radius: 8px !important; font-weight: 800 !important; height: 50px !important; font-size: 16px !important; }
    [data-testid="stFormSubmitButton"] button:active { background-color: #005a9e !important; transform: scale(0.98); }
    div.stButton > button { border-radius: 8px !important; border: 1px solid #cccccc !important; color: #333 !important; background-color: transparent !important; height: 40px !important; }
    
    .info-bar { font-size: 12px; color: #666; background: #f0f2f6; padding: 5px 10px; border-radius: 5px; display: flex; justify-content: space-between; margin-bottom: 10px; }

    /* MÉTODOS DE PAGO EN NEGRITA GIGANTE */
    div[role="radiogroup"] label { font-size: 18px !important; font-weight: 900 !important; color: #111 !important; }

    /* ESTÉTICA DE TARJETAS */
    .titulo-prod { font-size: 14px !important; font-weight: 800; text-align: center; line-height: 1.1; margin-top: -5px !important; height: 32px; overflow: hidden; }
    .precio-prod { font-size: 13px !important; color: #0078D7; font-weight: 900; text-align: center; margin-bottom: 5px; }
    div.stImage > img { height: 95px !important; object-fit: contain !important; margin: 0 auto; display: block; }

    /* PÍLDORA DEL CARRITO NATIVA */
    div[data-testid="stNumberInput"] > div > div[data-baseweb="input"] { background-color: #f2f4f7 !important; border-radius: 20px !important; border: none !important; height: 38px !important; }
    div[data-testid="stNumberInput"] input { text-align: center !important; font-weight: 900 !important; font-size: 18px !important; color: #333 !important; }
</style>
""", unsafe_allow_html=True)

def now_vzla(): return datetime.utcnow() - timedelta(hours=4)

# --- 2. SISTEMA DE SEGURIDAD ---
def get_manager(): return stx.CookieManager(key="agua_manager_secure")

def check_auth():
    if st.session_state.get('auth_status', False): return True
    cookie_manager = get_manager()
    cookies = cookie_manager.get_all()
    if not cookies and 'intentos_auth' not in st.session_state:
        st.session_state['intentos_auth'] = 1
        with st.spinner("Conectando..."): time.sleep(0.5)
        st.rerun()
    if cookies and "agua_token_secure" in cookies:
        token_cookie = cookies.get("agua_token_secure")
        try:
            tokens_validos = st.secrets["tokens"]
            if token_cookie in tokens_validos or token_cookie == "admin_manual":
                st.session_state['auth_status'] = True
                st.session_state['usuario'] = "Admin" if token_cookie == "admin_manual" else token_cookie
                return True
        except: pass

    c1, c2, c3 = st.columns([1,2,1])
    logo_path = os.path.join(CARPETA_LOCAL, "logo.png")
    if os.path.exists(logo_path): 
        with c2: st.image(logo_path, use_container_width=True)

    st.markdown("### 🔒 Acceso")
    with st.form("login_manual"):
        password = st.text_input("Clave Maestra", type="password")
        if st.form_submit_button("Entrar", use_container_width=True):
            if password == st.secrets["passwords"]["main"]:
                st.session_state['auth_status'] = True
                st.session_state['usuario'] = "Admin"
                cookie_manager.set("agua_token_secure", "admin_manual", expires_at=now_vzla() + timedelta(days=1))
                st.rerun()
            else: st.error("Incorrecto")
    return False

if not check_auth(): st.stop()

# --- 3. CONEXIÓN DATOS ---
if 'cart_counter' not in st.session_state: st.session_state.cart_counter = 0

@st.cache_resource
def obtener_conexion():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = dict(st.secrets["gcp_service_account"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    return client.open("Gestion_Ventas_Agua")

@st.cache_data(ttl=60)
def cargar_datos_maestros():
    try:
        libro = obtener_conexion()
        try: sheet_prod = libro.worksheet("Productos").get_all_records()
        except: sheet_prod = []
        try: sheet_conf = libro.worksheet("Configuracion").get_all_records()
        except: sheet_conf = []
        try: sheet_inv = libro.worksheet("Inventario").get_all_records()
        except: sheet_inv = []
        return sheet_prod, sheet_conf, libro.worksheet("Cargas").get_all_records(), libro.sheet1.get_all_records(), sheet_inv
    except: return [], [], [], [], []

def procesar_maestros(datos_prod, datos_conf):
    productos = {}
    for f in datos_prod:
        nombre = str(f.get('Producto', '')).strip()
        if not nombre: continue
        codigo = str(f.get('Código_SKU', f.get('Código (SKU)', f.get('Codigo', f.get('SKU', nombre))))).strip()
        pr = float(str(f.get('Precio_Actual', 0)).replace(',', '.'))
        l = float(str(f.get('Litros', 0)).replace(',', '.'))
        categoria = str(f.get('Categoria', f.get('Categoría', '💧 Productos Generales'))).strip()
        imagen = str(f.get('Imagen', f.get('imagen', ''))).strip()
        ctrl_keys = [k for k in f.keys() if 'controla' in k.lower()]
        controla = str(f.get(ctrl_keys[0], 'NO')).strip().upper() in ['SI', 'SÍ', 'YES', 'TRUE'] if ctrl_keys else False
        productos[nombre] = {"precio": pr, "litros": l, "codigo": codigo, "controla_stock": controla, "categoria": categoria, "imagen": imagen}
    tasa = 60.0
    for c in datos_conf:
        if str(c.get('Parametro', '')).strip() == "TASA_DIA":
            try: tasa = float(str(c.get('Valor', 0)).replace(',', '.'))
            except: pass
    return productos, tasa

def calcular_stock(c, v):
    df_cargas = pd.DataFrame(c)
    ent = pd.to_numeric(df_cargas['Litros'], errors='coerce').sum() if not df_cargas.empty and 'Litros' in df_cargas.columns else 0
    sal = pd.DataFrame(v)['Total_Litros'].sum() if v else 0
    return ent - sal

try:
    d_prod, d_conf, d_cargas, d_ventas, d_inv = cargar_datos_maestros()
    productos_disponibles, tasa_global_db = procesar_maestros(d_prod, d_conf)
    stock = calcular_stock(d_cargas, d_ventas)
    libro_actual = obtener_conexion()
    sheet_ventas = libro_actual.sheet1
    sheet_cargas = libro_actual.worksheet("Cargas") if "Cargas" in [ws.title for ws in libro_actual.worksheets()] else None
    sheet_inventario = libro_actual.worksheet("Inventario") if "Inventario" in [ws.title for ws in libro_actual.worksheets()] else None
except:
    st.warning("⚠️ Reconectando..."); time.sleep(1); st.cache_data.clear(); st.rerun()

st.session_state.tasa_actual = max(tasa_global_db, 1.0) 

# ---------------- PREPARACIÓN GLOBAL DE DATOS ----------------
df_v = pd.DataFrame(d_ventas)
df_c = pd.DataFrame(d_cargas)
df_i = pd.DataFrame(d_inv)

if not df_v.empty and 'Monto' in df_v.columns:
    df_v['FechaDT'] = pd.to_datetime(df_v['Fecha'], errors='coerce') 
    df_v['Monto'] = pd.to_numeric(df_v['Monto'], errors='coerce').fillna(0)

if not df_c.empty:
    df_c.rename(columns={'Costo_Divisa': 'Costo_Bs', 'Notas': 'Concepto'}, inplace=True)
    df_c['FechaDT'] = pd.to_datetime(df_c['Fecha'], errors='coerce')
    df_c['Costo_Bs'] = pd.to_numeric(df_c['Costo_Bs'], errors='coerce').fillna(0)

if not df_i.empty:
    sku_col = next((col for col in df_i.columns if 'código' in col.lower() or 'sku' in col.lower() or 'codigo' in col.lower()), 'Item')
    df_i.rename(columns={sku_col: 'SKU_Calc'}, inplace=True)
    df_i['FechaDT'] = pd.to_datetime(df_i['Fecha'], errors='coerce')
    df_i['Costo_USD'] = pd.to_numeric(df_i['Costo_Bs'], errors='coerce').fillna(0) / pd.to_numeric(df_i['Tasa_Cambio'], errors='coerce').fillna(st.session_state.tasa_actual).replace(0, 1)

# =====================================================================
# FUNCIÓN DE NOTIFICACIÓN (TOAST)
# =====================================================================
def notificar_carrito(producto_nombre):
    st.toast(f"🛒 ¡**{producto_nombre}** actualizado en el pedido!", icon="✅")

# =====================================================================
# FUNCIÓN COMPARTIDA PARA DIBUJAR TARJETAS
# =====================================================================
def dibujar_tarjeta(p_name, info, c_key):
    nombre_img = str(info.get("imagen", "")).strip()
    ruta_final_img = os.path.join(CARPETA_LOCAL, IMAGEN_POR_DEFECTO)
    if nombre_img:
        ruta_intento = os.path.join(CARPETA_LOCAL, nombre_img)
        if os.path.exists(ruta_intento): ruta_final_img = ruta_intento

    with st.container(border=True):
        if os.path.exists(ruta_final_img): st.image(ruta_final_img, use_container_width=True)
        else: st.markdown("<div style='text-align:center; font-size:35px; padding:10px; height:95px;'>📦</div>", unsafe_allow_html=True)
        
        st.markdown(f"<div class='titulo-prod'>{p_name}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='precio-prod'>Bs {info['precio']:g}</div>", unsafe_allow_html=True)
        
        st.session_state.carrito[p_name] = st.number_input(
            "Cant", min_value=0, step=1, key=f"pos_{p_name}_{c_key}", 
            label_visibility="collapsed", 
            on_change=notificar_carrito, args=(p_name,)
        )

# =====================================================================
# MODAL FLOTANTE DE COBRO (CORRECCIÓN BOTONES +/-)
# =====================================================================
@st.dialog("💳 Finalizar Cobro")
def modal_cobro(total_bs, total_l, items_str, cant_recarga_20l, sheet_ventas, c_key):
    resumen_html = "<br>".join(items_str)
    st.markdown(f"<h3 style='text-align:center; color:#0078D7; margin-top:0; margin-bottom:10px;'>{resumen_html}</h3>", unsafe_allow_html=True)
    st.markdown("<hr style='margin-top: 0; margin-bottom: 15px;'>", unsafe_allow_html=True)
    st.markdown(f"<h2 style='text-align:center; color:#0078D7; margin-top:0;'>Total Pedido: Bs {total_bs:g}</h2>", unsafe_allow_html=True)
    
    metodo = st.radio("Selecciona Método de Pago:", ["Punto de Venta", "Efectivo", "Pago Móvil", "Mixto", "Divisa"], horizontal=True)
    tasa = st.session_state.tasa_actual
    
    es_combo_2x1 = (cant_recarga_20l == 2 and len(items_str) == 1)
    default_monto = 0.00 if metodo == "Divisa" else float(total_bs)
    if es_combo_2x1 and metodo == "Divisa": default_monto = 1.00

    with st.form("cobro_final"):
        # CORRECCIÓN 2: Ocultar los botones +/- del modal
        st.markdown("""<style>
            div[data-testid="stDialog"] button[title="Step down"], 
            div[data-testid="stDialog"] button[title="Step up"],
            div[data-testid="stDialog"] button[aria-label="Step down"], 
            div[data-testid="stDialog"] button[aria-label="Step up"],
            div[data-testid="stDialog"] [data-testid="stNumberInputStepDown"],
            div[data-testid="stDialog"] [data-testid="stNumberInputStepUp"] {
                display: none !important;
            }
        </style>""", unsafe_allow_html=True)

        if metodo != "Mixto":
            monto = st.number_input("Monto a Pagar", value=default_monto, step=None)
            ref = st.text_input("Referencia (Obligatoria para Pago Móvil/Punto)", max_chars=10)
            vuelto = st.number_input("📤 Vuelto entregado (Bs)", min_value=0.0, step=None) if metodo == "Divisa" else 0.0
        else:
            st.info("Pago Dividido")
            c1, c2 = st.columns(2)
            with c1: 
                m1_met = st.selectbox("Método 1", ["Efectivo", "Pago Móvil", "Divisa", "Punto de Venta"])
                m1_mon = st.number_input("Monto 1", value=0.0, step=None)
                m1_ref = st.text_input("Ref 1", max_chars=10)
            with c2: 
                m2_met = st.selectbox("Método 2", ["Punto de Venta", "Divisa", "Pago Móvil", "Efectivo"])
                m2_mon = st.number_input("Monto 2", value=0.0, step=None)
                m2_ref = st.text_input("Ref 2", max_chars=10)
            vuelto = 0.0

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""<style>div.stButton > button[kind="primary"] { background-color: #28a745 !important; color: white !important; height: 50px !important; font-size: 18px !important; }</style>""", unsafe_allow_html=True)
        
        if st.form_submit_button("✅ REGISTRAR VENTA", use_container_width=True):
            if metodo in ["Punto de Venta", "Pago Móvil"] and not ref.strip(): st.error("⚠️ Referencia obligatoria.")
            elif metodo == "Mixto" and ((m1_met in ["Punto de Venta", "Pago Móvil"] and not m1_ref.strip()) or (m2_met in ["Punto de Venta", "Pago Móvil"] and not m2_ref.strip())): st.error("⚠️ Falta referencia en el método electrónico.")
            else:
                try:
                    f_act = now_vzla().strftime("%Y-%m-%d"); h_act = now_vzla().strftime("%H:%M:%S")
                    vend = st.session_state.get('usuario', 'Admin'); ts = st.session_state.tasa_actual; txt = ", ".join(items_str)
                    
                    if metodo != "Mixto":
                        mon = "USD" if "Divisa" in metodo else "VES"
                        sheet_ventas.append_row([f_act, h_act, vend, txt, monto, mon, ts, metodo, ref or "N/A", total_l, "Activa"])
                        if vuelto > 0: sheet_ventas.append_row([f_act, h_act, vend, f"Vuelto ({txt})", -vuelto, "VES", ts, "Efectivo", "Salida Caja", 0, "Activa"])
                    else:
                        m1_mon_usd = "USD" if "Divisa" in m1_met else "VES"
                        sheet_ventas.append_row([f_act, h_act, vend, txt, m1_mon, m1_mon_usd, ts, m1_met, m1_ref or "N/A", total_l, "Activa"])
                        if m2_mon > 0: 
                            m2_mon_usd = "USD" if "Divisa" in m2_met else "VES"
                            sheet_ventas.append_row([f_act, h_act, vend, "Complemento Mixto", m2_mon, m2_mon_usd, ts, m2_met, m2_ref or "N/A", 0, "Activa"])
                    
                    st.cache_data.clear()
                    st.session_state.cart_counter += 1 
                    
                    st.success("✅ Venta exitosa")
                    time.sleep(1)
                    st.rerun() 
                    
                except Exception as e: st.error(f"Error: {e}")

# =====================================================================
# MENÚ HAMBURGUESA (SIDEBAR)
# =====================================================================
with st.sidebar:
    opciones_menu = ["🛒 VENDER", "📊 DIARIO", "🚛 CISTERNA", "📅 BALANCE", "⚙️ CONFIGURACIÓN"]
    if st.session_state.get('usuario', '').lower() == "admin":
        opciones_menu.extend(["🏦 CAJA GENERAL", "📦 INVENTARIO", "💸 NÓMINA", "🏧 DEPÓSITOS", "📈 MAPA DE CALOR"])
    
    seleccion = st.radio("Navegación", opciones_menu, label_visibility="collapsed")
    
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    st.divider()
    if st.button("🔄 Actualizar Datos", use_container_width=True):
        st.cache_data.clear(); st.rerun()
    if st.button("🔓 Cerrar Sesión", use_container_width=True):
        get_manager().delete("agua_token_secure")
        st.session_state.clear(); st.query_params.clear(); time.sleep(0.5); st.rerun()

# =====================================================================
# LOGO Y FRANJA GENERAL (Aparece en TODAS las pestañas)
# =====================================================================
c1, c2, c3 = st.columns([1, 2, 1])
with c2:
    ruta_logo = os.path.join(CARPETA_LOCAL, "logo.png")
    if os.path.exists(ruta_logo): st.image(ruta_logo, use_container_width=True)
    else: st.markdown("<h1 style='text-align:center;'>💧 Agua Control</h1>", unsafe_allow_html=True)

vend = st.session_state.get('usuario', 'Anon').upper()
ts = st.session_state.tasa_actual
st.markdown(f"""<div class="info-bar"><span>👤 <b>{vend}</b></span><span>💵 Tasa: <b>{ts} Bs/$</b></span></div>""", unsafe_allow_html=True)

# =====================================================================
# CONTROLADOR DE PÁGINAS
# =====================================================================

if seleccion == "🛒 VENDER":
    with st.expander("🔄 Actualizar Tasa del Día", expanded=False):
        nueva_tasa = st.number_input("Tasa Actual (Bs/$)", value=st.session_state.tasa_actual, step=0.1, key="global_tasa")
        if st.button("💾 Guardar Tasa"):
            try:
                ws_conf = libro_actual.worksheet("Configuracion")
                cell = ws_conf.find("TASA_DIA")
                if cell: ws_conf.update_cell(cell.row, cell.col + 1, nueva_tasa)
                else: ws_conf.append_row(["TASA_DIA", nueva_tasa])
                st.cache_data.clear(); st.success("¡Tasa Actualizada!"); time.sleep(1); st.rerun()
            except Exception as e: st.error(f"Error: {e}")

    color_st = "#D32F2F" if stock < 200 else "#0078D7"
    st.markdown(f"""
    <div style="padding:15px; background:linear-gradient(90deg, #f8f9fa 0%, #e9ecef 100%); border-radius:12px; margin-bottom:15px; margin-top:5px; border-left:5px solid {color_st}; display:flex; justify-content:space-between; align-items:center;">
        <div style="font-size:12px; color:#555; font-weight:bold;">TANQUE<br>DISPONIBLE</div>
        <div style="font-size:28px; font-weight:900; color:{color_st};">{stock:,.0f} L</div>
    </div>
    """, unsafe_allow_html=True)

    if 'carrito' not in st.session_state: st.session_state.carrito = {}
    
    if not productos_disponibles:
        st.warning("⚠️ No se encontraron productos.")
    else:
        categorias_dict = {}
        for nom, dat in productos_disponibles.items():
            cat = dat["categoria"] if dat["categoria"] else "💧 Otros"
            if cat not in categorias_dict: categorias_dict[cat] = []
            categorias_dict[cat].append(nom)

        c_key = st.session_state.cart_counter 

        for cat, prods in categorias_dict.items():
            st.markdown(f"**{cat}**")
            
            if "Móvil" in st.session_state.modo_vista:
                st.markdown("""<style>
                    .block-container div[data-testid="stHorizontalBlock"] { flex-wrap: nowrap !important; overflow-x: auto !important; scroll-snap-type: x mandatory; padding-bottom: 10px !important; }
                    .block-container div[data-testid="stHorizontalBlock"] > div[data-testid="column"] { min-width: 145px !important; max-width: 145px !important; scroll-snap-align: center; }
                    .block-container div[data-testid="stHorizontalBlock"]::-webkit-scrollbar { display: none; }
                </style>""", unsafe_allow_html=True)
                
                # CORRECCIÓN 1: No crear 4 columnas por defecto, solo las necesarias.
                num_cols = max(len(prods), 1) 
                cols = st.columns(num_cols)
                for i, p_name in enumerate(prods):
                    with cols[i]:
                        dibujar_tarjeta(p_name, productos_disponibles[p_name], c_key)
            else:
                MAX_COLS = 4
                for i in range(0, len(prods), MAX_COLS):
                    chunk = prods[i:i + MAX_COLS]
                    cols = st.columns(MAX_COLS) 
                    for j, p_name in enumerate(chunk):
                        with cols[j]:
                            dibujar_tarjeta(p_name, productos_disponibles[p_name], c_key)

        # --- RESUMEN DEL CARRITO ---
        productos_en_carrito = [p for p in productos_disponibles.keys() if st.session_state.get(f"pos_{p}_{c_key}", 0) > 0]
        
        if productos_en_carrito:
            st.divider()
            col_t, col_b = st.columns([3, 1], vertical_alignment="center")
            col_t.markdown("### 🛒 Tu Pedido")
            if col_b.button("🗑️ VACIAR", use_container_width=True):
                st.session_state.cart_counter += 1
                st.rerun()

            total_bs = 0; total_l = 0; items_str = []
            cant_recarga_20l = st.session_state.get(f"pos_Recarga Botellón 20L_{c_key}", 0)

            for p in productos_en_carrito:
                q = st.session_state[f"pos_{p}_{c_key}"]
                dat = productos_disponibles[p]
                sub = dat['precio'] * q
                total_bs += sub; total_l += dat['litros'] * q
                items_str.append(f"{q}x {p}")
                st.markdown(f"<div style='border-bottom:1px solid #eee; padding:5px 0;'><b>{p}</b><br><span style='color:#666; font-size:13px;'>Cant: {q} | </span><b style='color:#0078D7;'>Bs {sub:g}</b></div>", unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("""<style>div.stButton > button[kind="primary"] { background-color: #0078D7 !important; color: white !important; height: 50px !important; font-weight: 900 !important; font-size: 16px !important; }</style>""", unsafe_allow_html=True)
            
            if st.button("💳 CONTINUAR AL COBRO", type="primary", use_container_width=True):
                modal_cobro(total_bs, total_l, items_str, cant_recarga_20l, sheet_ventas, c_key)

elif seleccion == "⚙️ CONFIGURACIÓN":
    st.header("⚙️ Configuración Visual")
    nuevo_modo = st.radio("Diseño de Catálogo de Productos:", ["📱 Móvil (Carrusel por defecto)", "💻 Forzar PC (Grilla)"], index=0 if "Móvil" in st.session_state.modo_vista else 1)
    if nuevo_modo != st.session_state.modo_vista:
        st.session_state.modo_vista = nuevo_modo
        st.rerun()

elif seleccion == "📊 DIARIO":
    st.header("📊 Diario")
    fecha = st.date_input("Fecha", now_vzla())
    if not df_v.empty and 'FechaDT' in df_v.columns:
        fecha_dt = pd.to_datetime(fecha)
        dia = df_v[df_v['FechaDT'] == fecha_dt]
        if not dia.empty:
            def suma_cond(metodo_txt): return dia[dia['Metodo_Pago'].astype(str).str.contains(metodo_txt, case=False, na=False)]['Monto'].sum()
            movil = suma_cond('Móvil|Movil'); efectivo = suma_cond('Efectivo|Bs'); punto = suma_cond('Punto'); divisa = suma_cond('Divisa|\$')
            mask_bs_dia = ~dia['Metodo_Pago'].str.contains('Divisa|\$', case=False, na=False)
            total_bs_convertidos = dia.loc[mask_bs_dia, 'Monto'].sum() / st.session_state.tasa_actual
            gran_total_usd = divisa + total_bs_convertidos
            
            k1, k2, k3 = st.columns(3)
            k1.metric("Pago Móvil", f"Bs {movil:,.2f}"); k2.metric("Efectivo Neto", f"Bs {efectivo:,.2f}"); k3.metric("Divisas ($)", f"$ {divisa:,.2f}")
            st.markdown("---"); c1, c2 = st.columns(2)
            c1.metric("Punto Venta", f"Bs {punto:,.2f}"); c2.metric("💰 Ventas Netas del Día (Aprox $)", f"$ {gran_total_usd:,.2f}")
            
            st.divider(); st.markdown(f"#### 📦 Resumen de Productos")
            conteo_dia = {}
            for item in dia['Detalles_Compra'].dropna():
                for i in str(item).split(", "):
                    if "x " in i and "Vuelto" not in i:
                        try: q, n = i.split("x ", 1); conteo_dia[n.strip()] = conteo_dia.get(n.strip(), 0) + int(q)
                        except: pass
            if conteo_dia: st.dataframe(pd.DataFrame(list(conteo_dia.items()), columns=['Producto', 'Vendidos']).sort_values(by='Vendidos', ascending=False), hide_index=True, use_container_width=True)
            st.divider(); st.dataframe(dia[['Hora','Vendedor','Detalles_Compra','Monto','Moneda','Metodo_Pago']], hide_index=True, use_container_width=True)
        else: st.info("Sin ventas hoy.")

elif seleccion == "🚛 CISTERNA":
    st.header("🚛 Carga de Cisterna")
    with st.form("cisterna"):
        c1, c2 = st.columns(2)
        f = c1.date_input("Día", now_vzla()); h = c2.time_input("Hora", now_vzla())
        l = st.number_input("Litros de la Cisterna", 2000, step=100)
        costo_bs = st.number_input("Costo Pagado (Bs)", min_value=0.0, step=1.0)
        n = st.text_input("Chofer / Proveedor")
        if st.form_submit_button("GUARDAR CARGA", use_container_width=True):
            if sheet_cargas is not None:
                sheet_cargas.append_row([str(f), str(h), l, costo_bs, n, st.session_state.tasa_actual])
                st.cache_data.clear(); st.rerun()
    if not df_c.empty:
        df_cisternas = df_c[~df_c['Concepto'].astype(str).str.contains('GASTO/NÓMINA|DEPÓSITO', case=False, na=False)]
        if not df_cisternas.empty: st.dataframe(df_cisternas.sort_values(by=['Fecha'], ascending=False)[['Fecha', 'Litros', 'Costo_Bs', 'Concepto']], hide_index=True, use_container_width=True)

elif seleccion == "📅 BALANCE":
    st.header("📅 Balance de Rendimiento")
    fechas = st.date_input("Selecciona el rango", [now_vzla().date() - timedelta(days=7), now_vzla().date()], max_value=now_vzla().date())
    if len(fechas) == 2:
        f_inicio_dt, f_fin_dt = pd.to_datetime(fechas[0]), pd.to_datetime(fechas[1])
        tasa = st.session_state.tasa_actual; v_usd = 0.0; c_usd = 0.0; s_usd = 0.0; i_usd = 0.0
        df_v_rango = pd.DataFrame()
        if not df_v.empty and 'FechaDT' in df_v.columns:
            df_v_rango = df_v[(df_v['FechaDT'] >= f_inicio_dt) & (df_v['FechaDT'] <= f_fin_dt)]
            v_usd = df_v_rango[df_v_rango['Metodo_Pago'].str.contains('Divisa', case=False, na=False)]['Monto'].sum() + (df_v_rango[~df_v_rango['Metodo_Pago'].str.contains('Divisa', case=False, na=False)]['Monto'].sum() / tasa)
        if not df_c.empty and 'FechaDT' in df_c.columns:
            rango_c = df_c[(df_c['FechaDT'] >= f_inicio_dt) & (df_c['FechaDT'] <= f_fin_dt)]
            mask_g = rango_c['Concepto'].str.contains('GASTO', case=False, na=False)
            mask_d = rango_c['Concepto'].str.contains('DEPÓSITO', case=False, na=False)
            c_usd = rango_c[~(mask_g | mask_d)]['Costo_Bs'].sum() / tasa
            s_usd = rango_c[mask_g]['Costo_Bs'].sum() / tasa
        if not df_i.empty and 'FechaDT' in df_i.columns:
            i_usd = df_i[(df_i['FechaDT'] >= f_inicio_dt) & (df_i['FechaDT'] <= f_fin_dt)]['Costo_USD'].sum()
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Ingresos (+)", f"$ {v_usd:,.2f}"); c2.metric("Agua (-)", f"$ {c_usd:,.2f}"); c3.metric("Gastos (-)", f"$ {(s_usd + i_usd):,.2f}"); c4.metric("UTILIDAD", f"$ {(v_usd - c_usd - s_usd - i_usd):,.2f}")
        
        st.divider()
        st.markdown("#### 📦 Resumen de Productos Vendidos")
        if not df_v_rango.empty:
            conteo = {}
            for item in df_v_rango['Detalles_Compra'].dropna():
                for i in str(item).split(", "):
                    if "x " in i and "Vuelto" not in i:
                        try: q, n = i.split("x ", 1); conteo[n.strip()] = conteo.get(n.strip(), 0) + int(q)
                        except: pass
            if conteo:
                df_conteo = pd.DataFrame(list(conteo.items()), columns=['Producto', 'Cantidad Vendida']).sort_values(by='Cantidad Vendida', ascending=False)
                st.dataframe(df_conteo, hide_index=True, use_container_width=True)
            else: st.info("No hay productos detallados en este rango.")

elif seleccion == "🏦 CAJA GENERAL":
    st.header("🏦 Caja General")
    caja_total_usd = 0.0; ventas_totales_usd = 0.0; total_litros_historicos = 0
    if not df_v.empty:
        divisa_tot = df_v[df_v['Metodo_Pago'].astype(str).str.contains('Divisa|\$', case=False, na=False)]['Monto'].sum()
        bs_tot_ingresos = df_v[~df_v['Metodo_Pago'].astype(str).str.contains('Divisa|\$', case=False, na=False)]['Monto'].sum()
        ventas_totales_usd = divisa_tot + (bs_tot_ingresos / st.session_state.tasa_actual)
        total_litros_historicos = pd.to_numeric(df_v['Total_Litros'], errors='coerce').sum() if 'Total_Litros' in df_v.columns else 0
        bs_tot_egresos = df_c[~df_c['Concepto'].astype(str).str.contains('DEPÓSITO', case=False, na=False)]['Costo_Bs'].sum() if not df_c.empty else 0.0
        bs_tot_inventario_usd = df_i['Costo_USD'].sum() if not df_i.empty else 0.0
        caja_total_usd = ventas_totales_usd - (bs_tot_egresos / st.session_state.tasa_actual) - bs_tot_inventario_usd
    st.markdown(f"<div style='background-color: #e6f7ff; border: 2px solid #0078D7; padding: 15px; border-radius: 10px; text-align: center; margin-bottom: 20px;'><h3>Caja Total Histórica: $ {caja_total_usd:,.2f}</h3></div>", unsafe_allow_html=True)
    
    st.divider(); st.subheader("💧 Análisis del Valor del Agua")
    costo_litro_usd = 0.0
    if not df_c.empty:
        mask_cisternas = ~df_c['Concepto'].astype(str).str.contains('GASTO/NÓMINA|DEPÓSITO', case=False, na=False)
        df_solo_cisternas = df_c[mask_cisternas]
        if not df_solo_cisternas.empty:
            ultima_cist = df_solo_cisternas.sort_values(by=['Fecha'], ascending=False).iloc[0]
            l_uc = pd.to_numeric(ultima_cist['Litros']); bs_uc = pd.to_numeric(ultima_cist['Costo_Bs'])
            tasa_uc = pd.to_numeric(ultima_cist.get('Tasa_Cambio', st.session_state.tasa_actual))
            if pd.isna(tasa_uc) or tasa_uc <= 0: tasa_uc = st.session_state.tasa_actual
            if l_uc > 0: costo_litro_usd = (bs_uc / tasa_uc) / l_uc
    promedio_venta_litro_usd = (ventas_totales_usd / total_litros_historicos) if total_litros_historicos > 0 else 0.0
    c1, c2 = st.columns(2)
    c1.metric("Costo por Litro (Última Cisterna)", f"$ {costo_litro_usd:,.4f}")
    margen_historico = f"{((promedio_venta_litro_usd - costo_litro_usd) / costo_litro_usd * 100):.0f}% de Margen" if costo_litro_usd > 0 else "N/A"
    c2.metric("Precio Promedio de Venta (Histórico)", f"$ {promedio_venta_litro_usd:,.4f}", delta=margen_historico)
    
    st.divider(); st.subheader("💡 Sugerencia de Precios (Punto de Equilibrio)")
    datos_sugeridos = []
    for nombre, data in productos_disponibles.items():
        costo_base = 0.0
        if data['litros'] > 0: costo_base += (data['litros'] * costo_litro_usd)
        sku = data['codigo']
        if 'botellón' in nombre.lower() and 'recarga' not in nombre.lower():
            if not df_i.empty and 'SKU_Calc' in df_i.columns:
                df_b = df_i[df_i['SKU_Calc'].astype(str).str.strip() == sku]
                cant_b = df_b['Cantidad'].sum()
                if cant_b > 0: costo_base += (df_b['Costo_USD'].sum() / cant_b)
            if sku_tapa and not df_i.empty and 'SKU_Calc' in df_i.columns:
                df_t = df_i[df_i['SKU_Calc'].astype(str).str.strip() == sku_tapa]
                cant_t = df_t['Cantidad'].sum()
                if cant_t > 0: costo_base += (df_t['Costo_USD'].sum() / cant_t)
        elif 'tapa' in nombre.lower():
            if not df_i.empty and 'SKU_Calc' in df_i.columns:
                df_t = df_i[df_i['SKU_Calc'].astype(str).str.strip() == sku]
                cant_t = df_t['Cantidad'].sum()
                if cant_t > 0: costo_base += (df_t['Costo_USD'].sum() / cant_t)
        precio_actual_usd = data['precio'] / st.session_state.tasa_actual
        datos_sugeridos.append({"Producto": nombre, "Costo Real ($)": f"${costo_base:.3f}", "Tu Precio Hoy ($)": f"${precio_actual_usd:.2f}", "Sugerido (+30%)": f"${(costo_base * 1.30):.2f}", "Sugerido (+50%)": f"${(costo_base * 1.50):.2f}"})
    if datos_sugeridos: st.dataframe(pd.DataFrame(datos_sugeridos), hide_index=True, use_container_width=True)

elif seleccion == "📦 INVENTARIO":
    st.header("📦 Gestión de Insumos y Rentabilidad")
    opciones_compra = {data['codigo']: nombre for nombre, data in productos_disponibles.items() if data['controla_stock']}
    with st.form("form_inventario"):
        st.markdown("##### 📥 Registrar Nueva Compra")
        if opciones_compra:
            c1, c2 = st.columns([2, 1])
            sku_seleccionado = c1.selectbox("Producto Comprado", options=list(opciones_compra.keys()), format_func=lambda x: opciones_compra[x])
            cant_compra = c2.number_input("Cantidad Física", min_value=1, step=10)
            c3, c4 = st.columns(2)
            moneda_compra = c3.selectbox("Moneda Usada", ["Divisas ($)", "Bolívares (Bs)"])
            costo_compra = c4.number_input("Costo TOTAL Pagado", min_value=0.0, step=1.0)
            if st.form_submit_button("Guardar Compra", use_container_width=True):
                if sheet_inventario is not None and costo_compra > 0:
                    h_act = now_vzla().strftime("%H:%M:%S"); f_act = now_vzla().strftime("%Y-%m-%d"); tasa_hoy = st.session_state.tasa_actual
                    monto_guardar_bs = costo_compra * tasa_hoy if "Divisas" in moneda_compra else costo_compra
                    sheet_inventario.append_row([str(f_act), str(h_act), sku_seleccionado, cant_compra, monto_guardar_bs, tasa_hoy])
                    st.cache_data.clear(); st.rerun()
        else: st.warning("⚠️ No hay productos marcados con 'SI' en Controla_Stock.")
    
    st.divider(); st.markdown("##### 🧮 Tablero Maestro de Rentabilidad")
    datos_maestros = []
    for nombre, data in productos_disponibles.items():
        if data['controla_stock']:
            sku = data['codigo']; cant_comprada = 0; costo_total_usd = 0.0
            if not df_i.empty and 'SKU_Calc' in df_i.columns:
                df_filtro = df_i[df_i['SKU_Calc'].astype(str).str.strip() == sku]
                cant_comprada = df_filtro['Cantidad'].sum()
                costo_total_usd = df_filtro['Costo_USD'].sum()
            cant_vendida = ventas_por_sku.get(sku, 0); stock_actual = cant_comprada - cant_vendida
            costo_unitario_usd = (costo_total_usd / cant_comprada) if cant_comprada > 0 else 0.0
            precio_venta_usd = data['precio'] / st.session_state.tasa_actual
            margen = f"{((precio_venta_usd - costo_unitario_usd) / costo_unitario_usd) * 100:.0f}%" if costo_unitario_usd > 0 and precio_venta_usd > 0 else "N/A"
            datos_maestros.append({"SKU": sku, "Producto": nombre, "Stock Real": stock_actual, "Costo c/u ($)": f"${costo_unitario_usd:.3f}", "Precio Venta ($)": f"${precio_venta_usd:.2f}", "Margen": margen})
    if datos_maestros: st.dataframe(pd.DataFrame(datos_maestros), hide_index=True, use_container_width=True)

elif seleccion == "💸 NÓMINA":
    st.header("💸 Pagar Nómina o Gasto Variable")
    with st.form("form_sueldos"):
        c1, c2, c3 = st.columns([2, 1, 1])
        concepto = c1.text_input("Concepto")
        moneda_gasto = c2.selectbox("Moneda Usada", ["Divisas ($)", "Bolívares (Bs)"])
        monto_gasto = c3.number_input("Monto Numérico", min_value=0.0, step=1.0)
        if st.form_submit_button("REGISTRAR GASTO", use_container_width=True) and monto_gasto > 0:
            monto_guardar_bs = monto_gasto * st.session_state.tasa_actual if "Divisas" in moneda_gasto else monto_gasto
            if sheet_cargas is not None:
                sheet_cargas.append_row([now_vzla().strftime("%Y-%m-%d"), now_vzla().strftime("%H:%M:%S"), 0, monto_guardar_bs, f"GASTO/NÓMINA: {concepto}", st.session_state.tasa_actual])
                st.cache_data.clear(); st.rerun()

elif seleccion == "🏧 DEPÓSITOS":
    st.header("🏧 Mover Efectivo a la Cuenta")
    with st.form("form_deposito"):
        c1, c2 = st.columns(2)
        tipo_entrada = c1.selectbox("Tipo de Movimiento", ["Depósito en Cuenta", "Transferencia de Efectivo"])
        ref_dep = c2.text_input("Referencia")
        c3, c4 = st.columns(2)
        moneda_dep = c3.selectbox("Moneda Física", ["Efectivo Bs", "Divisas ($)"])
        monto_dep = c4.number_input("Monto Depositado", min_value=0.0, step=1.0)
        if st.form_submit_button("REGISTRAR MOVIMIENTO", use_container_width=True) and monto_dep > 0:
            monto_guardar_bs = monto_dep * st.session_state.tasa_actual if "Divisas" in moneda_dep else monto_dep
            if sheet_cargas is not None:
                sheet_cargas.append_row([now_vzla().strftime("%Y-%m-%d"), now_vzla().strftime("%H:%M:%S"), 0, monto_guardar_bs, f"DEPÓSITO: {tipo_entrada} (Ref: {ref_dep})", st.session_state.tasa_actual])
                st.cache_data.clear(); st.rerun()

elif seleccion == "📈 MAPA DE CALOR":
    st.header("📈 Horario Comercial de Ventas")
    opcion_filtro = st.radio("Selecciona los datos a analizar:", ["Historial Completo", "Por Rango de Fechas"], horizontal=True)
    fechas_hm = st.date_input("Rango", [now_vzla().date() - timedelta(days=7), now_vzla().date()], max_value=now_vzla().date()) if opcion_filtro == "Por Rango de Fechas" else None
    
    if not df_v.empty and 'Hora' in df_v.columns and 'Fecha' in df_v.columns:
        df_hm = df_v.copy()
        if fechas_hm is not None and len(fechas_hm) == 2:
            df_hm['Fecha_Date'] = pd.to_datetime(df_hm['Fecha'], errors='coerce').dt.date
            df_hm = df_hm[(df_hm['Fecha_Date'] >= fechas_hm[0]) & (df_hm['Fecha_Date'] <= fechas_hm[1])]
        
        if not df_hm.empty:
            df_hm['FechaDT'] = pd.to_datetime(df_hm['Fecha'].astype(str) + ' ' + df_hm['Hora'], errors='coerce')
            df_hm = df_hm.dropna(subset=['FechaDT'])
            if not df_hm.empty:
                df_hm['Hora_Int'] = df_hm['FechaDT'].dt.hour
                df_hm = df_hm[(df_hm['Hora_Int'] >= 9) & (df_hm['Hora_Int'] <= 21)]
                if not df_hm.empty:
                    df_hm['Dia'] = df_hm['FechaDT'].dt.day_name()
                    dias_es = {'Monday':'Lunes', 'Tuesday':'Martes', 'Wednesday':'Miércoles', 'Thursday':'Jueves', 'Friday':'Viernes', 'Saturday':'Sábado', 'Sunday':'Domingo'}
                    df_hm['Dia'] = df_hm['Dia'].map(dias_es)
                    
                    hm_grouped = df_hm.groupby(['Dia', 'Hora_Int']).size().reset_index(name='Ventas')
                    hm_pivot = hm_grouped.pivot(index='Dia', columns='Hora_Int', values='Ventas').fillna(0)
                    
                    dias_orden = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
                    horas_orden = list(range(9, 22))
                    hm_pivot = hm_pivot.reindex(index=dias_orden, columns=horas_orden, fill_value=0)
                    horas_str = [f"{h}:00" for h in horas_orden]
                    
                    fig = px.imshow(hm_pivot, labels=dict(x="Hora del Día", y="Día de la Semana", color="Cantidad de Ventas"), x=horas_str, y=dias_orden, aspect="auto", text_auto=True, color_continuous_scale="Blues")
                    fig.update_xaxes(side="top")
                    st.plotly_chart(fig, use_container_width=True)
                    
                    st.divider(); st.markdown("#### ⏱️ Resumen de Tráfico")
                    resumen_horas = df_hm.groupby('Hora_Int').size().reindex(horas_orden, fill_value=0).reset_index(name='Total_Ventas')
                    idx_max = resumen_horas['Total_Ventas'].idxmax()
                    idx_min = resumen_horas['Total_Ventas'].idxmin()
                    
                    def formato_hora(h): return f"{h if h <= 12 else h - 12}:00 {'AM' if h < 12 else 'PM'}"
                    
                    c1, c2 = st.columns(2)
                    c1.success(f"🔥 **Mayor Tráfico:** {formato_hora(int(resumen_horas.loc[idx_max, 'Hora_Int']))}\n\nAcumulando **{int(resumen_horas.loc[idx_max, 'Total_Ventas'])} transacciones**.")
                    c2.warning(f"🧊 **Menor Tráfico:** {formato_hora(int(resumen_horas.loc[idx_min, 'Hora_Int']))}\n\nCon solo **{int(resumen_horas.loc[idx_min, 'Total_Ventas'])} transacciones**.")
                else: st.warning("No hay ventas entre 9 AM y 9 PM.")
            else: st.warning("Fechas inválidas.")
        else: st.warning("Sin ventas en este rango.")
