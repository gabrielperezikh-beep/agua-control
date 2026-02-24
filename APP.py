import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta
import time
import os
import extra_streamlit_components as stx
import plotly.express as px

# --- 1. CONFIGURACIÓN E IDENTIDAD ---
st.set_page_config(page_title="Agua Control", page_icon="logo.png", layout="wide")

st.markdown("""
<style>
    footer {visibility: hidden;}
    header {visibility: visible;}
    .block-container { max-width: 900px; margin: auto; padding-top: 2rem !important; }
    [data-testid="column"] { min-width: 10px !important; padding: 0 2px !important; }
    [data-testid="stForm"], div.stContainer { background-color: white; border: 1px solid #e0e0e0; border-radius: 12px; padding: 10px !important; box-shadow: 0 2px 4px rgba(0,0,0,0.05); margin-bottom: 8px; }
    [data-testid="stForm"] button { background-color: #0078D7 !important; color: white !important; border: none !important; border-radius: 8px !important; font-weight: 800 !important; height: 50px !important; font-size: 16px !important; }
    [data-testid="stForm"] button:active { background-color: #005a9e !important; transform: scale(0.98); }
    div.stButton > button { border-radius: 8px !important; border: 1px solid #ff4b4b !important; color: #ff4b4b !important; background-color: transparent !important; height: 40px !important; }
    .prod-name { font-weight: 700; font-size: 15px; color: #333; }
    .prod-price { font-weight: 800; font-size: 15px; color: #0078D7; }
    div[data-testid="stNumberInput"] input { font-size: 22px; font-weight: bold; text-align: center; }
    .info-bar { font-size: 12px; color: #666; background: #f0f2f6; padding: 5px 10px; border-radius: 5px; display: flex; justify-content: space-between; margin-bottom: 10px; }
</style>
""", unsafe_allow_html=True)

def now_vzla(): return datetime.utcnow() - timedelta(hours=4)

# --- 2. SISTEMA DE SEGURIDAD Y ANTI-PARPADEO ---
def get_manager(): return stx.CookieManager(key="agua_manager_secure")

def check_auth():
    if st.session_state.get('auth_status', False): return True
    cookie_manager = get_manager()
    params = st.query_params
    token_url = params.get("token", None)
    
    if token_url:
        try: tokens_validos = st.secrets["tokens"]
        except: st.error("⚠️ Falta configurar [tokens]"); st.stop()
        if token_url in tokens_validos:
            st.session_state['auth_status'] = True
            st.session_state['usuario'] = token_url
            cookie_manager.set("agua_token_secure", token_url, expires_at=now_vzla() + timedelta(days=90))
            st.query_params.clear(); st.rerun(); return True
        else: st.error("⛔ Enlace inválido."); st.stop()

    cookies = cookie_manager.get_all()
    
    # 🛡️ ESCUDO ANTI-PARPADEO: Da tiempo al navegador a enviar la cookie si la app se "durmió"
    if not cookies and 'intentos_auth' not in st.session_state:
        st.session_state['intentos_auth'] = 1
        with st.spinner("Conectando de forma segura..."):
            time.sleep(0.5)
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
    if os.path.exists("logo.png"): 
        with c2: st.image("logo.png", use_container_width=True)

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
if 'carrito' not in st.session_state: st.session_state.carrito = {}

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
        return sheet_prod, sheet_conf, libro.worksheet("Cargas").get_all_records(), libro.sheet1.get_all_records()
    except: return [], [], [], []

def procesar_maestros(datos_prod, datos_conf):
    productos = {}
    for f in datos_prod:
        nombre = str(f.get('Producto', '')).strip()
        if not nombre: continue
        pr = float(str(f.get('Precio_Actual', 0)).replace(',', '.'))
        l = float(str(f.get('Litros', 0)).replace(',', '.'))
        productos[nombre] = {"precio": pr, "litros": l}

    tasa = 60.0
    for c in datos_conf:
        param = str(c.get('Parametro', '')).strip()
        if param == "TASA_DIA":
            try: tasa = float(str(c.get('Valor', 0)).replace(',', '.'))
            except: pass
    return productos, tasa

