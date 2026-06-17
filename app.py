import streamlit as st
import random
from datetime import datetime, timedelta

# Configuración de la página móvil
st.set_page_config(page_title="Muestreo Métodos", page_icon="📊", layout="centered")

st.title("📊 Auditoría de Muestreo de Trabajo")
st.write("Estudio de Métodos - Formato Móvil de Campo")

# --- BLOQUE 1: DATOS DE CONTROL ---
st.subheader("📋 Datos de Control")
maquina = st.text_input("Máquina / Equipo:", "Torno CNC 01")
operacion = st.text_input("Operación realizada:", "Desbastado Cilíndrico")
operario = st.text_input("Nombre del Operario:", "Juan Pérez")
analista = st.text_input("Analista Encargado:", "Tu Nombre")
fecha = st.text_input("Fecha de Estudio:", datetime.now().strftime("%d/%m/%Y"))

# --- BLOQUE 2: JORNADA Y TOLERANCIAS ---
st.subheader("⏱️ Jornada y Tolerancias")
col_j1, col_j2 = st.columns(2)
with col_j1:
    inicio_str = st.text_input("Inicio Jornada (HH:MM):", "08:00")
with col_j2:
    fin_str = st.text_input("Fin Jornada (HH:MM):", "16:00")

st.write("Tolerancias Autorizadas (Breaks):")
texto_descansos = st.text_area("Escribe una por línea usando formato HH:MM-HH:MM", "10:00-10:15\n12:00-12:45")

# --- BLOQUE 3: ESTADÍSTICA ---
st.subheader("🧮 Parámetros Estadísticos")
confianza_sel = st.selectbox("Nivel de Confianza:", ["90%", "95%", "99%"], index=1)
p_input = st.number_input("Porcentaje análisis inicial p (%):", min_value=1, max_value=99, value=60)

# Inicializar estados de la aplicación en memoria de Streamlit
if "horas_generadas" not in st.session_state:
    st.session_state.horas_generadas = []
if "registro_estados" not in st.session_state:
    st.session_state.registro_estados = {}

# --- BOTÓN DE CÁLCULO ---
if st.button("⚡ Calcular y Generar Horas", type="primary"):
    try:
        formato = "%H:%M"
        inicio_jornada = datetime.strptime(inicio_str.strip(), formato)
        fin_jornada = datetime.strptime(fin_str.strip(), formato)
        
        descansos = []
        if texto_descansos.strip():
            for linea in texto_descansos.strip().split("\n"):
                if "-" in linea:
                    d_ini, d_fin = linea.split("-")
                    descansos.append((datetime.strptime(d_ini.strip(), formato).time(), datetime.strptime(d_fin.strip(), formato).time()))

        z = 1 if confianza_sel == "90%" else (2 if confianza_sel == "95%" else 3)
        p = float(p_input) / 100.0
        
        n_muestras = int(((z**2) * p * (1 - p)) / (0.05**2))
        n_muestras = max(1, n_muestras)

        horas_validas = []
        minutos_totales = int((fin_jornada - inicio_jornada).total_seconds() / 60)
        
        intentos = 0
        while len(horas_validas) < n_muestras and intentos < 20000:
            hora_candidata = inicio_jornada + timedelta(minutes=random.randint(0, minutos_totales))
            en_descanso = any(d_ini <= hora_candidata.time() <= d_fin for d_ini, d_fin in descansos)
            hora_str = hora_candidata.strftime("%H:%M")
            if not en_descanso and hora_str not in horas_validas:
                horas_validas.append(hora_str)
            intentos += 1

        horas_validas.sort()
        st.session_state.horas_generadas = horas_validas
        st.session_state.registro_estados = {h: "No observado" for h in horas_validas}
        
    except ValueError:
        st.error("Por favor, verifica los formatos de hora introducidos.")

