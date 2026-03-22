import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import json
import os
import math
from dataclasses import dataclass

# --- ZAAWANSOWANA KONFIGURACJA UI ---
st.set_page_config(page_title="VORTEZA STACK ENGINE PRO", layout="wide")

def apply_industrial_theme():
    st.markdown("""
        <style>
        .stApp { background-color: #050505; background-image: url("https://www.transparenttextures.com/patterns/carbon-fibre.png"); color: #e0e0e0; }
        [data-testid="stSidebar"] { background-color: #0a0a0a !important; border-right: 2px solid #d2a679; }
        .metric-box { background: rgba(20, 20, 20, 0.9); border-left: 5px solid #d2a679; padding: 20px; border-radius: 4px; margin: 10px 0; }
        .stMetricValue { color: #d2a679 !important; font-family: 'Courier New', monospace !important; }
        </style>
    """, unsafe_allow_html=True)

# --- MODEL DANYCH ---
@dataclass
class Product:
    name: str
    w: float
    l: float
    h: float
    weight: float
    can_stack: bool
    qty: int
    ipc: int # items per case (np. 1 paleta)

# --- SILNIK OPTYMALIZACJI (Wersja High-Performance) ---
class VorterzaLogic:
    def __init__(self, vw, vl, vh):
        self.vw, self.vl, self.vh = vw, vl, vh

    def calculate_loading(self, items):
        # 1. Przygotowanie jednostek wysyłkowych
        to_pack = []
        for it in items:
            units = math.ceil(it.qty / it.ipc)
            for _ in range(units):
                to_pack.append({'name': it.name, 'w': it.w, 'l': it.l, 'h': it.h, 'stackable': it.can_stack})

        # 2. Sortowanie: Najpierw te, które zajmują najwięcej podłogi
        to_pack.sort(key=lambda x: (x['w'] * x['l']), reverse=True)
        
        packed = []
        current_y = 0.0
        
        while to_pack:
            leader = to_pack.pop(0)
            lw, ll, lh = leader['w'], leader['l'], leader['h']
            
            # Rotacja dla oszczędności LDM
            if lw < ll and ll <= self.vw: lw, ll = ll, lw
            
            # OBLICZANIE PIĘTROWANIA (Tu rozwiązujemy problem Twoich TV)
            # Jeśli can_stack=True, sprawdzamy ile wejdzie do wysokości naczepy (np. 265cm)
            stack_height = math.floor(self.vh / lh) if leader['stackable'] else 1
            # Jeśli mamy więcej takich samych przedmiotów, "zużywamy" je do stosu
            actual_stack = 1
            for _ in range(stack_height - 1):
                for i, shadow in enumerate(to_pack):
                    if shadow['name'] == leader['name']:
                        to_pack.pop(i)
                        actual_stack += 1
                        break
            
            packed.append({
                'name': leader['name'], 'x': 0, 'y': current_y, 'z': 0,
                'w': lw, 'l': ll, 'h': lh * actual_stack, 'stacked': actual_stack
            })
            
            # SIDE-FILLING (Wypełnianie luki obok stosu)
            rem_w = self.vw - lw
            if rem_w > 20: # jeśli zostało więcej niż 20cm
                idx = 0
                while idx < len(to_pack):
                    c = to_pack[idx]
                    cw, cl, ch = c['w'], c['l'], c['h']
                    # Próba dopasowania
                    fit = False
                    if cw <= rem_w and cl <= ll: fit = True
                    elif cl <= rem_w and cw <= ll: cw, cl = cl, cw; fit = True
                    
                    if fit:
                        c_stack_limit = math.floor(self.vh / ch) if c['stackable'] else 1
                        c_actual_stack = 1
                        to_pack.pop(idx) # zabieramy lidera bocznego
                        # Dopychamy stos boczny
                        for _ in range(c_stack_limit - 1):
                            for j, shadow in enumerate(to_pack):
                                if shadow['name'] == c['name']:
                                    to_pack.pop(j)
                                    c_actual_stack += 1
                                    break
                        
                        packed.append({
                            'name': c['name'], 'x': self.vw - rem_w, 'y': current_y, 'z': 0,
                            'w': cw, 'l': cl, 'h': ch * c_actual_stack, 'stacked': c_actual_stack
                        })
                        rem_w -= cw
                    else:
                        idx += 1
            
            current_y += ll
            
        return packed, current_y

