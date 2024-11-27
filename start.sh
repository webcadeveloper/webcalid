#!/bin/bash

# Iniciar el servidor Streamlit en segundo plano
streamlit run main.py --server.port 8502 &

# Iniciar el servidor API Flask en segundo plano
python3 api_server.py &

# Iniciar el servidor de señalización WebRTC
python3 webrtc_signaling.py &

# Esperar a que los servidores estén listos
sleep 5

# Mantener el script en ejecución
wait
