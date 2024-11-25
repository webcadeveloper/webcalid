import streamlit as st

class USBManager:
    def __init__(self):
        self.connected_devices = []

    def connect_device(self):
        # Lógica para conectar un dispositivo USB
        device = "Micrófono USB"
        self.connected_devices.append(device)
        st.success(f"Dispositivo {device} conectado.")

    def disconnect_device(self):
        # Lógica para desconectar un dispositivo USB
        if self.connected_devices:
            device = self.connected_devices.pop()
            st.success(f"Dispositivo {device} desconectado.")
        else:
            st.warning("No hay dispositivos USB conectados.")

    def configure_device(self, device):
        # Lógica para configurar un dispositivo USB
        st.write(f"Configurando el dispositivo {device}...")
        # Aquí puedes agregar la lógica específica para configurar el dispositivo

    def get_connected_devices(self):
        return self.connected_devices