# --- INTERFEJS ---
def main():
    apply_industrial_theme()
    st.title("VORTEZA | STACK ANALYZER v3.1")
    
    if 'cargo' not in st.session_state: st.session_state.cargo = []

    with st.sidebar:
        st.header("PARAMETRY NACZEPY")
        v_type = st.selectbox("TYP:", ["FTL 13.6m", "Solo 8m", "Bus"])
        dims = {"FTL 13.6m": (245, 1360, 265), "Solo 8m": (245, 800, 250), "Bus": (170, 400, 180)}
        vw, vl, vh = dims[v_type]
        
        st.header("DODAJ TOWAR")
        with st.expander("KREATOR PRODUKTU"):
            name = st.text_input("Nazwa", "TV 55 CALI")
            c1, c2 = st.columns(2)
            w = c1.number_input("Szer [cm]", value=120)
            l = c2.number_input("Dł [cm]", value=80)
            h = c1.number_input("Wys [cm]", value=110)
            qty = st.number_input("Ilość sztuk", value=50)
            ipc = st.number_input("Sztuk na palecie", value=1)
            stack = st.checkbox("Można piętrować?", value=True)
            if st.button("DODAJ DO PLANU"):
                st.session_state.cargo.append(Product(name, w, l, h, 40, stack, qty, ipc))

        if st.button("RESET"): st.session_state.cargo = []; st.rerun()

    if st.session_state.cargo:
        logic = VorterzaLogic(vw, vl, vh)
        packed, ldm = logic.calculate_loading(st.session_state.cargo)
        
        # WIDOK STATYSTYK
        m1, m2, m3 = st.columns(3)
        with m1: st.markdown(f"<div class='metric-box'><small>LDM</small><br><span class='metric-value'>{round(ldm/100, 2)} m</span></div>", unsafe_allow_html=True)
        with m2: st.markdown(f"<div class='metric-box'><small>WYKORZYSTANIE PODŁOGI</small><br><span class='metric-value'>{round((ldm/vl)*100, 1)}%</span></div>", unsafe_allow_html=True)
        with m3: st.markdown(f"<div class='metric-box'><small>OBJĘTOŚĆ</small><br><span class='metric-value'>{len(packed)} STOSÓW</span></div>", unsafe_allow_html=True)

        # WIZUALIZACJA 3D
        fig = go.Figure()
        # Naczepa
        fig.add_trace(go.Mesh3d(x=[0,vw,vw,0,0,vw,vw,0], y=[0,0,ldm,ldm,0,0,ldm,ldm], z=[0,0,0,0,vh,vh,vh,vh], opacity=0.05, color='white'))
        # Towary
        for b in packed:
            x,y,z,bw,bl,bh = b['x'], b['y'], b['z'], b['w'], b['l'], b['h']
            fig.add_trace(go.Mesh3d(x=[x,x+bw,x+bw,x,x,x+bw,x+bw,x], y=[y,y,y+bl,y+bl,y,y,y+bl,y+bl], z=[z,z,z,z,z+bh,z+bh,z+bh,z+bh], 
                                   color='#d2a679', opacity=0.9, flatshading=True, name=b['name'],
                                   text=f"{b['name']} | Stos: x{b['stacked']}", hoverinfo="text"))
        
        fig.update_layout(scene=dict(aspectmode='data', bgcolor='black', xaxis=dict(visible=False), yaxis=dict(visible=False), zaxis=dict(visible=False)),
                          paper_bgcolor='rgba(0,0,0,0)', margin=dict(l=0,r=0,b=0,t=0), height=600)
        st.plotly_chart(fig, use_container_width=True)
        
        st.table(pd.DataFrame([vars(p) for p in st.session_state.cargo]))
    else:
        st.info("Dodaj towar, aby rozpocząć analizę.")

if __name__ == "__main__": main()
