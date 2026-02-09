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

st.markdown("""
<style>
    footer {visibility: hidden;}
    header {visibility: visible;}
    .block-container { max-width: 800px; margin: auto; padding-top: 2rem !important; }
    [data-testid="column"] { min-width: 10px !important; padding: 0 2px !important; }
    
    /* Tarjetas y Forms */
    [data-testid="stForm"], div.stContainer { 
        background-color: white; 
        border: 1px solid #e0e0e0; 
        border-radius: 12px; 
        padding: 10px !important; 
        box-shadow: 0 2px 4px rgba(0,0,0,0.05); 
        margin-bottom: 8px; 
    }
    
    /* Botones */
    [data-testid="stForm"] button { background-color: #0078D7 !important; color: white !important; border: none !important; border-radius: 8px !important; font-weight: 800 !important; height: 50px !important; font-size: 16px !important; }
    [data-testid="stForm"] button:active { background-color: #005a9e !important; transform: scale(0.98); }
    
    /* Botón Borrar */
    div.stButton > button { border-radius: 8px !important; border: 1px solid #ff4b4b !important; color: #ff4b4b !important; background-color: transparent !important; height: 40px !important; }
    
    /* Inputs y Textos */
    .prod-name { font-weight: 700; font-size: 15px; color: #333; }
    .prod-price { font-weight: 800; font-size: 15px; color: #0078D7; }
    div[data-testid="stNumberInput"] input { font-size: 22px; font-weight: bold; text-align: center; }
    
    /* Tasa y Usuario */
    .info-bar { font-size: 12px; color: #666; background: #f0f2f6; padding: 5px 10px; border-radius: 5px; display: flex; justify-content: space-between; margin-bottom: 10px; }
</style>
""", unsafe_allow_html=True)

def now_vzla(): return datetime.utcnow() - timedelta(hours=4)

# --- 2. SISTEMA DE SEGURIDAD ---
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
    token_cookie = cookies.get("agua_token_secure")
    if token_cookie:
        try:
            tokens_validos = st.secrets["tokens"]
            if token_cookie in tokens_validos or token_cookie == "admin_manual":
                st.session_state['auth_status'] = True
                st.session_state['usuario'] = "Admin" if token_cookie == "admin_manual" else token_cookie
                return True
        except: pass

    c1, c2, c3 = st.columns([1,2,1])
    if os.path.exists("logo.png"): 
        with c2: 
            st.image("logo.png", use_container_width=True)

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

# ========================================================
# 🚀 APLICACIÓN
# ========================================================

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
    ent = pd.DataFrame(c)['Litros'].sum() if c else 0
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

st.session_state.tasa_actual = tasa_global_db

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
        # CORRECCIÓN LOGOUT: Limpieza profunda
        try: get_manager().delete("agua_token_secure")
        except: pass
        
        # Limpiar variables de sesión críticas
        keys_to_clear = ['auth_status', 'usuario', 'carrito']
        for k in keys_to_clear:
            if k in st.session_state: del st.session_state[k]
            
        # Limpiar URL para evitar re-login automático
        st.query_params.clear()
        time.sleep(0.5) 
        st.rerun()

# --- ACTUALIZAR TASA ---
with st.expander("⚙️ Cambiar Tasa Global"):
    nueva_tasa = st.number_input("Nueva Tasa BCV/Paralelo", value=st.session_state.tasa_actual, step=0.1)
    if st.button("💾 Guardar Nueva Tasa"):
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

# --- RESTO DE LA APP ---
def agregar_producto(nombre):
    st.session_state.carrito[nombre] = st.session_state.carrito.get(nombre, 0) + 1
    st.toast(f"✅ {nombre}", icon="🛒")

def limpiar_carrito(): st.session_state.carrito = {}

