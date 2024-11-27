#!/bin/bash

# Función para verificar si un puerto está disponible
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null ; then
        echo "Error: Puerto $port ya está en uso"
        kill $(lsof -t -i:$port) 2>/dev/null || true
        sleep 2
    fi
}

# Verificar y liberar puertos si están en uso
check_port 8502  # Streamlit
check_port 3000  # API Server
check_port 3001  # WebRTC Signaling

echo "Iniciando servicios..."

# 1. Iniciar el servidor API Flask (debe iniciar primero ya que otros servicios dependen de él)
echo "Iniciando API Server..."
python3 api_server.py &
API_PID=$!
sleep 5

# Verificar que el API server esté funcionando
if ! curl -s http://localhost:3000 >/dev/null; then
    echo "Error: API Server no respondió correctamente"
    kill $API_PID
    exit 1
fi

# 2. Iniciar el servidor de señalización WebRTC
echo "Iniciando WebRTC Signaling Server..."
python3 webrtc_signaling.py &
WEBRTC_PID=$!
sleep 5

# 3. Iniciar el servidor Streamlit
echo "Iniciando Streamlit App..."
streamlit run main.py --server.port 8502 --server.address 0.0.0.0 --server.baseUrlPath="" &
STREAMLIT_PID=$!

# Función para manejar la señal de terminación
cleanup() {
    echo "Deteniendo servicios..."
    kill $API_PID $WEBRTC_PID $STREAMLIT_PID
    exit 0
}

# Registrar el manejador de señales
trap cleanup SIGINT SIGTERM

# Mantener el script en ejecución y monitorear los procesos
while true; do
    if ! kill -0 $API_PID 2>/dev/null; then
        echo "API Server se detuvo inesperadamente"
        cleanup
    fi
    if ! kill -0 $WEBRTC_PID 2>/dev/null; then
        echo "WebRTC Signaling Server se detuvo inesperadamente"
        cleanup
    fi
    if ! kill -0 $STREAMLIT_PID 2>/dev/null; then
        echo "Streamlit App se detuvo inesperadamente"
        cleanup
    fi
    sleep 5
done