def calcular_stock(c, v):
    df_cargas = pd.DataFrame(c)
    ent = pd.to_numeric(df_cargas['Litros'], errors='coerce').sum() if not df_cargas.empty and 'Litros' in df_cargas.columns else 0
    sal = pd.DataFrame(v)['Total_Litros'].sum() if v else 0
    return ent - sal

try:
    d_prod, d_conf, d_cargas, d_ventas = cargar_datos_maestros()
    productos_disponibles, tasa_global_db = procesar_maestros(d_prod, d_conf)
    stock = calcular_stock(d_cargas, d_ventas)
    libro_actual = obtener_conexion()
    sheet_ventas = libro_actual.sheet1
    try: sheet_cargas = libro_actual.worksheet("Cargas")
    except: sheet_cargas = None
except:
    st.warning("⚠️ Reconectando..."); time.sleep(1); st.cache_data.clear(); st.rerun()

st.session_state.tasa_actual = max(tasa_global_db, 1.0) 

# --- BARRA SUPERIOR ---
c_logo, c_info, c_logout = st.columns([1, 4, 1], vertical_alignment="center")
with c_logo:
    if os.path.exists("logo.png"): st.image("logo.png", use_container_width=True)
    else: st.write("💧")

with c_info:
    vend = st.session_state.get('usuario', 'Anon').upper()
    ts = st.session_state.tasa_actual
    st.markdown(f"""<div class="info-bar"><span>👤 <b>{vend}</b></span><span>💵 Tasa: <b>{ts} Bs/$</b></span></div>""", unsafe_allow_html=True)

with c_logout:
    if st.button("🔓", key="logout", help="Cerrar Sesión"):
        try:
            manager = get_manager()
            galletas = manager.get_all()
            if galletas and "agua_token_secure" in galletas:
                manager.delete("agua_token_secure")
        except Exception:
            pass
            
        keys_to_clear = ['auth_status', 'usuario', 'carrito', 'intentos_auth']
        for k in keys_to_clear:
            if k in st.session_state: del st.session_state[k]
        st.query_params.clear()
        time.sleep(0.5)
        st.rerun()

def agregar_producto(nombre):
    st.session_state.carrito[nombre] = st.session_state.carrito.get(nombre, 0) + 1
    st.toast(f"✅ {nombre}", icon="🛒")

# --- ACTUALIZAR TASA VISIBLE PARA TODOS ---
with st.expander("🔄 Cambiar Tasa del Día", expanded=False):
    nueva_tasa = st.number_input("Tasa Actual (Bs/$)", value=st.session_state.tasa_actual, step=0.1, key="global_tasa")
    if st.button("💾 Guardar Tasa"):
        try:
            ws_conf = libro_actual.worksheet("Configuracion")
            cell = ws_conf.find("TASA_DIA")
            if cell:
                ws_conf.update_cell(cell.row, cell.col + 1, nueva_tasa)
                st.cache_data.clear(); st.success("¡Tasa Actualizada!"); time.sleep(1); st.rerun()
            else:
                ws_conf.append_row(["TASA_DIA", nueva_tasa])
                st.cache_data.clear(); st.rerun()
        except Exception as e: st.error(f"Error: {e}")

color_st = "#D32F2F" if stock < 200 else "#0078D7"
st.markdown(f"""
<div style="padding:15px; background:linear-gradient(90deg, #f8f9fa 0%, #e9ecef 100%); border-radius:12px; margin-bottom:15px; margin-top:5px; border-left:5px solid {color_st}; display:flex; justify-content:space-between; align-items:center;">
    <div style="font-size:12px; color:#555; font-weight:bold;">TANQUE<br>DISPONIBLE</div>
    <div style="font-size:28px; font-weight:900; color:{color_st};">{stock:,.0f} L</div>
</div>
""", unsafe_allow_html=True)

