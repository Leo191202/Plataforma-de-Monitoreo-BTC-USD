"""
=============================================================================
Proyecto:     Plataforma de Monitoreo Analítico y Trading Automatizado
Autor:        Jose Leon
Descripción:  Backend API y motor de análisis técnico. Extrae datos crudos 
              y procesa algoritmos de doble confirmación (Cruce de Medias 
              Móviles + Oscilador MACD) para emitir alertas de mercado.
=============================================================================
"""
from flask import Flask, jsonify, render_template
import sqlite3

app = Flask(__name__)

@app.route("/")
def inicio():
    return render_template("index.html")

@app.route("/api/precios")
def obtener_precios():
    conexion = sqlite3.connect("monitoreo.db")
    cursor = conexion.cursor()
    
    # Extraer los últimos 80 registros para el cálculo estabilizado del MACD
    cursor.execute("SELECT hora, precio FROM precios_bitcoin ORDER BY id DESC LIMIT 80")
    datos = cursor.fetchall()
    conexion.close()
    
    datos.reverse() 
    total_puntos = len(datos)
    
    if total_puntos == 0:
        return jsonify([])
        
    precios = [d[1] for d in datos]
    
    # --- A. CÁLCULO DE INDICADORES (EMA 5 y SMA 15) ---
    k_5 = 2 / (5 + 1)
    ema_5_arr = []
    ema_5_ant = precios[0]
    for p in precios:
        ema_5_act = (p - ema_5_ant) * k_5 + ema_5_ant
        ema_5_arr.append(ema_5_act)
        ema_5_ant = ema_5_act
        
    sma_15_arr = []
    for i in range(total_puntos):
        if i >= 14:
            sma_15_arr.append(sum(precios[i-14:i+1]) / 15)
        else:
            sma_15_arr.append(None)

    # --- B. CÁLCULO DEL OSCILADOR MACD (12, 26, 9) ---
    k_12 = 2 / (12 + 1)
    k_26 = 2 / (26 + 1)
    k_9 = 2 / (9 + 1)
    
    ema_12_arr = []
    ema_26_arr = []
    ema_12_ant = precios[0]
    ema_26_ant = precios[0]
    
    for p in precios:
        ema_12_act = (p - ema_12_ant) * k_12 + ema_12_ant
        ema_26_act = (p - ema_26_ant) * k_26 + ema_26_ant
        ema_12_arr.append(ema_12_act)
        ema_26_arr.append(ema_26_act)
        ema_12_ant = ema_12_act
        ema_26_ant = ema_26_act
        
    # Línea MACD = EMA(12) - EMA(26)
    macd_linea = [e12 - e26 for e12, e26 in zip(ema_12_arr, ema_26_arr)]
    
    # Línea de Señal = EMA(9) de la Línea MACD
    signal_linea = []
    signal_ant = macd_linea[0]
    for m in macd_linea:
        signal_act = (m - signal_ant) * k_9 + signal_ant
        signal_linea.append(signal_act)
        signal_ant = signal_act
        
    # Histograma = MACD - Signal
    histograma = [m - s for m, s in zip(macd_linea, signal_linea)]

    # --- C. MOTOR DE LÓGICA DE SEÑALES ---
    lista_datos = []
    for i in range(total_puntos):
        senal = "ESPERAR"
        
        if i > 0 and sma_15_arr[i] is not None and sma_15_arr[i-1] is not None:
            cruce_alcista_medias = (ema_5_arr[i-1] <= sma_15_arr[i-1] and ema_5_arr[i] > sma_15_arr[i])
            cruce_bajista_medias = (ema_5_arr[i-1] >= sma_15_arr[i-1] and ema_5_arr[i] < sma_15_arr[i])
            
            # Condición Long: Cruce alcista confirmado por impulso MACD positivo
            if cruce_alcista_medias and histograma[i] > 0:
                senal = "COMPRA"
            
            # Condición Short: Cruce bajista confirmado por impulso MACD negativo
            elif cruce_bajista_medias and histograma[i] < 0:
                senal = "VENTA"
                
        lista_datos.append({
            "hora": datos[i][0],
            "precio": precios[i],
            "sma_15": sma_15_arr[i],
            "ema_5": ema_5_arr[i],
            "macd": macd_linea[i],
            "signal": signal_linea[i],
            "histograma": histograma[i],
            "senal": senal
        })
        
    # Retornar únicamente los últimos 20 registros procesados al cliente
    return jsonify(lista_datos[-20:])

if __name__ == "__main__":
    app.run(debug=True)