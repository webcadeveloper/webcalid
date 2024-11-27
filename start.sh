#!/bin/bash

# Iniciar el servidor Streamlit en segundo plano
streamlit run main.py --server.port 8501 &

# Iniciar el servidor API Flask en segundo plano
python3 api_server.py &

# Esperar a que ambos servidores estén listos
sleep 5

# Mantener el script en ejecución
wait