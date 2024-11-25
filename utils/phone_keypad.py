import numpy as np
import sounddevice as sd
import streamlit as st

class PhoneKeypad:
    def __init__(self):
        self.dtmf_freqs = {
            '1': (697, 1209), '2': (697, 1336), '3': (697, 1477),
            '4': (770, 1209), '5': (770, 1336), '6': (770, 1477),
            '7': (852, 1209), '8': (852, 1336), '9': (852, 1477),
            '*': (941, 1209), '0': (941, 1336), '#': (941, 1477)
        }
        
    def generate_dtmf_tone(self, key: str, duration: float = 0.1) -> None:
        """Generate DTMF tone for a given key."""
        if key not in self.dtmf_freqs:
            return
            
        sample_rate = 44100
        t = np.linspace(0, duration, int(duration * sample_rate), False)
        
        # Generate the two frequencies
        f1, f2 = self.dtmf_freqs[key]
        tone = 0.5 * np.sin(2*np.pi*f1*t) + 0.5 * np.sin(2*np.pi*f2*t)
        
        # Normalize and convert to 16-bit integer
        audio = np.float32(tone)
        sd.play(audio, sample_rate)
        sd.wait()
        
    def render(self, on_key_press):
        """Render the phone keypad."""
        st.markdown("""
        <style>
        .phone-keypad {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 10px;
            max-width: 300px;
            margin: 0 auto;
        }
        .key-button {
            background-color: rgba(0, 255, 0, 0.1);
            color: #00ff00;
            border: 1px solid #00ff00;
            border-radius: 5px;
            padding: 15px;
            font-size: 20px;
            cursor: pointer;
            text-align: center;
            transition: all 0.3s ease;
        }
        .key-button:hover {
            background-color: rgba(0, 255, 0, 0.2);
            transform: scale(1.05);
        }
        .key-button:active {
            background-color: rgba(0, 255, 0, 0.3);
            transform: scale(0.95);
        }
        </style>
        """, unsafe_allow_html=True)
        
        st.markdown('<div class="phone-keypad">', unsafe_allow_html=True)
        
        keys = [
            ['1', '2', '3'],
            ['4', '5', '6'],
            ['7', '8', '9'],
            ['*', '0', '#']
        ]
        
        for row in keys:
            cols = st.columns(3)
            for i, key in enumerate(row):
                with cols[i]:
                    if st.button(key, key=f"key_{key}", help=f"Press {key}"):
                        self.generate_dtmf_tone(key)
                        on_key_press(key)
        
        st.markdown('</div>', unsafe_allow_html=True)