# ---------------- PESTAÑAS ----------------
pestanas = ["🛒 VENDER", "📊 DIARIO", "🚛 CISTERNA", "📅 BALANCE"]
if st.session_state.get('usuario', '').lower() == "admin":
    pestanas.append("⚙️ ADMIN")

tabs = st.tabs(pestanas)

# ---------------- TAB 1: VENDER ----------------
with tabs[0]:
    if not productos_disponibles:
        st.warning("⚠️ No se encontraron productos.")
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
        
        es_combo_2x1 = False
        cant_20L = st.session_state.carrito.get("Botellón 20L", 0) + st.session_state.carrito.get("Recarga Botellón 20L", 0)
        if cant_20L == 2 and len(keys_carrito) == 1: es_combo_2x1 = True

        for p in keys_carrito:
            q = st.session_state.carrito[p]
            dat = productos_disponibles.get(p, {'precio':0, 'litros':0})
            sub = dat['precio'] * q
            total_bs += sub; total_l += dat['litros'] * q
            items_str.append(f"{q}x {p}")
            
            with st.container():
                c_izq, c_der = st.columns([4, 1], vertical_alignment="center")
                c_izq.markdown(f"<div class='prod-name'>{p.replace('Recarga','')}</div><div class='prod-details'>Cant: <b>{q}</b> | Total: <span class='prod-price'>Bs {sub:g}</span></div>", unsafe_allow_html=True)
                if c_der.button("🗑️", key=f"del_{p}"): del st.session_state.carrito[p]; st.rerun()

        st.markdown("---")
        metodo_seleccionado = st.radio("Método de Pago:", ["Pago Móvil", "Efectivo Bs", "Divisas ($)", "Punto de Venta", "Mixto"], horizontal=True)
        
        default_monto = float(total_bs)
        mostrar_vuelto = False
        if metodo_seleccionado == "Divisas ($)":
            default_monto = 0.0 
            if es_combo_2x1: default_monto = 1.0
            mostrar_vuelto = True
        
        with st.form("cobro_final"):
            if metodo_seleccionado != "Mixto":
                monto = st.number_input("Monto a Pagar", value=default_monto, step=1.0)
                ref = st.text_input("Referencia", max_chars=4)
                vuelto_bs = 0.0
                if mostrar_vuelto:
                    vuelto_bs = st.number_input("📤 Vuelto entregado (Bs)", min_value=0.0, step=1.0)
            else:
                st.info("Pago Dividido")
                c1, c2 = st.columns(2)
                with c1:
                    m1_metodo = st.selectbox("Método 1", ["Efectivo Bs", "Pago Móvil", "Divisas ($)", "Punto de Venta"])
                    m1_monto = st.number_input("Monto 1", value=0.0)
                    m1_ref = st.text_input("Ref 1", max_chars=4)
                with c2:
                    m2_metodo = st.selectbox("Método 2", ["Punto de Venta", "Divisas ($)", "Pago Móvil", "Efectivo Bs"])
                    m2_monto = st.number_input("Monto 2", value=0.0)
                    m2_ref = st.text_input("Ref 2", max_chars=4)
                vuelto_bs = 0.0

            if st.form_submit_button("✅ CONFIRMAR VENTA", use_container_width=True):
                try:
                    h_act = now_vzla().strftime("%H:%M:%S")
                    f_act = now_vzla().strftime("%Y-%m-%d")
                    vend = st.session_state.get('usuario', 'Admin')
                    ts = st.session_state.tasa_actual
                    items_txt = ", ".join(items_str)
                    
                    if metodo_seleccionado != "Mixto":
                        moneda = "USD" if "$" in metodo_seleccionado else "VES"
                        sheet_ventas.append_row([f_act, h_act, vend, items_txt, monto, moneda, ts, metodo_seleccionado, ref or "N/A", total_l, "Activa"])
                        if vuelto_bs > 0:
                            sheet_ventas.append_row([f_act, h_act, vend, f"Vuelto ({items_txt})", -vuelto_bs, "VES", ts, "Efectivo Bs", "Salida Caja", 0, "Activa"])
                    else:
                        mon1 = "USD" if "$" in m1_metodo else "VES"
                        sheet_ventas.append_row([f_act, h_act, vend, items_txt, m1_monto, mon1, ts, m1_metodo, m1_ref or "N/A", total_l, "Activa"])
                        if m2_monto > 0:
                            mon2 = "USD" if "$" in m2_metodo else "VES"
                            sheet_ventas.append_row([f_act, h_act, vend, "Complemento Mixto", m2_monto, mon2, ts, m2_metodo, m2_ref or "N/A", 0, "Activa"])

                    st.cache_data.clear(); st.success("Venta Exitosa"); limpiar_carrito(); time.sleep(1); st.rerun()
                except Exception as e:
                    if "Rerun" not in str(e): st.error(f"Error: {e}")