color_st = "#D32F2F" if stock < 200 else "#0078D7"
st.markdown(f"""
<div style="padding:15px; background:linear-gradient(90deg, #f8f9fa 0%, #e9ecef 100%); border-radius:12px; margin-bottom:15px; margin-top:5px; border-left:5px solid {color_st}; display:flex; justify-content:space-between; align-items:center;">
    <div style="font-size:12px; color:#555; font-weight:bold;">TANQUE<br>DISPONIBLE</div>
    <div style="font-size:28px; font-weight:900; color:{color_st};">{stock:,.0f} L</div>
</div>
""", unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs(["🛒 VENDER", "📊 DIARIO", "🚛 CISTERNA", "📅 SEMANAL"])

# ---------------- TAB 1: VENDER ----------------
with tab1:
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

# ---------------- TAB 2: DIARIO ----------------
with tab2:
    if st.button("🔄 Actualizar", use_container_width=True): st.cache_data.clear(); st.rerun()
    fecha = st.date_input("Fecha", now_vzla())
    df = pd.DataFrame(d_ventas)
    
    if not df.empty and len(df.columns) >= 11:
        df['Fecha'] = pd.to_datetime(df['Fecha']).dt.date
        df['Monto'] = pd.to_numeric(df['Monto'], errors='coerce').fillna(0)
        df['Tasa_Cambio'] = pd.to_numeric(df['Tasa_Cambio'], errors='coerce').fillna(1)
        
        dia = df[df['Fecha'] == fecha]
        if not dia.empty:
            def suma_cond(metodo_txt): 
                return dia[dia['Metodo_Pago'].astype(str).str.contains(metodo_txt, case=False, na=False)]['Monto'].sum()
            
            movil = suma_cond('Móvil|Movil')
            efectivo = suma_cond('Efectivo|Bs')
            punto = suma_cond('Punto')
            divisa = suma_cond('Divisa|\$')
            
            mask_bs = ~dia['Metodo_Pago'].str.contains('Divisa|\$', case=False, na=False)
            total_bs_convertidos = (dia.loc[mask_bs, 'Monto'] / dia.loc[mask_bs, 'Tasa_Cambio'].replace(0, 1)).sum()
            gran_total_usd = divisa + total_bs_convertidos

            k1, k2, k3 = st.columns(3)
            k1.metric("Pago Móvil", f"Bs {movil:,.2f}")
            k2.metric("Efectivo (Caja)", f"Bs {efectivo:,.2f}")
            k3.metric("Divisas ($)", f"$ {divisa:,.2f}")
            
            st.markdown("---")
            c1, c2 = st.columns(2)
            c1.metric("Punto Venta", f"Bs {punto:,.2f}")
            c2.metric("💰 Total Día (Aprox $)", f"$ {gran_total_usd:,.2f}", help="Suma de Divisas + (Bs / Tasa Registrada)")
            
            st.dataframe(dia[['Hora','Vendedor','Detalles_Compra','Monto','Moneda','Metodo_Pago']], hide_index=True, use_container_width=True)
        else: st.info("Sin ventas hoy.")

# ---------------- TAB 3: CISTERNA ----------------
with tab3:
    st.markdown("### 🚛 Carga de Agua")
    with st.form("cisterna"):
        c1, c2 = st.columns(2)
        f = c1.date_input("Día", now_vzla()); h = c2.time_input("Hora", now_vzla())
        l = st.number_input("Litros", 2000, step=100)
        costo_bs = st.number_input("Costo Pagado (Bs)", min_value=0.0, step=1.0)
        n = st.text_input("Chofer")
        
        if st.form_submit_button("GUARDAR", use_container_width=True):
            if sheet_cargas:
                try: sheet_cargas.append_row([str(f), str(h), l, costo_bs, n]); st.cache_data.clear(); st.success("Registrado"); time.sleep(1); st.rerun()
                except Exception as e: st.error(f"Error: {e}")

    st.divider()
    df_c = pd.DataFrame(d_cargas)
    if not df_c.empty:
        try:
            if len(df_c.columns) >= 4:
                df_c.rename(columns={df_c.columns[3]: 'Costo_Bs'}, inplace=True)
            df_c['Fecha'] = pd.to_datetime(df_c['Fecha'])
            df_c = df_c.sort_values(by=['Fecha', 'Hora'], ascending=False)
            df_c['Fecha'] = df_c['Fecha'].dt.date
            st.dataframe(df_c, hide_index=True, use_container_width=True)
        except: st.dataframe(df_c)

# ---------------- TAB 4: SEMANAL ----------------
with tab4:
    st.markdown("### 📅 Balance Semanal")
    fecha_ref = st.date_input("Referencia", now_vzla())
    inicio = fecha_ref - timedelta(days=fecha_ref.weekday())
    fin = inicio + timedelta(days=6)
    st.info(f"Semana: {inicio.strftime('%d/%m')} al {fin.strftime('%d/%m')}")
    
    df_v = pd.DataFrame(d_ventas)
    df_c = pd.DataFrame(d_cargas)
    
    if not df_v.empty and 'Monto' in df_v.columns:
        df_v['Fecha'] = pd.to_datetime(df_v['Fecha']).dt.date
        df_v['Monto'] = pd.to_numeric(df_v['Monto'], errors='coerce').fillna(0)
        mask = (df_v['Fecha'] >= inicio) & (df_v['Fecha'] <= fin)
        df_sem = df_v.loc[mask]

        if not df_sem.empty:
            # CORRECCIÓN REPORTES: Desglose por Método detallado
            def sum_m(txt): return df_sem[df_sem['Metodo_Pago'].astype(str).str.contains(txt, case=False, na=False)]['Monto'].sum()
            divisa = sum_m('Divisa|\$')
            movil = sum_m('Móvil|Movil')
            efectivo = sum_m('Efectivo|Bs')
            punto = sum_m('Punto')
            
            # Cálculo de Utilidad
            bs_totales = movil + efectivo + punto
            ingreso_usd = divisa + (bs_totales / st.session_state.tasa_actual)
            
            gasto_cisterna_usd = 0.0
            if not df_c.empty and len(df_c.columns) >= 4:
                df_c['Fecha'] = pd.to_datetime(df_c['Fecha']).dt.date
                mask_c = (df_c['Fecha'] >= inicio) & (df_c['Fecha'] <= fin)
                df_c_sem = df_c.loc[mask_c]
                costo_bs_total = pd.to_numeric(df_c_sem.iloc[:, 3], errors='coerce').sum()
                gasto_cisterna_usd = costo_bs_total / st.session_state.tasa_actual
            
            utilidad = ingreso_usd - gasto_cisterna_usd
            color_utilidad = "normal" if utilidad >= 0 else "inverse"

            # --- NUEVA VISUALIZACIÓN DE DESGLOSE ---
            st.subheader("💵 Desglose por Método")
            k1, k2, k3, k4 = st.columns(4)
            k1.metric("Móvil", f"Bs {movil:,.2f}")
            k2.metric("Efectivo", f"Bs {efectivo:,.2f}")
            k3.metric("Punto", f"Bs {punto:,.2f}")
            k4.metric("Divisa", f"$ {divisa:,.2f}")
            
            st.divider()
            
            # --- RESUMEN FINANCIERO NETO ---
            c1, c2, c3 = st.columns(3)
            c1.metric("Ingresos Ventas", f"$ {ingreso_usd:,.2f}")
            c2.metric("Gastos Cisterna", f"$ {gasto_cisterna_usd:,.2f}", delta="-Gastos", delta_color="inverse")
            c3.metric("UTILIDAD NETA", f"$ {utilidad:,.2f}", delta="Ganancia" if utilidad>0 else "Pérdida", delta_color=color_utilidad)
            
            st.divider()
            st.caption("📦 Productos")
            conteo = {}
            for item in df_sem['Detalles_Compra']:
                for i in str(item).split(", "):
                    if "x " in i and "Vuelto" not in i:
                        try: q, n = i.split("x ", 1); conteo[n.strip()] = conteo.get(n.strip(), 0) + int(q)
                        except: pass
            for p, c in conteo.items(): st.write(f"**{p}:** {c}")
            
        else: st.warning("Sin ventas esta semana.")
