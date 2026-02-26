<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <meta http-equiv="Content-Security-Policy" content="default-src 'self' https://*.google.com https://*.googleusercontent.com https://cdn.jsdelivr.net 'unsafe-inline' data:;">
    <title>WellnessTech | Psicología en Venezuela</title>
    
    <link href="https://cdn.jsdelivr.net/npm/@sweetalert2/theme-material-ui/material-ui.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/sweetalert2@11"></script>

    <style>
        * { box-sizing: border-box; } 
        :root { --midnight: #1A2B3C; --sky: #A3D8F4; --sand: #F5F5DC; --white: #FFFFFF; --green: #27ae60; --gold: #f1c40f; --error: #e74c3c; --multi: #B39DDB; }
        body { font-family: 'Segoe UI', sans-serif; margin: 0; background-color: var(--white); color: var(--midnight); overflow-x: hidden; }
        nav { background: var(--white); padding: 15px 5%; display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid var(--sand); position: sticky; top:0; z-index: 1000; }
        .logo { font-weight: bold; font-size: 1.5rem; cursor: pointer; }
        .hero { background: linear-gradient(135deg, var(--white) 0%, var(--sand) 100%); padding: 60px 5% 120px 5%; text-align: center; }
        .hero h1 { font-size: 2.5rem; margin-bottom: 10px; }
        
        .buscador-container { position: relative; max-width: 1000px; margin: 30px auto; text-align: center; padding: 0 10px; }
        .btn-menu-filtros { display: none; background: var(--midnight); color: white; font-size: 1rem; font-weight: bold; padding: 12px 25px; border-radius: 30px; border: none; cursor: pointer; margin: 0 auto 15px auto; transition: 0.3s; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }
        .buscador-flotante { background: white; padding: 20px; border-radius: 40px; box-shadow: 0 15px 35px rgba(0,0,0,0.1); display: inline-flex; gap: 10px; flex-wrap: wrap; justify-content: center; align-items: center; border: 1px solid #eee; transition: all 0.4s ease; }
        .input-filtro, .select-filtro { padding: 12px 20px; border-radius: 25px; border: 1px solid #ddd; font-size: 0.95rem; outline: none; background-color: #fcfcfc; }
        .input-filtro { width: 180px; } .select-filtro { width: 150px; cursor: pointer; }
        .btn-geo { background-color: var(--sky); border: none; padding: 12px 15px; border-radius: 50%; cursor: pointer; transition: 0.2s; font-size: 1.2rem; }
        .btn-geo-mobile { display: none; width: 100%; background: var(--sky); border: none; padding: 12px; border-radius: 25px; cursor: pointer; font-weight: bold; color: var(--midnight); margin-top: 10px; }
        
        .directorio { padding: 50px 5%; display: flex; flex-wrap: wrap; justify-content: center; gap: 25px; min-height: 300px; }
        .card { width: 100%; max-width: 300px; background: white; border-radius: 15px; border: 1px solid #eee; box-shadow: 0 10px 20px rgba(0,0,0,0.05); overflow: hidden; transition: 0.3s; cursor: pointer; animation: fadeIn 0.8s ease; display: flex; flex-direction: column; height: 480px; }
        .card:hover { transform: translateY(-5px); box-shadow: 0 15px 30px rgba(0,0,0,0.1); }
        .photo { height: 180px; display: flex; align-items: center; justify-content: center; font-size: 4rem; overflow: hidden; position: relative; flex-shrink: 0; }
        .photo img { width: 100%; height: 100%; object-fit: cover; transition: 0.5s; }
        .card:hover .photo img { transform: scale(1.05); } 
        .info { padding: 20px; flex-grow: 1; display: flex; flex-direction: column; }
        .tags-container { display: flex; gap: 5px; margin-bottom: 10px; flex-wrap: wrap; }
        .tag { font-size: 0.7rem; padding: 3px 8px; border-radius: 10px; background: #f0f0f0; color: #555; }
        .tag.online { background: #e3f2fd; color: #1565c0; } 
        
        .tag-vip { background: var(--gold); color: var(--midnight); font-weight: bold; box-shadow: 0 2px 5px rgba(241,196,15,0.4); }

        .fpv { color: var(--green); font-weight: bold; font-size: 0.8rem; display: block; margin-bottom: 5px; }
        .estrellas-card { color: var(--gold); font-size: 0.9rem; margin-bottom: 5px; } 
        .btn-contact { width: 100%; background: var(--midnight); color: white; border: none; padding: 10px; border-radius: 5px; margin-top: auto; cursor: pointer; transition: 0.2s; }
        .btn-contact:hover { background: #2c435a; }

        .btn-mostrar-mas { background-color: var(--sky); color: var(--midnight); border: 2px solid var(--midnight); padding: 12px 30px; border-radius: 25px; font-size: 1rem; font-weight: bold; cursor: pointer; transition: 0.3s; margin-top: 10px; }
        .btn-mostrar-mas:hover { background-color: var(--midnight); color: white; }

        #vistaProfesional { display: none; padding: 50px 5%; background-color: var(--sand); min-height: 80vh; }
        .registro-container { max-width: 750px; margin: 0 auto; background: white; padding: 40px; border-radius: 20px; box-shadow: 0 20px 40px rgba(0,0,0,0.1); }
        .registro-header { text-align: center; margin-bottom: 30px; }
        .form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; } 
        .form-full { grid-column: span 2; }
        .form-group label { display: block; font-weight: bold; margin-bottom: 8px; font-size: 0.9rem; color: var(--midnight); }
        .form-group input, .form-group select, .form-group textarea { width: 100%; padding: 12px; border: 1px solid #ddd; border-radius: 10px; font-size: 1rem; background: #fcfcfc; }
        .tags-grid { display: flex; flex-wrap: wrap; gap: 8px; }
        .tag-checkbox { position: relative; cursor: pointer; }
        .tag-checkbox input { position: absolute; opacity: 0; cursor: pointer; }
        .tag-label { display: inline-block; padding: 8px 16px; background: #f0f2f5; border-radius: 25px; font-size: 0.9rem; color: #555; transition: 0.2s; user-select: none; }
        .tag-checkbox input:checked + .tag-label { background: var(--midnight); color: white; transform: scale(1.05); }
        .schedule-compact { display: grid; grid-template-columns: repeat(auto-fit, minmax(70px, 1fr)); gap: 5px; margin-top: 5px; }
        .day-column { text-align: center; background: #fcfcfc; border: 1px solid #eee; border-radius: 10px; padding: 10px 5px; }
        .day-name { font-weight: bold; font-size: 0.85rem; margin-bottom: 10px; }
        .shift-toggles { display: flex; flex-direction: column; gap: 8px; align-items: center; }
        .shift-checkbox { position: relative; cursor: pointer; width: 100%; display: flex; justify-content: center; }
        .shift-checkbox input { position: absolute; opacity: 0; cursor: pointer; }
        .shift-text { display: inline-block; padding: 6px 15px; background: #eee; border-radius: 8px; font-size: 0.9rem; color: #888; transition: 0.2s; user-select: none; }
        .shift-checkbox input:checked + .shift-text { background: var(--sky); color: var(--midnight); font-weight: bold; transform: scale(1.1); box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        .btn-registro { width: 100%; background-color: var(--midnight); color: white; padding: 15px; border: none; border-radius: 10px; font-size: 1.1rem; font-weight: bold; cursor: pointer; margin-top: 25px; transition: 0.3s; }
        
        .seccion-seguridad { background: #fff3cd; border: 1px solid #ffeeba; border-radius: 10px; padding: 15px; margin-top: 20px; text-align: center; }

        .modal-overlay { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.7); z-index: 2000; align-items: center; justify-content: center; backdrop-filter: blur(4px); opacity: 0; transition: opacity 0.3s ease; overflow-y: auto; padding: 20px; }
        .modal-overlay.active { opacity: 1; }
        
        .modal-perfil-card { background: white; width: 90%; max-width: 800px; border-radius: 20px; overflow: hidden; display: flex; box-shadow: 0 25px 50px rgba(0,0,0,0.3); max-height: 90vh; flex-direction: row; transform: translateY(20px); transition: transform 0.3s ease; }
        .modal-overlay.active .modal-perfil-card { transform: translateY(0); }
        .perfil-sidebar { background: #f8f9fa; padding: 40px 30px; width: 35%; text-align: center; border-right: 1px solid #eee; display: flex; flex-direction: column; align-items: center; flex-shrink: 0; }
        .perfil-foto-grande { width: 120px; height: 120px; background: var(--sky); border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 3rem; margin-bottom: 20px; overflow: hidden; border: 4px solid white; box-shadow: 0 5px 15px rgba(0,0,0,0.1); }
        .perfil-foto-grande img { width: 100%; height: 100%; object-fit: cover; }
        .perfil-precio-box { background: white; padding: 15px; border-radius: 12px; margin-top: 20px; border: 1px solid #eee; width: 80%; }
        .monto-precio { font-size: 1.4rem; font-weight: bold; color: var(--green); }
        .perfil-content { padding: 40px; width: 65%; text-align: left; overflow-y: auto; position: relative; }
        
        .perfil-nombre { font-size: 2rem; margin: 0 0 5px 0; color: var(--midnight); line-height: 1.2; }
        .perfil-titulo-destacado { color: #555; font-size: 1.1rem; font-weight: 600; margin-bottom: 5px; display: block; }
        .perfil-fpv { display: inline-block; background: #eee; padding: 4px 10px; border-radius: 15px; font-size: 0.85rem; color: #666; margin-bottom: 10px; }
        .perfil-rating { font-size: 1rem; color: var(--gold); margin-bottom: 20px; display: block; } 
        
        .seccion-titulo { font-size: 0.85rem; font-weight: bold; text-transform: uppercase; color: var(--midnight); border-bottom: 2px solid var(--sky); display: inline-block; margin-bottom: 15px; letter-spacing: 1px; }
        .badge-disponibilidad { margin-top: 15px; background: #e3f2fd; color: #1565c0; padding: 8px; border-radius: 8px; font-size: 0.85rem; display: inline-block; font-weight: bold; text-align: center;}
        .badge-turno { margin-top: 5px; background: #f9f9f9; color: #555; padding: 5px 10px; border-radius: 15px; font-size: 0.8rem; display: inline-block; border: 1px solid #eee; }
        
        .botones-perfil-container { display: flex; gap: 10px; margin-top: 30px; }
        .btn-agendar { background: var(--green); color: white; width: 100%; padding: 15px; border: none; border-radius: 10px; font-size: 1.1rem; font-weight: bold; cursor: pointer; transition: 0.3s; }
        .btn-calificar { background: white; color: var(--midnight); border: 2px solid var(--midnight); width: 40%; padding: 15px; border-radius: 10px; font-size: 1rem; font-weight: bold; cursor: pointer; transition: 0.3s; }
        .btn-agendar:hover { background: #219653; } .btn-calificar:hover { background: #f0f0f0; }

        .modal-pequeno .modal-content { background: white; padding: 30px; border-radius: 15px; width: 90%; max-width: 350px; text-align: center; position:relative; transform: scale(0.9); transition: transform 0.3s ease; }
        .modal-overlay.active .modal-content { transform: scale(1); }
        .modal-pequeno input, .modal-pequeno textarea { width: 100%; padding: 12px; margin: 10px 0; border: 1px solid #ddd; border-radius: 8px; box-sizing: border-box; font-size: 1rem; }
        
        .star-rating-interactivo { display: flex; justify-content: center; gap: 10px; margin: 15px 0; font-size: 2.8rem; color: #e0e0e0; cursor: pointer; user-select: none; }
        .star-rating-interactivo .star { transition: transform 0.2s, color 0.2s; }
        .star-rating-interactivo .star.active { color: var(--gold); text-shadow: 0 0 10px rgba(241, 196, 15, 0.4); }
        .star-rating-interactivo .star:active { transform: scale(0.8); }

        .texto-legal { font-size: 0.8rem; color: #555; margin: 15px 0; background-color: #f9f9f9; padding: 10px; border-radius: 5px; text-align: left; }
        .btn-enviar-wa { width: 100%; background: var(--green); color: white; border: none; padding: 12px; border-radius: 5px; cursor: pointer; font-weight: bold; font-size: 1rem; display: flex; justify-content: center; align-items: center; gap: 8px; }

        .seccion-testimonios { background-color: #f8f9fa; padding: 40px 0; overflow: hidden; border-top: 1px solid #eee; }
        .titulo-testimonios { text-align: center; margin-bottom: 30px; color: var(--midnight); }
        .carrusel-track { display: flex; animation: desplazamiento 30s linear infinite; }
        .testimonio-card { width: 300px; margin: 0 15px; background: white; padding: 20px; border-radius: 15px; box-shadow: 0 5px 15px rgba(0,0,0,0.03); border: 1px solid #eee; flex-shrink: 0; }
        .estrellas { color: var(--gold); margin-bottom: 10px; font-size: 1.2rem; }
        .texto-testimonio { font-style: italic; color: #555; font-size: 0.9rem; line-height: 1.5; }
        .autor-testimonio { margin-top: 15px; font-weight: bold; font-size: 0.85rem; color: var(--midnight); display: flex; align-items: center; gap: 10px; }
        .avatar-letra { width: 30px; height: 30px; background: var(--sand); border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 0.8rem; }
        @keyframes desplazamiento { 0% { transform: translateX(0); } 100% { transform: translateX(-50%); } }

        .skeleton-card { width: 300px; height: 480px; background: #fff; border-radius: 15px; border: 1px solid #eee; overflow: hidden; }
        .sk-photo { width: 100%; height: 180px; background: #eee; animation: pulse 1.5s infinite; }
        .sk-info { padding: 20px; }
        .sk-line { height: 15px; background: #eee; margin-bottom: 10px; border-radius: 4px; animation: pulse 1.5s infinite; }
        .sk-line.short { width: 60%; }
        @keyframes pulse { 0% { opacity: 0.6; } 50% { opacity: 1; } 100% { opacity: 0.6; } }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }

        @media (max-width: 768px) { 
            .btn-menu-filtros { display: block; }
            .buscador-flotante { flex-direction: column; width: 90%; gap: 10px; padding: 0; margin-top: 0; border: none; box-shadow: none; background: transparent; max-height: 0; opacity: 0; pointer-events: none; box-sizing: border-box; }
            .buscador-flotante.activo { max-height: 600px; opacity: 1; pointer-events: all; padding: 20px; background: white; border: 1px solid #eee; box-shadow: 0 15px 35px rgba(0,0,0,0.1); }
            .input-filtro, .select-filtro { width: 100%; }
            .btn-geo { display: none; }
            .btn-geo-mobile { display: block; }
            .card { width: 100%; max-width: 360px; margin: 0 auto; height: auto; min-height: 480px; } 
            .directorio { padding: 30px 15px; gap: 20px; } 
            .modal-overlay { align-items: flex-start; padding-top: 30px; } 
            .modal-perfil-card { flex-direction: column; width: 100%; height: auto; max-height: none; overflow: visible; } 
            .perfil-sidebar { width: 100%; padding: 25px; border-right: none; border-bottom: 2px solid #f0f0f0; background: #f8f9fa; }
            .perfil-content { width: 100%; padding: 25px; text-align: center; background: white; }
            .botones-perfil-container { flex-direction: column; }
            .btn-calificar { width: 100%; }
            .form-grid { grid-template-columns: 1fr; } 
            .form-full { grid-column: span 1; } 
        }
    </style>
</head>
<body onload="cargarDatos()">

    <nav>
        <div class="logo" onclick="cambiarVista('paciente')">🌿 WellnessTech</div>
        <button onclick="cambiarVista('profesional')" style="background:none; border: 1px solid var(--midnight); padding: 5px 15px; border-radius: 5px; cursor: pointer;">Soy Psicólogo</button>
    </nav>

    <div id="vistaPaciente">
        <header class="hero">
            <h1>Tu bienestar mental en buenas manos.</h1>
            <p>Encuentra al especialista perfecto para ti.</p>
            <div class="buscador-container">
                <button class="btn-menu-filtros" onclick="toggleFiltros()">☰ Filtrar Búsqueda</button>
                <div class="buscador-flotante" id="filtrosBox">
                    <input type="text" id="filtroTexto" class="input-filtro" placeholder="🔍 Especialidad, nombre, síntoma..." onkeyup="filtrar()">
                    <select id="filtroEspecialidad" class="select-filtro" onchange="filtrar()"><option value="todos">🧠 Especialidad</option><option value="ansiedad">Ansiedad</option><option value="depresión">Depresión</option><option value="pareja">Pareja</option><option value="infantil">Infantil</option><option value="autoestima">Autoestima</option><option value="duelo">Duelo</option><option value="estrés">Estrés</option><option value="adicciones">Adicciones</option><option value="tdah">TDAH</option></select>
                    <select id="filtroModalidad" class="select-filtro" onchange="filtrar()"><option value="todos">💻 Modalidad</option><option value="online">Online</option><option value="presencial">Presencial</option></select>
                    <select id="filtroSexo" class="select-filtro" onchange="filtrar()"><option value="todos">⚧ Género</option><option value="femenino">Mujer</option><option value="masculino">Hombre</option></select>
                    <select id="filtroCiudad" class="select-filtro" onchange="filtrar()"><option value="todos">📍 Ciudad</option><option value="Caracas">Caracas</option><option value="Valencia">Valencia</option><option value="Maracaibo">Maracaibo</option></select>
                    <button class="btn-geo" onclick="simularGeo()" title="Usar mi ubicación actual">🎯</button>
                    <button class="btn-geo-mobile" onclick="simularGeo()">📍 Usar mi ubicación</button>
                </div>
            </div>
        </header>

        <section class="directorio" id="directorio">
            <div class="skeleton-card"><div class="sk-photo"></div><div class="sk-info"><div class="sk-line"></div><div class="sk-line short"></div><div class="sk-line"></div></div></div>
            <div class="skeleton-card"><div class="sk-photo"></div><div class="sk-info"><div class="sk-line"></div><div class="sk-line short"></div><div class="sk-line"></div></div></div>
            <div class="skeleton-card"><div class="sk-photo"></div><div class="sk-info"><div class="sk-line"></div><div class="sk-line short"></div><div class="sk-line"></div></div></div>
        </section>

        <div id="contenedorMostrarMas" style="text-align:center; width:100%; display:none; padding-bottom: 40px;">
            <button onclick="mostrarMas()" class="btn-mostrar-mas">Mostrar más especialistas ⬇️</button>
        </div>

        <section class="seccion-testimonios" id="seccionTestimonios" style="display:none;">
            <h3 class="titulo-testimonios">Experiencias Reales de Pacientes</h3>
            <div class="carrusel-track" id="carruselTestimonios"></div>
        </section>
    </div>

    <div id="vistaProfesional">
        <div class="registro-container">
            <div class="registro-header"><h2>Únete a la red líder en Venezuela</h2><p>Gestiona tu consulta y consigue pacientes verificados.</p></div>
            <form onsubmit="event.preventDefault(); procesarRegistro();">
                <div style="display:none; visibility:hidden;"><input type="text" id="campoTrampa" autocomplete="off"></div>
                <div class="form-grid">
                    <div class="form-group"><label>Nombres</label><input type="text" id="regNombres" required pattern="[A-Za-zÁ-ÿ\s]+" title="Solo letras"></div>
                    <div class="form-group"><label>Apellidos</label><input type="text" id="regApellidos" required pattern="[A-Za-zÁ-ÿ\s]+" title="Solo letras"></div>
                    <div class="form-group"><label>Correo Electrónico</label><input type="email" id="regCorreo" required placeholder="tucorreo@gmail.com"></div>
                    <div class="form-group"><label>Teléfono (WhatsApp)</label><input type="tel" id="regTelefono" required pattern="[0-9]+" placeholder="04141234567" title="Solo números"></div>
                    <div class="form-group"><label>Número de FPV</label><input type="number" id="regFPV" required min="1"></div>
                    <div class="form-group"><label>Título Principal</label><select id="regTitulo"><option>Cargando...</option></select></div>
                    <div class="form-group"><label>Precio Consulta ($)</label><input type="number" id="regPrecio" placeholder="40" min="0"></div>
                    <div class="form-group"><label>Ciudad Base</label><select id="regCiudad"><option>Caracas</option><option>Valencia</option><option>Maracaibo</option></select></div>
                    <div class="form-group"><label>Género</label><select id="regSexo"><option value="femenino">Femenino</option><option value="masculino">Masculino</option></select></div>
                    <div class="form-group"><label>Modalidad de Consulta</label><select id="regModalidad"><option value="online">Online</option><option value="presencial">Presencial</option><option value="online, presencial">Ambas</option></select></div>
                    
                    <div class="form-group form-full">
                        <label>Especialidades Clínicas</label>
                        <div class="tags-grid" id="listaEspecialidades">
                            <label class="tag-checkbox"><input type="checkbox" value="Ansiedad"><span class="tag-label">Ansiedad</span></label><label class="tag-checkbox"><input type="checkbox" value="Depresión"><span class="tag-label">Depresión</span></label><label class="tag-checkbox"><input type="checkbox" value="Pareja"><span class="tag-label">Pareja/Familia</span></label><label class="tag-checkbox"><input type="checkbox" value="Infantil"><span class="tag-label">Infantil</span></label><label class="tag-checkbox"><input type="checkbox" value="Autoestima"><span class="tag-label">Autoestima</span></label><label class="tag-checkbox"><input type="checkbox" value="Duelo"><span class="tag-label">Duelo</span></label><label class="tag-checkbox"><input type="checkbox" value="Estrés"><span class="tag-label">Estrés</span></label><label class="tag-checkbox"><input type="checkbox" value="Adicciones"><span class="tag-label">Adicciones</span></label><label class="tag-checkbox"><input type="checkbox" value="TDAH"><span class="tag-label">TDAH</span></label><label class="tag-checkbox"><input type="checkbox" value="Sexualidad"><span class="tag-label">Sexualidad</span></label>
                        </div>
                    </div>

                    <div class="form-group form-full">
                        <label>Turnos Disponibles en la semana</label>
                        <div class="schedule-compact" id="listaDias">
                            <div class="day-column"><span class="day-name">Lun</span><div class="shift-toggles"><label class="shift-checkbox"><input type="checkbox" value="lun_am"><span class="shift-text">☀️</span></label><label class="shift-checkbox"><input type="checkbox" value="lun_pm"><span class="shift-text">🌙</span></label></div></div>
                            <div class="day-column"><span class="day-name">Mar</span><div class="shift-toggles"><label class="shift-checkbox"><input type="checkbox" value="mar_am"><span class="shift-text">☀️</span></label><label class="shift-checkbox"><input type="checkbox" value="mar_pm"><span class="shift-text">🌙</span></label></div></div>
                            <div class="day-column"><span class="day-name">Mié</span><div class="shift-toggles"><label class="shift-checkbox"><input type="checkbox" value="mier_am"><span class="shift-text">☀️</span></label><label class="shift-checkbox"><input type="checkbox" value="mier_pm"><span class="shift-text">🌙</span></label></div></div>
                            <div class="day-column"><span class="day-name">Jue</span><div class="shift-toggles"><label class="shift-checkbox"><input type="checkbox" value="jue_am"><span class="shift-text">☀️</span></label><label class="shift-checkbox"><input type="checkbox" value="jue_pm"><span class="shift-text">🌙</span></label></div></div>
                            <div class="day-column"><span class="day-name">Vie</span><div class="shift-toggles"><label class="shift-checkbox"><input type="checkbox" value="vie_am"><span class="shift-text">☀️</span></label><label class="shift-checkbox"><input type="checkbox" value="vie_pm"><span class="shift-text">🌙</span></label></div></div>
                            <div class="day-column"><span class="day-name">Sáb</span><div class="shift-toggles"><label class="shift-checkbox"><input type="checkbox" value="sab_am"><span class="shift-text">☀️</span></label><label class="shift-checkbox"><input type="checkbox" value="sab_pm"><span class="shift-text">🌙</span></label></div></div>
                        </div>
                    </div>

                    <div class="form-group form-full"><label>Foto de Perfil Profesional</label><input type="file" id="regFoto" accept="image/png, image/jpeg" required><small style="color:#666;">Se verá en la web (Máx 5MB).</small></div>
                    <div class="form-group form-full"><label>Biografía (Descripción de tu consulta)</label><textarea id="regBio" rows="3" maxlength="500"></textarea></div>
                    
                    <div class="seccion-seguridad form-full">
                        <h3>🔒 Verificación de Credenciales</h3>
                        <p>Para proteger a los pacientes, validamos tu identidad. <strong>Estos documentos NO serán públicos.</strong></p>
                        <div class="form-group" style="text-align: left;"><label>Foto de la Cédula de Identidad</label><input type="file" id="regCedula" accept="image/png, image/jpeg, application/pdf" required></div>
                        <div class="form-group" style="text-align: left; margin-top: 15px;"><label>Foto del Título Universitario</label><input type="file" id="regDocTitulo" accept="image/png, image/jpeg, application/pdf" required></div>
                    </div>
                </div>
                <button class="btn-registro">Enviar Solicitud de Verificación</button>
            </form>
            <p style="text-align:center; margin-top:20px;"><a href="#" onclick="cambiarVista('paciente')" style="color:var(--midnight); text-decoration:none;">← Volver al Directorio</a></p>
        </div>
    </div>

    <div id="modalPerfil" class="modal-overlay" onclick="cerrarPerfilFuera(event)">
        <div class="modal-perfil-card" onclick="event.stopPropagation()">
            <div class="perfil-sidebar">
                <div class="perfil-foto-grande" id="pFoto"></div>
                <div class="perfil-precio-box"><div style="font-size:0.8rem; color:#777;">CONSULTA</div><div class="monto-precio" id="pPrecio">$0</div></div>
                <div class="badge-disponibilidad" id="pDisponibilidad">...</div>
                <div class="badge-turno" id="pTurno" style="display:none;"></div>
            </div>
            <div class="perfil-content">
                <button onclick="cerrarPerfil()" style="float:right; border:none; background:none; font-size:1.5rem; cursor:pointer;">×</button>
                <h2 class="perfil-nombre" id="pNombre">Nombre</h2>
                <span id="pTitulo" class="perfil-titulo-destacado">Título</span>
                <span id="pEstrellas" class="perfil-rating">⭐⭐⭐⭐⭐</span>
                <span id="pFpvDisplay" class="perfil-fpv">FPV: ...</span>
                <span class="seccion-titulo" style="display:block;">Sobre mí</span>
                <p id="pBio" style="color:#555; line-height:1.6; margin-bottom:20px;">...</p>
                <span class="seccion-titulo">Especialidades</span>
                <ul id="pEspecialidades" style="list-style:none; padding:0; display:flex; gap:5px; flex-wrap:wrap;"></ul>
                
                <div class="botones-perfil-container">
                    <button class="btn-agendar" onclick="abrirModalContactoDesdePerfil()">📅 Agendar Cita</button>
                    <button class="btn-calificar" onclick="abrirModalResena()">⭐ Calificar</button>
                </div>
            </div>
        </div>
    </div>

    <div id="modalContacto" class="modal-overlay modal-pequeno" style="z-index: 3000;" onclick="cerrarModalFuera(event, 'modalContacto')">
        <div class="modal-content" onclick="event.stopPropagation()">
            <h3 id="tituloModal" style="margin-top:0;">Contactar al Especialista</h3>
            <input type="text" id="nombreP" placeholder="Tu nombre">
            <input type="tel" id="telP" placeholder="Tu número de celular">
            <div class="texto-legal">🔒 Se abrirá WhatsApp para contactar directamente al doctor.</div>
            
            <button class="btn-enviar-wa" onclick="enviarLeadWa()">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="white"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51a12.8 12.8 0 0 0-.57-.01c-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 0 1-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 0 1-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 0 1 2.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0 0 12.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 0 0 5.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 0 0-3.48-8.413Z"/></svg>
                Continuar a WhatsApp
            </button>
            <button onclick="cerrarModal('modalContacto')" style="background:none; border:none; color:#999; width:100%; margin-top:10px; cursor:pointer;">Cancelar</button>
        </div>
    </div>

    <div id="modalResena" class="modal-overlay modal-pequeno" style="z-index: 3000;" onclick="cerrarModalFuera(event, 'modalResena')">
        <div class="modal-content" onclick="event.stopPropagation()">
            <h3 style="margin-top:0;">Dejar Reseña</h3>
            <p style="font-size:0.9rem; color:#666; margin-bottom: 15px;" id="tituloResena">Doctor</p>
            <div style="display: flex; gap: 10px;">
                <input type="text" id="resenaNombre" placeholder="Tu Nombre">
                <input type="text" id="resenaApellido" placeholder="Tu Apellido">
            </div>
            <p class="texto-legal" style="margin-top: 5px; margin-bottom: 15px;">🔒 <b>Privacidad:</b> Publicaremos solo tus iniciales (Ej: P. P.).</p>
            <div class="star-rating-interactivo" id="estrellasInteractivas">
                <span class="star active" data-val="1">★</span><span class="star active" data-val="2">★</span><span class="star active" data-val="3">★</span><span class="star active" data-val="4">★</span><span class="star active" data-val="5">★</span>
            </div>
            <input type="hidden" id="resenaEstrellas" value="5">
            <textarea id="resenaComentario" rows="3" placeholder="Escribe tu experiencia..."></textarea>
            <button class="btn-enviar" id="btnEnviarResena" onclick="enviarResena()">Enviar Calificación</button>
            <button onclick="cerrarModal('modalResena')" style="background:none; border:none; color:#999; width:100%; margin-top:10px; cursor:pointer;">Cancelar</button>
        </div>
    </div>

    <script src="config.js"></script>

    <script>
        function escapeHTML(str) { if (str === null || str === undefined) return ""; return String(str).replace(/[&<>'"]/g, tag => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[tag])); }
        function quitarAcentos(cadena) { if (!cadena) return ""; return cadena.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase(); }

        let doctoresDB = {}; let todosLosDoctores = []; let doctoresFiltrados = [];
        let reseñasGenerales = []; let calificacionDoctores = {}; 
        let limiteActual = 6; const ITEMS_POR_PAGINA = 6; let doctorActualId = ""; let doctorSeleccionado = "";

        document.addEventListener('DOMContentLoaded', () => {
            const stars = document.querySelectorAll('#estrellasInteractivas .star');
            const hiddenInput = document.getElementById('resenaEstrellas');
            stars.forEach(star => {
                star.addEventListener('click', function() {
                    const val = parseInt(this.getAttribute('data-val'));
                    hiddenInput.value = val;
                    actualizarUIEstrellas(val);
                });
            });
        });

        function actualizarUIEstrellas(val) { document.querySelectorAll('#estrellasInteractivas .star').forEach(s => { if (parseInt(s.getAttribute('data-val')) <= val) s.classList.add('active'); else s.classList.remove('active'); }); }
        function shuffleArray(array) { for (let i = array.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [array[i], array[j]] = [array[j], array[i]]; } }

        function cargarDatos() {
            if(window.innerWidth > 768) { document.getElementById('filtrosBox').classList.add('activo'); }
            fetch(SCRIPT_URL).then(r => r.json()).then(data => {
                const docs = data.doctores || []; const titulos = data.titulos || []; reseñasGenerales = data.resenas || []; 
                calificacionDoctores = {};
                reseñasGenerales.forEach(r => {
                    let fpv = r.fpv_doctor || r.FPV_Doctor;
                    if(!calificacionDoctores[fpv]) calificacionDoctores[fpv] = { sum: 0, count: 0 };
                    calificacionDoctores[fpv].sum += Number(r.estrellas || r.Estrellas || 5);
                    calificacionDoctores[fpv].count += 1;
                });
                renderTestimonios();
                let aprobados = docs.filter(doc => (doc.estado || "").toLowerCase() === "aprobado");
                if (aprobados.length === 0) { document.getElementById('directorio').innerHTML = "<p style='width:100%; text-align:center;'>No hay doctores aprobados.</p>"; return; }
                shuffleArray(aprobados);
                todosLosDoctores = aprobados.map(doc => {
                    let fpvValue = doc.FPV || doc.fpv || "N/A"; let id = escapeHTML(doc.id || fpvValue); doc.id = id; doctoresDB[id] = doc; return doc;
                });
                doctoresFiltrados = [...todosLosDoctores]; renderCards();
                const sel = document.getElementById('regTitulo');
                if(titulos.length > 0) { sel.innerHTML = ""; titulos.forEach(t => { let o = document.createElement("option"); o.value = t.codigo; o.text = t.nombre; sel.appendChild(o); }); }
            }).catch(e => document.getElementById('directorio').innerHTML = "<p style='color:red; text-align:center;'>Error de conexión.</p>");
        }

        function renderTestimonios() {
            const seccion = document.getElementById('seccionTestimonios');
            const track = document.getElementById('carruselTestimonios');
            track.innerHTML = "";
            if(reseñasGenerales.length === 0) return; 
            seccion.style.display = "block";
            let reviews = [...reseñasGenerales]; shuffleArray(reviews); let topReviews = reviews.slice(0, 6); 
            let renderBlock = topReviews.map(r => {
                let est = parseInt(r.estrellas || r.Estrellas || 5); let stars = "★".repeat(est) + "☆".repeat(5-est);
                let pac = escapeHTML(r.paciente || r.Paciente || "Anónimo"); let letra = pac.charAt(0).toUpperCase();
                let com = escapeHTML(r.comentario || r.Comentario || ""); if(com.length > 100) com = com.substring(0, 100) + "..."; 
                return `<div class="testimonio-card"><div class="estrellas">${stars}</div><p class="texto-testimonio">"${com}"</p><div class="autor-testimonio"><div class="avatar-letra">${letra}</div> ${pac}</div></div>`;
            }).join('');
            track.innerHTML = renderBlock + renderBlock; track.style.width = `calc(330px * ${topReviews.length * 2})`;
        }

        function renderCards() {
            const dir = document.getElementById('directorio'); dir.innerHTML = ''; 
            if (doctoresFiltrados.length === 0) { dir.innerHTML = '<div id="noResultados" style="display:block; text-align:center; width:100%; color:#777; font-size:1.2rem; margin-top:20px;">😔 No encontramos especialistas.</div>'; document.getElementById('contenedorMostrarMas').style.display = 'none'; return; }
            let max = Math.min(limiteActual, doctoresFiltrados.length);
            for (let i = 0; i < max; i++) {
                let doc = doctoresFiltrados[i]; let n = escapeHTML(doc.nombres+" "+doc.apellidos);
                let fotoUrl = doc.foto ? doc.foto : ""; let fotoHTML = fotoUrl ? `<img src="${fotoUrl}" onerror="this.src='https://cdn-icons-png.flaticon.com/512/3135/3135715.png'" style="width:100%; height:100%; object-fit:cover;">` : `<div style="font-size:4rem;">👤</div>`;
                let ratingHtml = ""; let calif = calificacionDoctores[doc.id];
                if(calif) { let prom = (calif.sum / calif.count).toFixed(1); ratingHtml = `<div class="estrellas-card">⭐ ${prom}</div>`; }
                let colorFondo = doc.color || '#A3D8F4'; let isVip = (colorFondo.toLowerCase() === '#f1c40f' || colorFondo.toLowerCase() === '#ffd700');
                let etiquetaVipHTML = isVip ? `<span class="tag tag-vip">⭐ DESTACADO</span>` : '';
                let estiloBordeVip = isVip ? `border: 2px solid var(--gold); box-shadow: 0 10px 25px rgba(241,196,15,0.2);` : ``;
                let div = document.createElement('div'); div.className = 'card'; div.style = estiloBordeVip; div.onclick = function() { verPerfil(doc.id); };
                div.innerHTML = `<div class="photo" style="background:${colorFondo}">${fotoHTML}</div>
                    <div class="info"><div class="tags-container">${generarTags(doc.modalidad)}${etiquetaVipHTML}</div><span class="fpv">✓ VERIFICADO</span>${ratingHtml}<h3 style="margin-top:5px;">Lic. ${n}</h3><p>${escapeHTML(doc.titulo_nombre || "Especialista")}<br>${escapeHTML(doc.ciudad)}</p><button class="btn-contact">Ver Perfil</button></div>`;
                dir.appendChild(div);
            }
            document.getElementById('contenedorMostrarMas').style.display = (doctoresFiltrados.length > limiteActual) ? 'block' : 'none';
        }

        function mostrarMas() { limiteActual += ITEMS_POR_PAGINA; renderCards(); }
        function toggleFiltros() { document.getElementById('filtrosBox').classList.toggle('activo'); }

        function filtrar() {
            let txt = quitarAcentos(document.getElementById('filtroTexto').value); 
            let esp = quitarAcentos(document.getElementById('filtroEspecialidad').value);
            let mod = document.getElementById('filtroModalidad').value.toLowerCase();
            let sexo = document.getElementById('filtroSexo').value.toLowerCase();
            let ciudad = document.getElementById('filtroCiudad').value; 
            if (txt.includes("psicologa")) { sexo = "femenino"; txt = txt.replace("psicologa", "psicolog"); } else if (txt.includes("mujer") || txt.includes("femenino")) { sexo = "femenino"; txt = txt.replace("mujer", "").replace("femenino", "").trim(); }
            doctoresFiltrados = todosLosDoctores.filter(doc => {
                let dC = quitarAcentos(doc.ciudad || ""); let dE = quitarAcentos(doc.especialidades || ""); let dM = (doc.modalidad || "").toLowerCase(); let dS = (doc.sexo || "").toLowerCase();
                let content = quitarAcentos([doc.nombres, doc.apellidos, doc.titulo_nombre, doc.especialidades, doc.bio, doc.ciudad].join(" "));
                if (txt && !content.includes(txt)) return false; if (esp !== "todos" && !dE.includes(esp)) return false; if (mod !== "todos" && !dM.includes(mod)) return false;
                if (sexo !== "todos" && dS !== sexo) return false; if (ciudad !== "todos" && (doc.ciudad || "") !== ciudad) return false;
                return true;
            });
            limiteActual = ITEMS_POR_PAGINA; renderCards();
        }

        function leerArchivo(file, esImagenRedimensionable) {
            return new Promise((resolve, reject) => {
                if(!file) resolve({ base64: null, mimeType: null });
                const reader = new FileReader();
                if(esImagenRedimensionable && file.type.startsWith('image/')) {
                    reader.onload = function(e) {
                        const img = new Image(); img.src = e.target.result;
                        img.onload = function() {
                            const c = document.createElement('canvas'); const scale = 500 / img.width; c.width = 500; c.height = img.height * scale;
                            const ctx = c.getContext("2d"); ctx.drawImage(img, 0, 0, c.width, c.height); resolve({ base64: c.toDataURL("image/jpeg", 0.7), mimeType: "image/jpeg" });
                        }
                    };
                } else { reader.onload = () => resolve({ base64: reader.result, mimeType: file.type }); }
                reader.onerror = error => reject(error); reader.readAsDataURL(file);
            });
        }

        async function procesarRegistro() {
            if (document.getElementById('campoTrampa').value !== "") return; 
            const btn = document.querySelector('.btn-registro'); btn.innerText = "Subiendo..."; btn.disabled = true;
            let nom = document.getElementById('regNombres').value.trim(); let tel = document.getElementById('regTelefono').value.replace(/\D/g, ''); 
            let espArr = []; document.querySelectorAll('#listaEspecialidades input:checked').forEach(c => espArr.push(c.value));
            let diasArr = []; document.querySelectorAll('#listaDias input:checked').forEach(c => diasArr.push(c.value));
            const fileFoto = document.getElementById('regFoto').files[0]; const fileCedula = document.getElementById('regCedula').files[0]; const fileTitulo = document.getElementById('regDocTitulo').files[0];
            if((fileCedula && fileCedula.size > 5*1024*1024) || (fileTitulo && fileTitulo.size > 5*1024*1024)) { Swal.fire('Error', 'Los documentos no pueden pesar más de 5MB.', 'error'); btn.disabled=false; btn.innerText="Enviar Solicitud"; return; }
            try {
                const [dataFoto, dataCedula, dataTitulo] = await Promise.all([ leerArchivo(fileFoto, true), leerArchivo(fileCedula, false), leerArchivo(fileTitulo, false) ]);
                const cap = (s) => s.replace(/\b\w/g, l => l.toUpperCase());
                const datos = {
                    accion: 'registrar_doctor', nombres: cap(nom), apellidos: cap(document.getElementById('regApellidos').value), 
                    correo: document.getElementById('regCorreo').value.trim(),
                    telefono: tel, fpv: document.getElementById('regFPV').value, titulo: document.getElementById('regTitulo').value, 
                    precio: document.getElementById('regPrecio').value, ciudad: document.getElementById('regCiudad').value, 
                    sexo: document.getElementById('regSexo').value, modalidad: document.getElementById('regModalidad').value,
                    especialidades: espArr, dias: diasArr, bio: document.getElementById('regBio').value, 
                    fotoBase64: dataFoto.base64, fotoMimeType: dataFoto.mimeType, cedulaBase64: dataCedula.base64, cedulaMimeType: dataCedula.mimeType, tituloBase64: dataTitulo.base64, tituloMimeType: dataTitulo.mimeType
                };
                enviarAlBackend(datos);
            } catch (error) { Swal.fire('Error', 'Error subiendo.', 'error'); btn.disabled = false; btn.innerText="Enviar Solicitud"; }
        }

        function enviarAlBackend(datos) {
            fetch(SCRIPT_URL, { method: 'POST', mode: 'no-cors', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(datos) })
            .then(() => { Swal.fire({ title: '¡Solicitud Recibida!', text: 'Nuestro equipo verificará.', icon: 'success' }); document.querySelector('form').reset(); cambiarVista('paciente'); document.querySelector('.btn-registro').disabled=false; document.querySelector('.btn-registro').innerText="Enviar Solicitud"; })
            .catch(() => { Swal.fire('Error', 'Error de conexión', 'error'); document.querySelector('.btn-registro').disabled=false; document.querySelector('.btn-registro').innerText="Enviar Solicitud"; });
        }

        function verPerfil(id) {
            doctorActualId = id; const d = doctoresDB[id]; if(!d) return;
            document.getElementById('pNombre').innerText = "Lic. " + d.nombres + " " + d.apellidos;
            document.getElementById('pTitulo').innerText = d.titulo_nombre || "Especialista";
            document.getElementById('pFpvDisplay').innerText = "FPV: " + (d.FPV || d.fpv || "N/A");
            
            let calif = calificacionDoctores[id]; let starsTxt = "Nuevo en la plataforma";
            if(calif) { let prom = (calif.sum / calif.count).toFixed(1); starsTxt = "⭐".repeat(Math.round(prom)) + ` ${prom}`; }
            document.getElementById('pEstrellas').innerText = starsTxt;

            document.getElementById('pBio').innerText = d.bio || "Sin biografía."; document.getElementById('pPrecio').innerText = "$" + d.precio;
            
            const mapaDias = {lun: 'Lun', mar: 'Mar', mier: 'Mié', jue: 'Jue', vie: 'Vie', sab: 'Sáb', dom: 'Dom'};
            let diasAtencion = []; let tieneAM = false; let tienePM = false;
            for(let key in mapaDias) { let am = d[key+'_am'] == 1; let pm = d[key+'_pm'] == 1; if(am || pm) { diasAtencion.push(mapaDias[key]); if(am) tieneAM = true; if(pm) tienePM = true; } }
            document.getElementById('pDisponibilidad').innerText = "📅 Días: " + (diasAtencion.length > 0 ? diasAtencion.join(', ') : "Previa Cita");
            
            let colorFondo = d.color || '#A3D8F4'; let f = document.getElementById('pFoto');
            f.innerHTML = d.foto ? `<img src="${d.foto}" onerror="this.src='https://cdn-icons-png.flaticon.com/512/3135/3135715.png'">` : "👤";
            f.style.background = colorFondo; f.style.border = (colorFondo.toLowerCase() === '#f1c40f' || colorFondo.toLowerCase() === '#ffd700') ? "4px solid var(--gold)" : "4px solid white";

            const l = document.getElementById('pEspecialidades'); l.innerHTML = "";
            if(d.especialidades) d.especialidades.split(',').forEach(e => { if(e.trim()) l.innerHTML += `<li style="background:var(--sky); padding:5px 10px; border-radius:15px; font-size:0.8rem;">✨ ${escapeHTML(e.trim())}</li>`; });

            let textoTurno = ""; if(tieneAM && tienePM) textoTurno = "🔄 Turnos: Mañana y Tarde"; else if(tieneAM) textoTurno = "☀️ Turnos: Mañana"; else if(tienePM) textoTurno = "🌙 Turnos: Tarde";
            const badge = document.getElementById('pTurno'); badge.innerText = textoTurno; badge.style.display = textoTurno ? 'inline-block' : 'none';
            const m = document.getElementById('modalPerfil'); m.style.display = 'flex'; setTimeout(() => m.classList.add('active'), 10);
        }

        function cerrarPerfil() { document.getElementById('modalPerfil').classList.remove('active'); setTimeout(() => document.getElementById('modalPerfil').style.display = 'none', 300); }
        function cerrarPerfilFuera(e) { if(e.target.id === 'modalPerfil') cerrarPerfil(); }
        function abrirModalContactoDesdePerfil() { cerrarPerfil(); setTimeout(() => { doctorSeleccionado = "Lic. " + doctoresDB[doctorActualId].nombres; document.getElementById('tituloModal').innerText = "Contactar a " + doctorSeleccionado; document.getElementById('modalContacto').style.display = 'flex'; setTimeout(() => document.getElementById('modalContacto').classList.add('active'), 10); }, 350); }
        function cerrarModal(idModal) { document.getElementById(idModal).classList.remove('active'); setTimeout(() => document.getElementById(idModal).style.display = 'none', 300); }
        function cerrarModalFuera(e, idModal) { if(e.target.id === idModal) cerrarModal(idModal); }
        
        function abrirModalResena() {
            cerrarPerfil();
            setTimeout(() => {
                document.getElementById('tituloResena').innerText = "Lic. " + doctoresDB[doctorActualId].nombres + " " + doctoresDB[doctorActualId].apellidos;
                document.getElementById('resenaEstrellas').value = 5; actualizarUIEstrellas(5);
                document.getElementById('modalResena').style.display = 'flex'; setTimeout(() => document.getElementById('modalResena').classList.add('active'), 10);
            }, 350);
        }

        function enviarResena() {
            let nom = document.getElementById('resenaNombre').value.trim(); let ape = document.getElementById('resenaApellido').value.trim(); let com = document.getElementById('resenaComentario').value.trim();
            if(!nom || !ape || !com) { Swal.fire('Ojo', 'Completa tu nombre, apellido y comentario.', 'warning'); return; }
            let btn = document.getElementById('btnEnviarResena'); btn.innerText = "Enviando..."; btn.disabled = true;
            const datos = { accion: 'enviar_resena', paciente: escapeHTML(nom + " " + ape), fpv_doctor: doctorActualId, estrellas: document.getElementById('resenaEstrellas').value, comentario: escapeHTML(com) };
            fetch(SCRIPT_URL, { method: 'POST', mode: 'no-cors', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(datos) })
            .then(() => { Swal.fire('¡Gracias!', 'Tu reseña fue enviada y está en revisión.', 'success'); cerrarModal('modalResena'); btn.innerText = "Enviar Calificación"; btn.disabled = false; document.getElementById('resenaNombre').value=""; document.getElementById('resenaApellido').value=""; document.getElementById('resenaComentario').value=""; })
            .catch(() => { Swal.fire('Error', 'No se pudo enviar.', 'error'); btn.innerText = "Enviar Calificación"; btn.disabled = false; });
        }

        // 🔥 FUNCION WHATSAPP V73 (Rastreador de Número Inteligente)
        function enviarLeadWa() { 
            let nomP = document.getElementById('nombreP').value.trim();
            let telP = document.getElementById('telP').value.trim();
            
            if(!nomP || !telP) { Swal.fire('Atención', 'Por favor, completa tus datos para contactar al especialista.', 'warning'); return; }

            const d = doctoresDB[doctorActualId];
            let docNombre = "Lic. " + d.nombres + " " + d.apellidos;
            
            // 🔥 RASTREADOR: Busca cualquier columna en Excel que parezca un teléfono
            let telDocBruto = d.telefono || d.Telefono || d.Teléfono || d.teléfono || d.whatsapp || "";
            if (!telDocBruto) {
                for (let key in d) {
                    if (key.toLowerCase().includes('telef') || key.toLowerCase().includes('whats')) {
                        telDocBruto = d[key];
                        break;
                    }
                }
            }

            let telDoc = String(telDocBruto).replace(/\D/g, '');
            
            if(telDoc.length < 10) {
                Swal.fire('Error', 'No se pudo encontrar el número del especialista. Intenta más tarde.', 'error');
                return;
            }

            if(telDoc.startsWith('0')) telDoc = '58' + telDoc.substring(1);
            else if(!telDoc.startsWith('58')) telDoc = '58' + telDoc;

            let mensaje = `Hola ${docNombre}, soy ${nomP}. Vi su perfil en la plataforma y me gustaría agendar una consulta. Mi número es ${telP}.`;
            let urlWA = `https://wa.me/${telDoc}?text=${encodeURIComponent(mensaje)}`;

            const datos = { 
                accion: 'agendar_cita', 
                nombre: escapeHTML(nomP), 
                telefono: escapeHTML(telP), 
                doctor: escapeHTML(docNombre),
                fpv_doctor: doctorActualId 
            };
            fetch(SCRIPT_URL, { method: 'POST', mode: 'no-cors', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(datos) });

            Swal.fire({ title: '¡Conectando!', text: 'Te estamos llevando a WhatsApp...', icon: 'success', timer: 2000, showConfirmButton: false }).then(() => {
                window.open(urlWA, '_blank');
                cerrarModal('modalContacto');
                document.getElementById('nombreP').value = "";
                document.getElementById('telP').value = "";
            });
        }

        function generarTags(mod) { if(!mod) return ""; let h=""; if(mod.includes("online")) h+='<span class="tag online">Online</span>'; if(mod.includes("presencial")) h+='<span class="tag">Presencial</span>'; return h; }
        function cambiarVista(v) { window.scrollTo(0,0); document.getElementById('vistaPaciente').style.display = v==='profesional'?'none':'block'; document.getElementById('vistaProfesional').style.display = v==='profesional'?'block':'none'; }
        function simularGeo() { Swal.fire('Geo', 'Caracas', 'info'); document.getElementById('filtroCiudad').value="Caracas"; filtrar(); }
    </script>
</body>
</html>
