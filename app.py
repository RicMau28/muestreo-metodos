import streamlit as st
import random
from datetime import datetime, timedelta

# Configuración de la página
st.set_page_config(page_title="Muestreo Métodos", page_icon="📊", layout="centered")

st.title("📊 Auditoría de Muestreo de Trabajo")
st.write("Estudio de Métodos - Formato Multidía")

# --- BLOQUE 1: DATOS DE CONTROL ---
st.subheader("📋 Datos de Control")
maquina = st.text_input("Máquina / Equipo:", "Torno CNC 01")
operacion = st.text_input("Operación realizada:", "Desbastado Cilíndrico")
operario = st.text_input("Nombre del Operario:", "Juan Pérez")
analista = st.text_input("Analista Encargado:", "Tu Nombre")

# --- BLOQUE 2: JORNADA Y TOLERANCIAS ---
st.subheader("⏱️ Jornada y Tolerancias")
col_j1, col_j2 = st.columns(2)
with col_j1:
    inicio_str = st.text_input("Inicio Jornada (HH:MM):", "08:00")
with col_j2:
    fin_str = st.text_input("Fin Jornada (HH:MM):", "18:00")

st.write("Tolerancias Autorizadas (Breaks):")
texto_descansos = st.text_area("Escribe una por línea usando formato HH:MM-HH:MM", "10:00-10:15\n12:00-12:45")

# --- BLOQUE 3: ESTADÍSTICA Y PLANIFICACIÓN DIARIA ---
st.subheader("🧮 Parámetros Estadísticos y Plan")
confianza_sel = st.selectbox("Nivel de Confianza:", ["90%", "95%", "99%"], index=1)
p_input = st.number_input("Porcentaje análisis inicial p (%):", min_value=1, max_value=99, value=60)
muestras_diarias = st.number_input("¿Cuántas observaciones harás por día?", min_value=5, max_value=100, value=20)

# Inicializar estados de la aplicación en memoria de Streamlit para soportar múltiples días
if "dias_planificados" not in st.session_state:
    st.session_state.dias_planificados = {}
if "registro_multidia" not in st.session_state:
    st.session_state.registro_multidia = {}
if "n_total_teorico" not in st.session_state:
    st.session_state.n_total_teorico = 0