# --- BLOQUE 4: PANEL DE CAMPO (DISEÑO EN TARJETAS PARA CELULAR) ---
if st.session_state.horas_generadas:
    st.subheader("📝 Registro de Observaciones en Campo")
    st.info(f"Calculado N = {len(st.session_state.horas_generadas)} muestras.")
    
    # Generar un contenedor visual estilizado por cada hora para evitar desbordes móviles
    for h in st.session_state.horas_generadas:
        estado_actual = st.session_state.registro_estados.get(h, "No observado")
        
        check_trabajando = (estado_actual == "Trabajando (Sí)")
        check_detenida = (estado_actual == "Detenida (No)")
        
        # Usamos st.container con borde para crear una "tarjeta" limpia en el celular
        with st.container(border=True):
            st.markdown(f"⏱️ **Hora de Observación: {h}**")
            
            # Colocamos los dos checkboxes lado a lado de forma compacta
            c_trab, c_det = st.columns(2)
            with c_trab:
                marcado_t = st.checkbox("Trabajando", value=check_trabajando, key=f"t_{h}")
            with c_det:
                marcado_d = st.checkbox("Detenida", value=check_detenida, key=f"d_{h}")
            
            # Lógica de exclusión mutua automática
            if marcado_t and not check_trabajando:
                st.session_state.registro_estados[h] = "Trabajando (Sí)"
                st.rerun()
            elif marcado_d and not check_detenida:
                st.session_state.registro_estados[h] = "Detenida (No)"
                st.rerun()
            elif not marcado_t and not marcado_d and estado_actual != "No observado":
                st.session_state.registro_estados[h] = "No observado"
                st.rerun()

    # --- CALCULAR PORCENTAJES EN TIEMPO REAL ---
    valores_registro = list(st.session_state.registro_estados.values())
    t_trabajando = valores_registro.count("Trabajando (Sí)")
    t_detenida = valores_registro.count("Detenida (No)")
    total_obs = t_trabajando + t_detenida
    porc_util = (t_trabajando / total_obs * 100) if total_obs > 0 else 0.0

    st.subheader("📈 Resumen de Utilización")
    st.metric("Porcentaje de Utilización Real", f"{porc_util:.2f}%")
    st.write(f"• Trabajando: {t_trabajando} | • Detenidas: {t_detenida} | • Total lecturas realizadas: {total_obs}")

    # --- GENERAR REPORTE IMPRIMIBLE ---
    st.subheader("📄 Exportar Reporte")
    
    tol_html = texto_descansos.strip().replace("\n", "<br>")
    html_reporte = f"""
    <html><head><meta charset='UTF-8'><style>
    body {{ font-family: Arial, sans-serif; margin: 30px; color: #333; }}
    h2 {{ color: #004080; text-align: center; text-transform: uppercase; }}
    .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; background: #f2f2f2; padding: 15px; border: 1px solid #ddd; border-radius: 6px; }}
    .box {{ background: #e6f2ff; border-left: 5px solid #0066cc; padding: 15px; margin: 20px 0; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
    th {{ background: #004080; color: white; padding: 12px; border: 1px solid #ddd; }}
    td {{ padding: 16px; text-align: center; border: 1px solid #ddd; font-size: 15px; }}
    tr:nth-child(even) {{ background: #f9f9f9; }}
    </style></head><body>
    <h2>Estudio de Métodos</h2><h4>Reporte Oficial Móvil de Muestreo de Actividades</h4>
    <div class='grid'>
    <div><b>Máquina:</b> {maquina}</div><div><b>Operación:</b> {operacion}</div>
    <div><b>Operario:</b> {operario}</div><div><b>Analista:</b> {analista}</div>
    <div><b>Fecha:</b> {fecha}</div><div><b>Jornada:</b> {inicio_str} a {fin_str}</div>
    <div style='grid-column: span 2;'><b>Tolerancias:</b><br>{tol_html}</div></div>
    <div class='box'><p><b>Resultados Globales de Auditoría:</b></p>
    <p>• Confianza: {confianza_sel} | Margen de error: 5%</p>
    <p>• Muestras Planificadas: {len(st.session_state.horas_generadas)}</p>
    <p>• Eventos Trabajando: {t_trabajando} | Eventos Detenida: {t_detenida}</p>
    <p>• <b>Porcentaje de Utilización Real: {porc_util:.2f}%</b></p></div>
    <table><thead><tr><th>Hora Al Azar</th><th>Estado Registrado</th></tr></thead><tbody>
    """
    for h in st.session_state.horas_generadas:
        html_reporte += f"<tr><td><b>{h}</b></td><td>{st.session_state.registro_estados[h]}</td></tr>"
    html_reporte += "</tbody></table></body></html>"

    st.download_button(
        label="📥 Descargar Hoja de Impresión PDF/HTML",
        data=html_reporte,
        file_name="reporte_muestreo_movil.html",
        mime="text/html"
    )
