"""
=============================================================================
Proyecto:     Plataforma de Monitoreo Analítico y Trading Automatizado
Autor:        Jose Leon
Descripción:  Script de extracción de datos (ETL). Consulta la API de CoinGecko
              y almacena el historial de precios en una base de datos SQLite.
=============================================================================
"""
import requests
import time
import sqlite3
import datetime

# --- Inicialización de Base de Datos ---
conexion = sqlite3.connect("monitoreo.db")
cursor = conexion.cursor()

# Crear esquema si no existe
cursor.execute("""CREATE TABLE IF NOT EXISTS precios_bitcoin (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hora TEXT,
    precio REAL
)""")

# --- Bucle Principal de Extracción ---
while True:
    url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
    respuesta = requests.get(url)
    datos = respuesta.json()
    
    # Validación de respuesta
    if "bitcoin" in datos:
        precio = datos["bitcoin"]["usd"]
        hora_actual = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Inserción de datos
        cursor.execute("INSERT INTO precios_bitcoin(hora, precio) VALUES (?, ?)", (hora_actual, precio))
        conexion.commit() 
        
        print(f"[{hora_actual}] Registro insertado: ${precio}")
        
    # Rate limiting: 1 petición por minuto
    time.sleep(60)