# --- BOTÓN DE CÁLCULO ---
if st.button("⚡ Calcular y Planificar Todo el Estudio", type="primary"):
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
        
        # Tamaño de muestra total (N)
        n_muestras_total = int(((z**2) * p * (1 - p)) / (0.05**2))
        n_muestras_total = max(1, n_muestras_total)
        st.session_state.n_total_teorico = n_muestras_total

        # Calcular cantidad de pestañas de días necesarias (Redondeo hacia arriba)
        dias_totales = -(n_muestras_total // -muestras_diarias)
        minutos_totales = int((fin_jornada - inicio_jornada).total_seconds() / 60)
        
        # Limpiar estados previos para el nuevo cálculo
        st.session_state.dias_planificados = {}
        st.session_state.registro_multidia = {}

        # Generar horas al azar diferentes para cada pestaña de día
        for d in range(1, dias_totales + 1):
            nombre_dia = f"Día {d}"
            horas_dia = []
            intentos = 0
            
            while len(horas_dia) < muestras_diarias and intentos < 20000:
                # CORRECCIÓN AQUÍ: Se cambió "minutes_totales" por "minutos_totales" para solucionar el NameError
                hora_candidata = inicio_jornada + timedelta(minutes=random.randint(0, minutos_totales))
                en_descanso = any(d_ini <= hora_candidata.time() <= d_fin for d_ini, d_fin in descansos)
                hora_str = hora_candidata.strftime("%H:%M")
                
                if not en_descanso and hora_str not in horas_dia:
                    horas_dia.append(hora_str)
                intentos += 1
                
            horas_dia.sort()
            st.session_state.dias_planificados[nombre_dia] = horas_dia
            st.session_state.registro_multidia[nombre_dia] = {h: "No observado" for h in horas_dia}
            
    except ValueError:
        st.error("Por favor, verifica los formatos de hora introducidos.")

# --- Funciones Callbacks para manejar el guardado síncrono multidía ---
def marcar_trabajando(dia, hora):
    if st.session_state[f"t_{dia}_{hora}"]:
        st.session_state.registro_multidia[dia][hora] = "Trabajando (Sí)"
        st.session_state[f"d_{dia}_{hora}"] = False
    else:
        st.session_state.registro_multidia[dia][hora] = "No observado"

def marcar_detenida(dia, hora):
    if st.session_state[f"d_{dia}_{hora}"]:
        st.session_state.registro_multidia[dia][hora] = "Detenida (No)"
        st.session_state[f"t_{dia}_{hora}"] = False
    else:
        st.session_state.registro_multidia[dia][hora] = "No observado"

# --- BLOQUE 4: PANEL INTERACTIVO EN PESTAÑAS (TABS) ---
if st.session_state.dias_planificados:
    st.subheader("📝 Registro de Observaciones en Campo")
    st.info(f"Muestra total requerida (N): {st.session_state.n_total_teorico} observaciones.")

    # Crear dinámicamente las pestañas superiores para cada día
    lista_dias = list(st.session_state.dias_planificados.keys())
    pestañas = st.tabs(lista_dias)

    # Renderizar el contenido exclusivo de cada pestaña
    for i, nombre_dia in enumerate(lista_dias):
        with pestañas[i]:
            st.success(f"📍 Horas exclusivas para el **{nombre_dia}**")
            horas_del_dia = st.session_state.dias_planificados[nombre_dia]
            
            for h in horas_del_dia:
                estado_actual = st.session_state.registro_multidia[nombre_dia].get(h, "No observado")
                check_t = (estado_actual == "Trabajando (Sí)")
                check_d = (estado_actual == "Detenida (No)")
                
                with st.container(border=True):
                    st.markdown(f"⏱️ **Hora: {h}**")
                    c_trab, c_det = st.columns(2)
                    with c_trab:
                        st.checkbox("Trabajando", value=check_t, key=f"t_{nombre_dia}_{h}", on_change=marcar_trabajando, args=(nombre_dia, h))
                    with c_det:
                        st.checkbox("Detenida", value=check_d, key=f"d_{nombre_dia}_{h}", on_change=marcar_detenida, args=(nombre_dia, h))

    # --- CALCULAR ESTADÍSTICAS GLOBALES ---
    total_trabajando = 0
    total_detenida = 0
    
    for d_nombre, registros in st.session_state.registro_multidia.items():
        valores = list(registros.values())
        total_trabajando += valores.count("Trabajando (Sí)")
        total_detenida += valores.count("Detenida (No)")
        
    total_obs_global = total_trabajando + total_detenida
    porc_util_global = (total_trabajando / total_obs_global * 100) if total_obs_global > 0 else 0.0

    st.subheader("📈 Resumen de Utilización Global")
    st.metric("Porcentaje de Utilización Acumulado", f"{porc_util_global:.2f}%")
    st.write(f"• Trabajando: {total_trabajando} | • Detenidas: {total_detenida} | • Completadas: {total_obs_global} de {st.session_state.n_total_teorico}")

    # --- GENERAR REPORTE IMPRIMIBLE INTEGRADO ---
    st.subheader("📄 Exportar Reporte Unificado")
    
    tol_html = texto_descansos.strip().replace("\n", "<br>")
    
    # Encabezado del Reporte HTML
    html = "<!DOCTYPE html><html><head><meta charset='UTF-8'><style>"
    html += "body { font-family: sans-serif; margin: 30px; color: #333; } h2 { color: #004080; text-align: center; } h3 { color: #0066cc; margin-top: 25px; border-bottom: 2px solid #0066cc; }"
    html += ".grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; background: #f2f2f2; padding: 15px; border: 1px solid #ddd; }"
    html += ".box { background: #e6f2ff; border-left: 5px solid #0066cc; padding: 15px; margin: 20px 0; } table { width: 100%; border-collapse: collapse; }"
    html += "th { background: #004080; color: white; padding: 12px; border: 1px solid #ddd; } td { padding: 14px; text-align: center; border: 1px solid #ddd; font-size: 15px; }"
    html += "</style></head><body><h2>Estudio de Métodos</h2><h4>Reporte de Muestreo Multidía</h4>"
    
    # Variables de Control
    html += "<div class='grid'>"
    html += f"<div><b>Máquina:</b> {maquina}</div><div><b>Operación:</b> {operacion}</div>"
    html += f"<div><b>Operario:</b> {operario}</div><div><b>Analista:</b> {analista}</div>"
    html += f"<div><b>Horario Jornada:</b> {inicio_str} a {fin_str}</div>"
    html += f"<div style='grid-column: span 2;'><b>Tolerancias Excluidas:</b><br>{tol_html}</div></div>"
    
    # Cuadro de resultados
    html += "<div class='box'><p><b>Resultados Consolidados:</b></p>"
    html += f"<p>• Confianza: {confianza_sel} | • Muestras Requeridas: {st.session_state.n_total_teorico}</p>"
    html += f"<p>• Auditadas: {total_obs_global} | • Trabajando: {total_trabajando} | • Detenida: {total_detenida}</p>"
    html += f"<p>• <b>UTILIZACIÓN GLOBAL ACUMULADA: {porc_util_global:.2f}%</b></p></div>"
    
    # Agregar las tablas de cada día individualmente
    for dia_nombre, horas_lista in st.session_state.dias_planificados.items():
        html += f"<h3>Registros: {dia_nombre}</h3>"
        html += "<table><thead><tr><th>Hora Al Azar</th><th>Estado Registrado</th></tr></thead><tbody>"
        for h in horas_lista:
            estado_reg = st.session_state.registro_multidia[dia_nombre].get(h, "No observado")
            html += f"<tr><td><b>{h}</b></td><td>{estado_reg}</td></tr>"
        html += "</tbody></table>"
        
    html += "</body></html>"

    st.download_button(
        label="📥 Descargar Reporte Completo Multidía (PDF/HTML)",
        data=html,
        file_name="reporte_consolidado_muestreo.html",
        mime="text/html"
    )
