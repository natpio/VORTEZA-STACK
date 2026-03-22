import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import json
import os
import math
from datetime import datetime

# ==========================================
# 1. KONFIGURACJA I STYLIZACJA (VORTEZA DARK PRO)
# ==========================================
st.set_page_config(
    page_title="VORTEZA STACK PRO v3.2",
    layout="wide",
    initial_sidebar_state="expanded"
)

def apply_pro_theme():
    st.markdown("""
        <style>
        .stApp {
            background-color: #080808;
            background-image: radial-gradient(#1a1a1a 1px, transparent 1px);
            background-size: 20px 20px;
            color: #ececec;
        }
        [data-testid="stSidebar"] {
            background-color: #0c0c0c !important;
            border-right: 1px solid #d2a679;
        }
        .metric-card {
            background: #111;
            border-left: 4px solid #d2a679;
            padding: 15px;
            border-radius: 4px;
            margin-bottom: 10px;
        }
        .metric-val {
            color: #d2a679;
            font-family: 'JetBrains Mono', monospace;
            font-size: 1.8rem;
            font-weight: bold;
        }
        .stButton>button {
            border: 1px solid #d2a679;
            color: #d2a679;
            background: transparent;
        }
        .stButton>button:hover {
            background: #d2a679;
            color: black;
        }
        </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. SILNIK LOGISTYCZNY (NAPRAWIONY)
# ==========================================
class CargoPacker:
    def __init__(self, width, length, height):
        self.vw = width
        self.vl = length
        self.vh = height
        self.packed_items = []

    def pack(self, manifest_list):
        """
        Główny algorytm. Przyjmuje listę SŁOWNIKÓW.
        Naprawiono błąd TypeError poprzez ujednolicenie kluczy.
        """
        self.packed_items = []
        queue = []

        # 1. Przygotowanie kolejki (rozbicie na fizyczne opakowania)
        for item in manifest_list:
            # Upewniamy się, że klucze istnieją (z wartościami domyślnymi)
            qty = item.get('qty', 1)
            ipc = item.get('items_per_case', 1)
            
            num_boxes = math.ceil(qty / ipc)
            
            for _ in range(num_boxes):
                queue.append({
                    'name': item.get('name', 'Nienazwany'),
                    'w': item.get('width', 80),
                    'l': item.get('length', 120),
                    'h': item.get('height', 100),
                    'weight': item.get('weight', 0),
                    'stack': item.get('can_stack', True)
                })

        # 2. Sortowanie: Powierzchnia podstawy DESC
        queue.sort(key=lambda x: (x['w'] * x['l']), reverse=True)
        
        y_cursor = 0.0
        
        while queue:
            leader = queue.pop(0)
            lw, ll = leader['w'], leader['l']
            
            # Rotacja lidera dla optymalizacji szerokości
            if lw < ll and ll <= self.vw:
                lw, ll = ll, lw
                
            # Piętrowanie lidera (Stacking)
            max_s = math.floor(self.vh / leader['h']) if leader['stack'] else 1
            current_s = 1
            
            # Szukamy identycznych sztuk do pionowego stosu
            idx = 0
            while idx < len(queue) and current_s < max_s:
                if queue[idx]['name'] == leader['name']:
                    queue.pop(idx)
                    current_s += 1
                else:
                    idx += 1
            
            # Dodanie stosu do wyników (każdy element osobno dla wizualizacji linii)
            for s in range(current_s):
                self.packed_items.append({
                    'name': leader['name'],
                    'x': 0, 'y': y_cursor, 'z': s * leader['h'],
                    'w': lw, 'l': ll, 'h': leader['h'],
                    'color': '#d2a679'
                })
            
            # SIDE-FILLING (Wypełnianie luki obok lidera)
            x_cursor = lw
            row_l = ll
            
            j = 0
            while j < len(queue):
                cand = queue[j]
                cw, cl = cand['w'], cand['l']
                
                fit = False
                if x_cursor + cw <= self.vw and cl <= row_l:
                    fit = True
                elif x_cursor + cl <= self.vw and cw <= row_l:
                    cw, cl = cl, cw
                    fit = True
                
                if fit:
                    max_cs = math.floor(self.vh / cand['h']) if cand['stack'] else 1
                    current_cs = 1
                    queue.pop(j)
                    
                    k = 0
                    while k < len(queue) and current_cs < max_cs:
                        if queue[k]['name'] == cand['name']:
                            queue.pop(k)
                            current_cs += 1
                        else:
                            k += 1
                            
                    for cs in range(current_cs):
                        self.packed_items.append({
                            'name': cand['name'],
                            'x': x_cursor, 'y': y_cursor, 'z': cs * cand['h'],
                            'w': cw, 'l': cl, 'h': cand['h'],
                            'color': '#a88664'
                        })
                    x_cursor += cw
                else:
                    j += 1
            
            y_cursor += row_l
            
        return self.packed_items, y_cursor

# ==========================================
# 3. WIZUALIZACJA 3D
# ==========================================
def draw_3d(items, vw, vl, vh):
    fig = go.Figure()
    # Naczepa
    fig.add_trace(go.Mesh3d(
        x=[0,vw,vw,0,0,vw,vw,0], y=[0,0,vl,vl,0,0,vl,vl], z=[0,0,0,0,vh,vh,vh,vh],
        opacity=0.03, color='white'
    ))
    # Boxy
    for it in items:
        x, y, z, w, l, h = it['x'], it['y'], it['z'], it['w'], it['l'], it['h']
        fig.add_trace(go.Mesh3d(
            x=[x, x+w, x+w, x, x, x+w, x+w, x],
            y=[y, y, y+l, y+l, y, y, y+l, y+l],
            z=[z, z, z, z, z+h, z+h, z+h, z+h],
            i=[7,0,0,0,4,4,6,6,4,0,3,2], j=[3,4,1,2,5,6,5,2,0,1,6,3], k=[0,7,2,3,6,7,1,1,5,5,7,6],
            color=it['color'], opacity=0.9, flatshading=True, name=it['name']
        ))
    fig.update_layout(scene=dict(aspectmode='data', bgcolor='black', xaxis_visible=False, yaxis_visible=False, zaxis_visible=False),
                      paper_bgcolor='rgba(0,0,0,0)', margin=dict(l=0,r=0,b=0,t=0), height=700)
    return fig

# ==========================================
# 4. INTERFEJS UŻYTKOWNIKA
# ==========================================
def main():
    apply_pro_theme()
    
    if 'manifest' not in st.session_state:
        st.session_state.manifest = []

    with st.sidebar:
        st.title("VORTEZA STACK")
        v_choice = st.selectbox("POJAZD:", ["Standard FTL", "Solo", "Bus"])
        v_map = {"Standard FTL": (245, 1360, 265), "Solo": (245, 800, 250), "Bus": (170, 400, 180)}
        vw, vl, vh = v_map[v_choice]
        
        st.subheader("DODAJ ŁADUNEK")
        if st.button("DODAJ 50x TV 55\" (TEST)"):
            st.session_state.manifest.append({
                "name": "TV 55 CALI", "width": 140, "length": 20, "height": 85, 
                "weight": 25, "can_stack": True, "items_per_case": 1, "qty": 50
            })
            st.rerun()

        with st.expander("WŁASNY PRODUKT"):
            n = st.text_input("Nazwa", "Paleta")
            c1, c2 = st.columns(2)
            w = c1.number_input("Szer [cm]", 80)
            l = c2.number_input("Dł [cm]", 120)
            h = c1.number_input("Wys [cm]", 100)
            q = st.number_input("Sztuk", 1)
            stk = st.checkbox("Stacking", True)
            if st.button("DODAJ"):
                st.session_state.manifest.append({
                    "name": n, "width": w, "length": l, "height": h, 
                    "weight": 100, "can_stack": stk, "items_per_case": 1, "qty": q
                })
                st.rerun()
        
        if st.button("RESET"):
            st.session_state.manifest = []; st.rerun()

    if st.session_state.manifest:
        packer = CargoPacker(vw, vl, vh)
        # Przekazujemy listę słowników do silnika
        packed_items, ldm_total = packer.pack(st.session_state.manifest)
        
        # Statystyki
        cols = st.columns(3)
        cols[0].markdown(f"<div class='metric-card'><small>LDM</small><br><div class='metric-val'>{round(ldm_total/100, 2)}m</div></div>", unsafe_allow_html=True)
        cols[1].markdown(f"<div class='metric-card'><small>OBJĘTOŚĆ</small><br><div class='metric-val'>{len(packed_items)} box</div></div>", unsafe_allow_html=True)
        cols[2].markdown(f"<div class='metric-box'><small>WYKORZYSTANIE</small><br><b>{round((ldm_total/vl)*100,1)}%</b></div>", unsafe_allow_html=True)

        st.plotly_chart(draw_3d(packed_items, vw, max(vl, ldm_total+50), vh), use_container_width=True)
        st.table(pd.DataFrame(st.session_state.manifest))

if __name__ == "__main__":
    main()