# ---------------- PREPARACIÓN DE DATOS GLOBALES ----------------
df_v = pd.DataFrame(d_ventas)
df_c = pd.DataFrame(d_cargas)

if not df_v.empty and 'Monto' in df_v.columns:
    df_v['Fecha'] = pd.to_datetime(df_v['Fecha'], errors='coerce').dt.date
    df_v['Monto'] = pd.to_numeric(df_v['Monto'], errors='coerce').fillna(0)

if not df_c.empty:
    if len(df_c.columns) >= 5:
        df_c.rename(columns={df_c.columns[2]: 'Litros', df_c.columns[3]: 'Costo_Bs', df_c.columns[4]: 'Concepto'}, inplace=True)
    df_c['Fecha'] = pd.to_datetime(df_c['Fecha'], errors='coerce').dt.date
    df_c['Litros'] = pd.to_numeric(df_c['Litros'], errors='coerce').fillna(0)
    df_c['Costo_Bs'] = pd.to_numeric(df_c['Costo_Bs'], errors='coerce').fillna(0)

# ---------------- TAB 2: DIARIO ----------------
with tabs[1]:
    if st.button("🔄 Actualizar", use_container_width=True): st.cache_data.clear(); st.rerun()
    fecha = st.date_input("Fecha", now_vzla())
    
    if not df_v.empty:
        dia = df_v[df_v['Fecha'] == fecha]
        if not dia.empty:
            def suma_cond(metodo_txt): 
                return dia[dia['Metodo_Pago'].astype(str).str.contains(metodo_txt, case=False, na=False)]['Monto'].sum()
            
            movil = suma_cond('Móvil|Movil')
            efectivo = suma_cond('Efectivo|Bs')
            punto = suma_cond('Punto')
            divisa = suma_cond('Divisa|\$')
            
            mask_bs_dia = ~dia['Metodo_Pago'].str.contains('Divisa|\$', case=False, na=False)
            total_bs_convertidos = dia.loc[mask_bs_dia, 'Monto'].sum() / st.session_state.tasa_actual
            gran_total_usd = divisa + total_bs_convertidos

            k1, k2, k3 = st.columns(3)
            k1.metric("Pago Móvil", f"Bs {movil:,.2f}")
            k2.metric("Efectivo Neto", f"Bs {efectivo:,.2f}")
            k3.metric("Divisas ($)", f"$ {divisa:,.2f}")
            
            st.markdown("---")
            c1, c2 = st.columns(2)
            c1.metric("Punto Venta", f"Bs {punto:,.2f}")
            c2.metric("💰 Ventas Netas del Día (Aprox $)", f"$ {gran_total_usd:,.2f}")
            
            st.dataframe(dia[['Hora','Vendedor','Detalles_Compra','Monto','Moneda','Metodo_Pago']], hide_index=True, use_container_width=True)
        else: st.info("Sin ventas hoy.")

