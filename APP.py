def check_auth():
    if st.session_state.get('auth_status', False): return True
    cookie_manager = get_manager()
    
    # --- 1. LECTOR DE ENLACES (ESTO FALTABA) ---
    # Revisa si el link trae ?token=yanelis o ?u=yanelis
    if "token" in st.query_params or "u" in st.query_params:
        url_token = st.query_params.get("token", st.query_params.get("u", ""))
        try:
            if url_token in st.secrets["tokens"]:
                st.session_state['auth_status'] = True
                st.session_state['usuario'] = url_token
                # Guarda la sesión en el teléfono por 30 días
                cookie_manager.set("agua_token_secure", url_token, expires_at=now_vzla() + timedelta(days=30))
                st.query_params.clear() # Limpia el link por seguridad
                time.sleep(0.5)
                st.rerun()
                return True
        except: pass
    # -------------------------------------------

    # --- 2. LECTOR DE COOKIES (Si ya había entrado antes) ---
    cookies = cookie_manager.get_all()
    if not cookies and 'intentos_auth' not in st.session_state:
        st.session_state['intentos_auth'] = 1
        with st.spinner("Conectando..."): time.sleep(0.5)
        st.rerun()
        
    if cookies and "agua_token_secure" in cookies:
        tk = cookies.get("agua_token_secure")
        try:
            if tk in st.secrets["tokens"] or tk == "admin_manual":
                st.session_state['auth_status'] = True
                st.session_state['usuario'] = "Admin" if tk == "admin_manual" else tk
                return True
        except: pass

    # --- 3. FORMULARIO MANUAL (Para ti como Admin) ---
    c1, c2, c3 = st.columns([1,2,1])
    try:
        l_path = os.path.join(CARPETA_LOCAL, "logo.png")
        if os.path.exists(l_path): 
            with c2: st.image(l_path, use_container_width=True)
    except: pass
    
    st.markdown("### 🔒 Acceso")
    with st.form("login_manual"):
        password = st.text_input("Clave Maestra", type="password")
        if st.form_submit_button("Entrar", use_container_width=True):
            try:
                if password == st.secrets["passwords"]["main"]:
                    st.session_state['auth_status'] = True
                    st.session_state['usuario'] = "Admin"
                    cookie_manager.set("agua_token_secure", "admin_manual", expires_at=now_vzla() + timedelta(days=1))
                    st.rerun()
                else: st.error("Incorrecto")
            except Exception as e:
                st.error("Error leyendo secretos de Streamlit.")
    return False
