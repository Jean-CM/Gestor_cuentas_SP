import streamlit as st
import pandas as pd
import sqlite3
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

# --- CONFIGURACIÓN DE BASE DE DATOS ---
conn = sqlite3.connect('database_st.db', check_same_thread=False)
c = conn.cursor()

def crear_tabla():
    c.execute('''CREATE TABLE IF NOT EXISTS registros 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, correo TEXT, contrasena TEXT, pais TEXT, estado TEXT, fecha TEXT)''')
    conn.commit()

crear_tabla()

# --- LÓGICA DE AUTOMATIZACIÓN ---
def ejecutar_bot(registros):
    options = Options()
    # options.add_argument("--headless") # Activar en la nube (Streamlit Cloud requiere config extra)
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, reg in enumerate(registros):
        correo, contra, pais, id_reg = reg[1], reg[2], reg[3], reg[0]
        status_text.text(f"🚀 Procesando {correo} (País: {pais})")
        
        try:
            # Simulacro de entrada (Aquí iría tu URL real)
            driver.get("https://www.google.com") # Ejemplo
            time.sleep(2)
            
            # Actualizar DB
            fecha_ahora = datetime.now().strftime("%Y-%m-%d %H:%M")
            c.execute("UPDATE registros SET estado='Listo', fecha=? WHERE id=?", (fecha_ahora, id_reg))
            conn.commit()
        except Exception as e:
            st.error(f"Error en {correo}: {e}")
        
        progress_bar.progress((i + 1) / len(registros))
    
    driver.quit()
    st.success("✅ ¡Proceso completado!")

# --- INTERFAZ DE USUARIO (STREAMLIT) ---
st.set_page_config(page_title="Gestor Pro Gem", layout="wide")
st.title("🚀 Gestor de Cuentas Automático (Streamlit Edition)")

col1, col2 = st.columns(2)

with col1:
    st.subheader("1. Cargar Datos")
    archivo = st.file_uploader("Sube tu CSV o Excel", type=['csv', 'xlsx'])
    if archivo:
        if st.button("Importar a Base de Datos"):
            df = pd.read_csv(archivo) if archivo.name.endswith('.csv') else pd.read_excel(archivo)
            df.columns = df.columns.str.strip().str.lower()
            for _, row in df.iterrows():
                c.execute("INSERT INTO registros (correo, contrasena, pais, estado) VALUES (?,?,?,?)",
                          (row['correo'], row['contrasena'], row['pais'], 'pendiente'))
            conn.commit()
            st.success(f"Cargados {len(df)} registros.")

with col2:
    st.subheader("2. Ejecutar Bot")
    pendientes = pd.read_sql_query("SELECT * FROM registros WHERE estado='pendiente'", conn)
    cantidad = st.number_input("Cantidad a procesar", min_value=0, max_value=len(pendientes), value=min(1, len(pendientes)))
    
    if st.button("Lanzar Automatización"):
        if cantidad > 0:
            lista_procesar = pendientes.head(cantidad).values.tolist()
            ejecutar_bot(lista_procesar)
            st.rerun() # Refrescar tabla
        else:
            st.warning("No hay registros pendientes.")

st.divider()
st.subheader("📊 Registros en el Sistema")
todo = pd.read_sql_query("SELECT * FROM registros", conn)
st.dataframe(todo, use_container_width=True)

if st.button("Descargar Reporte Final"):
    todo.to_csv("reporte_final.csv", index=False)
    st.download_button("Click para descargar CSV", data=open("reporte_final.csv", "rb"), file_name="reporte.csv")