# ---------------- TAB 3: CISTERNA ----------------
with tabs[2]:
    st.markdown("### 🚛 Carga de Agua (Cisterna)")
    with st.form("cisterna"):
        c1, c2 = st.columns(2)
        f = c1.date_input("Día", now_vzla()); h = c2.time_input("Hora", now_vzla())
        l = st.number_input("Litros de la Cisterna", 2000, step=100)
        costo_bs = st.number_input("Costo Pagado (Bs)", min_value=0.0, step=1.0)
        n = st.text_input("Chofer / Proveedor")
        
        if st.form_submit_button("GUARDAR CARGA", use_container_width=True):
            if sheet_cargas is not None:
                try: 
                    sheet_cargas.append_row([str(f), str(h), l, costo_bs, n])
                    st.cache_data.clear(); st.success("Cisterna Registrada"); time.sleep(1); st.rerun()
                except Exception as e: st.error(f"Error: {e}")

    st.divider()
    if not df_c.empty:
        mask_no_cisterna = df_c['Concepto'].astype(str).str.contains('GASTO/NÓMINA|DEPÓSITO', case=False, na=False)
        df_cisternas = df_c[~mask_no_cisterna]
        
        if not df_cisternas.empty:
            df_mostrar = df_cisternas.sort_values(by=['Fecha'], ascending=False).copy()
            st.dataframe(df_mostrar[['Fecha', 'Litros', 'Costo_Bs', 'Concepto']], hide_index=True, use_container_width=True)

# ---------------- TAB 4: BALANCE ----------------
with tabs[3]:
    st.markdown("### 📅 Balance de Rendimiento")
    
    fechas = st.date_input("Selecciona el rango a analizar", 
                           [now_vzla().date() - timedelta(days=7), now_vzla().date()], 
                           max_value=now_vzla().date())
    
    if len(fechas) == 2:
        f_inicio, f_fin = fechas
        tasa_hoy = st.session_state.tasa_actual
        
        ventas_rango_usd = 0.0
        if not df_v.empty:
            df_v_rango = df_v[(df_v['Fecha'] >= f_inicio) & (df_v['Fecha'] <= f_fin)]
            if not df_v_rango.empty:
                divisa_usd = df_v_rango[df_v_rango['Metodo_Pago'].astype(str).str.contains('Divisa|\$', case=False, na=False)]['Monto'].sum()
                bs_neto = df_v_rango[~df_v_rango['Metodo_Pago'].astype(str).str.contains('Divisa|\$', case=False, na=False)]['Monto'].sum()
                ventas_rango_usd = divisa_usd + (bs_neto / tasa_hoy)
        
        cist_rango_usd = 0.0
        suel_rango_usd = 0.0
        
        if not df_c.empty:
            df_c_rango = df_c[(df_c['Fecha'] >= f_inicio) & (df_c['Fecha'] <= f_fin)]
            if not df_c_rango.empty:
                mask_gastos = df_c_rango['Concepto'].astype(str).str.contains('GASTO/NÓMINA', case=False, na=False)
                mask_depositos = df_c_rango['Concepto'].astype(str).str.contains('DEPÓSITO', case=False, na=False)
                mask_cisternas = ~(mask_gastos | mask_depositos)
                
                cist_rango_usd = df_c_rango[mask_cisternas]['Costo_Bs'].sum() / tasa_hoy
                suel_rango_usd = df_c_rango[mask_gastos]['Costo_Bs'].sum() / tasa_hoy

        utilidad_rango = ventas_rango_usd - cist_rango_usd - suel_rango_usd

        st.markdown(f"<div style='background-color: #f8f9fa; border-left: 5px solid #0078D7; padding: 15px; border-radius: 10px; margin-bottom: 20px;'><h4>📊 Ganancia del Período ({f_inicio.strftime('%d/%m')} - {f_fin.strftime('%d/%m')})</h4></div>", unsafe_allow_html=True)
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Ingreso Neto (+)", f"$ {ventas_rango_usd:,.2f}", help="Ventas menos Vueltos")
        c2.metric("Cisternas (-)", f"$ {cist_rango_usd:,.2f}")
        c3.metric("Sueldos/Admin (-)", f"$ {suel_rango_usd:,.2f}")
        c4.metric("UTILIDAD NETA", f"$ {utilidad_rango:,.2f}", delta="A Favor" if utilidad_rango>=0 else "En Contra", delta_color="normal" if utilidad_rango>=0 else "inverse")

        st.divider()
        st.caption("📦 Productos Vendidos en este rango")
        if not df_v.empty and not df_v_rango.empty:
            conteo = {}
            for item in df_v_rango['Detalles_Compra']:
                for i in str(item).split(", "):
                    if "x " in i and "Vuelto" not in i:
                        try: q, n = i.split("x ", 1); conteo[n.strip()] = conteo.get(n.strip(), 0) + int(q)
                        except: pass
            for p, c in conteo.items(): st.write(f"**{p}:** {c}")
    else:
        st.warning("Selecciona una fecha de inicio y una fecha de fin en el calendario de arriba.")

# ---------------- TAB 5: ADMIN MENU ----------------
if len(tabs) == 5:
    with tabs[4]:
        st.header("⚙️ Centro de Control (Gerencia)")
        
        admin_tabs = st.tabs(["🏦 Caja General", "💸 Pagar Nómina", "🏧 Depósitos", "📈 Mapa de Calor"])
        
        # --- SUB TAB 1: CAJA ---
        with admin_tabs[0]:
            caja_total_usd = 0.0
            if not df_v.empty:
                divisa_tot = df_v[df_v['Metodo_Pago'].astype(str).str.contains('Divisa|\$', case=False, na=False)]['Monto'].sum()
                bs_tot_ingresos = df_v[~df_v['Metodo_Pago'].astype(str).str.contains('Divisa|\$', case=False, na=False)]['Monto'].sum()
                
                bs_tot_egresos = 0.0
                if not df_c.empty:
                    mask_dep_tot = df_c['Concepto'].astype(str).str.contains('DEPÓSITO', case=False, na=False)
                    bs_tot_egresos = df_c[~mask_dep_tot]['Costo_Bs'].sum()
                
                caja_total_usd = divisa_tot + ((bs_tot_ingresos - bs_tot_egresos) / st.session_state.tasa_actual)
                
            st.markdown(f"<div style='background-color: #e6f7ff; border: 2px solid #0078D7; padding: 15px; border-radius: 10px; text-align: center; margin-bottom: 20px;'><h3>🏦 CAJA TOTAL HISTÓRICA: $ {caja_total_usd:,.2f}</h3><p style='margin:0; color:#555;'>Ganancia acumulada desde el inicio de operaciones.</p></div>", unsafe_allow_html=True)

        # --- SUB TAB 2: EGRESOS Y SUELDOS ---
        with admin_tabs[1]:
            st.subheader("💸 Pagar Nómina o Gasto Variable")
            st.caption("Esto restará dinero de tu Caja Histórica y bajará tu rentabilidad.")
            with st.form("form_sueldos"):
                c1, c2, c3 = st.columns([2, 1, 1])
                concepto = c1.text_input("Concepto (Ej: Sueldo Yanelis)", max_chars=50)
                moneda_gasto = c2.selectbox("Moneda Usada", ["Divisas ($)", "Bolívares (Bs)"])
                monto_gasto = c3.number_input("Monto Numérico", min_value=0.0, step=1.0)
                
                if st.form_submit_button("REGISTRAR GASTO", use_container_width=True):
                    if monto_gasto > 0 and concepto:
                        try:
                            h_act = now_vzla().strftime("%H:%M:%S")
                            f_act = now_vzla().strftime("%Y-%m-%d")
                            monto_guardar_bs = monto_gasto * st.session_state.tasa_actual if "Divisas" in moneda_gasto else monto_gasto
                            if sheet_cargas is not None:
                                sheet_cargas.append_row([str(f_act), str(h_act), 0, monto_guardar_bs, f"GASTO/NÓMINA: {concepto}"])
                                st.cache_data.clear(); st.success(f"Gasto guardado."); time.sleep(1); st.rerun()
                        except Exception as e: st.error(f"Error: {e}")
                    else: st.warning("Completa el concepto y el monto.")

        # --- SUB TAB 3: DEPÓSITOS BANCARIOS ---
        with admin_tabs[2]:
            st.subheader("🏧 Mover Efectivo a la Cuenta")
            st.info("💡 Registra aquí el efectivo físico que depositas en tu cuenta. Esto deja constancia del movimiento sin restar tu Ganancia Total.")
            with st.form("form_deposito"):
                c1, c2 = st.columns(2)
                tipo_entrada = c1.selectbox("Tipo de Movimiento", ["Depósito en Cuenta", "Transferencia de Efectivo", "Otro"])
                ref_dep = c2.text_input("Referencia o Nota (Opcional)")
                
                c3, c4 = st.columns(2)
                moneda_dep = c3.selectbox("Moneda Física", ["Efectivo Bs", "Divisas ($)"])
                monto_dep = c4.number_input("Monto Depositado", min_value=0.0, step=1.0)
                
                if st.form_submit_button("REGISTRAR MOVIMIENTO", use_container_width=True):
                    if monto_dep > 0:
                        try:
                            h_act = now_vzla().strftime("%H:%M:%S")
                            f_act = now_vzla().strftime("%Y-%m-%d")
                            monto_guardar_bs = monto_dep * st.session_state.tasa_actual if "Divisas" in moneda_dep else monto_dep
                            
                            if sheet_cargas is not None:
                                sheet_cargas.append_row([str(f_act), str(h_act), 0, monto_guardar_bs, f"DEPÓSITO: {tipo_entrada} (Ref: {ref_dep})"])
                                st.cache_data.clear(); st.success(f"Movimiento guardado."); time.sleep(1); st.rerun()
                        except Exception as e: st.error(f"Error: {e}")
                    else: st.warning("Coloca un monto mayor a 0.")

        # --- SUB TAB 4: MAPA DE CALOR (INTERACTIVO) ---
        with admin_tabs[3]:
            st.subheader("📈 Horario Comercial de Ventas")
            
            opcion_filtro = st.radio("Selecciona los datos a analizar:", ["Historial Completo", "Por Rango de Fechas"], horizontal=True)
            
            if opcion_filtro == "Por Rango de Fechas":
                fechas_hm = st.date_input("Rango para el Mapa de Calor", 
                                       [now_vzla().date() - timedelta(days=7), now_vzla().date()], 
                                       max_value=now_vzla().date(), key="hm_dates")
            else:
                fechas_hm = None
            
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
                            
                            fig = px.imshow(
                                hm_pivot, 
                                labels=dict(x="Hora del Día", y="Día de la Semana", color="Cantidad de Ventas"),
                                x=horas_str, 
                                y=dias_orden, 
                                aspect="auto", 
                                text_auto=True, 
                                color_continuous_scale="Blues"
                            )
                            fig.update_xaxes(side="top")
                            st.plotly_chart(fig, use_container_width=True)
                            if opcion_filtro == "Historial Completo":
                                st.info("💡 Este mapa te muestra el volumen histórico de ventas en todas las fechas registradas.")
                            else:
                                st.info(f"💡 Mapa mostrando las ventas del **{fechas_hm[0].strftime('%d/%m')} al {fechas_hm[1].strftime('%d/%m')}**.")
                        else: st.warning("No hay ventas entre las 9 AM y 9 PM para el rango seleccionado.")
                    else: st.warning("Aún no hay ventas válidas registradas en este rango.")
                else: st.warning("No se encontraron ventas para las fechas seleccionadas.")
            else: st.info("Faltan datos para generar el gráfico.")
