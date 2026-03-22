import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import json
import os
import math
from datetime import datetime

# ==========================================
# 1. CORE CONFIGURATION & STYLING
# ==========================================
st.set_page_config(
    page_title="VORTEZA STACK PRO | Professional Logistics Suite",
    layout="wide",
    initial_sidebar_state="expanded"
)

def inject_enterprise_css():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700&family=JetBrains+Mono&display=swap');
        
        .stApp {
            background-color: #080808;
            background-image: radial-gradient(#1a1a1a 1px, transparent 1px);
            background-size: 20px 20px;
            color: #ececec;
            font-family: 'Inter', sans-serif;
        }
        
        [data-testid="stSidebar"] {
            background-color: #0c0c0c !important;
            border-right: 1px solid #2d2d2d;
            padding-top: 2rem;
        }
        
        .metric-card {
            background: linear-gradient(145deg, #111111, #161616);
            border: 1px solid #2d2d2d;
            border-left: 4px solid #d2a679;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.5);
            margin-bottom: 15px;
        }
        
        .metric-label {
            color: #888;
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            margin-bottom: 5px;
        }
        
        .metric-value {
            color: #d2a679;
            font-family: 'JetBrains Mono', monospace;
            font-size: 2rem;
            font-weight: 700;
        }

        .stButton>button {
            width: 100%;
            border-radius: 4px;
            background-color: transparent;
            border: 1px solid #d2a679;
            color: #d2a679;
            font-weight: bold;
            text-transform: uppercase;
            padding: 0.5rem;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }
        
        .stButton>button:hover {
            background-color: #d2a679;
            color: #000;
            box-shadow: 0 0 15px rgba(210, 166, 121, 0.4);
        }

        /* Tabela danych */
        .stDataFrame {
            border: 1px solid #2d2d2d;
            border-radius: 8px;
        }
        </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. LOGISTICS ENGINE (THE "BRAIN")
# ==========================================
class CargoPacker:
    def __init__(self, width, length, height):
        self.vw = width
        self.vl = length
        self.vh = height
        self.reset()

    def reset(self):
        self.packed_items = []
        self.current_ldm = 0
        self.total_weight = 0

    def pack(self, manifest):
        """
        Główny algorytm pakowania rzędowego z obsługą side-fillingu 
        oraz poprawnego fizycznego piętrowania.
        """
        self.reset()
        # Rozbicie na pojedyncze jednostki transportowe (boxy/palety)
        queue = []
        for item in manifest:
            count = math.ceil(item['qty'] / item['itemsPerCase'])
            for _ in range(count):
                queue.append({
                    'name': item['name'],
                    'w': item['width'],
                    'l': item['length'],
                    'h': item['height'],
                    'weight': item['weight'],
                    'stack': item['canStack']
                })

        # Sortowanie: Powierzchnia podstawy DESC
        queue.sort(key=lambda x: (x['w'] * x['l']), reverse=True)
        
        y_cursor = 0.0
        
        while queue:
            # Pobierz lidera rzędu
            leader = queue.pop(0)
            lw, ll = leader['w'], leader['l']
            
            # Rotacja lidera
            if lw < ll and ll <= self.vw:
                lw, ll = ll, lw
                
            # Ile sztuk TEGO SAMEGO typu wejdzie w stos w tym miejscu?
            max_s = math.floor(self.vh / leader['h']) if leader['stack'] else 1
            current_s = 1
            
            # Szukamy identycznych sztuk do stosu
            i = 0
            while i < len(queue) and current_s < max_s:
                if queue[i]['name'] == leader['name']:
                    queue.pop(i)
                    current_s += 1
                else:
                    i += 1
            
            # Dodaj lidera (stos) do listy
            # Rozbijamy na poszczególne boxy dla wizualizacji (widoczne linie podziału)
            for s_idx in range(current_s):
                self.packed_items.append({
                    'name': leader['name'],
                    'x': 0, 'y': y_cursor, 'z': s_idx * leader['h'],
                    'w': lw, 'l': ll, 'h': leader['h'],
                    'color': '#d2a679'
                })
            
            # SIDE-FILLING (Wypełnianie luki obok lidera w tym samym rzędzie)
            x_cursor = lw
            row_l = ll
            
            j = 0
            while j < len(queue):
                cand = queue[j]
                cw, cl = cand['w'], cand['l']
                
                # Próba dopasowania (z rotacją)
                fit = False
                if x_cursor + cw <= self.vw and cl <= row_l:
                    fit = True
                elif x_cursor + cl <= self.vw and cw <= row_l:
                    cw, cl = cl, cw
                    fit = True
                
                if fit:
                    max_cs = math.floor(self.vh / cand['h']) if cand['stack'] else 1
                    current_cs = 1
                    queue.pop(j) # zabierz lidera bocznego
                    
                    # Dopełnij stos boczny
                    k = 0
                    while k < len(queue) and current_cs < max_cs:
                        if queue[k]['name'] == cand['name']:
                            queue.pop(k)
                            current_cs += 1
                        else:
                            k += 1
                            
                    for cs_idx in range(current_cs):
                        self.packed_items.append({
                            'name': cand['name'],
                            'x': x_cursor, 'y': y_cursor, 'z': cs_idx * cand['h'],
                            'w': cw, 'l': cl, 'h': cand['h'],
                            'color': '#a88664'
                        })
                    x_cursor += cw
                else:
                    j += 1
            
            y_cursor += row_l
            self.total_weight += (current_s * leader['weight']) # uproszczone dla przykładu
            
        self.current_ldm = y_cursor
        return self.packed_items, self.current_ldm

# ==========================================
# 3. 3D RENDER ENGINE (PLOTLY)
# ==========================================
def draw_truck_3d(items, vw, vl, vh):
    fig = go.Figure()
    
    # Naczepa (Kontur/Szkielet)
    fig.add_trace(go.Mesh3d(
        x=[0, vw, vw, 0, 0, vw, vw, 0],
        y=[0, 0, vl, vl, 0, 0, vl, vl],
        z=[0, 0, 0, 0, vh, vh, vh, vh],
        i=[7, 0, 0, 0, 4, 4, 6, 6, 4, 0, 3, 2],
        j=[3, 4, 1, 2, 5, 6, 5, 2, 0, 1, 6, 3],
        k=[0, 7, 2, 3, 6, 7, 1, 1, 5, 5, 7, 6],
        opacity=0.03, color='#ffffff', showlegend=False
    ))

    # Renderowanie każdego boxu z osobna (dla widocznych linii podziału)
    for it in items:
        x, y, z = it['x'], it['y'], it['z']
        w, l, h = it['w'], it['l'], it['h']
        
        fig.add_trace(go.Mesh3d(
            x=[x, x+w, x+w, x, x, x+w, x+w, x],
            y=[y, y, y+l, y+l, y, y, y+l, y+l],
            z=[z, z, z, z, z+h, z+h, z+h, z+h],
            i=[7, 0, 0, 0, 4, 4, 6, 6, 4, 0, 3, 2],
            j=[3, 4, 1, 2, 5, 6, 5, 2, 0, 1, 6, 3],
            k=[0, 7, 2, 3, 6, 7, 1, 1, 5, 5, 7, 6],
            color=it['color'], opacity=0.9, flatshading=True,
            name=it['name'], hoverinfo="name"
        ))

    fig.update_layout(
        scene=dict(
            aspectmode='data',
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            zaxis=dict(visible=False),
            bgcolor='black'
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=0, r=0, b=0, t=0),
        height=750
    )
    return fig

# ==========================================
# 4. MAIN INTERFACE
# ==========================================
def main():
    inject_enterprise_css()
    
    # State Management
    if 'manifest' not in st.session_state:
        st.session_state.manifest = []

    # SIDEBAR: Kontrola wejścia
    with st.sidebar:
        st.markdown("<h1 style='color:#d2a679;'>VORTEZA STACK</h1>", unsafe_allow_html=True)
        st.markdown(f"**DATE:** {datetime.now().strftime('%Y-%m-%d')}")
        st.markdown("---")
        
        st.subheader("⚙️ KONFIGURACJA POJAZDU")
        v_choice = st.selectbox("Typ naczepy:", ["Standard FTL (13.6m)", "Solo (8.5m)", "Van (4.5m)"])
        v_data = {"Standard FTL (13.6m)": (245, 1360, 265), "Solo (8.5m)": (245, 850, 250), "Van (4.5m)": (180, 450, 190)}
        v_w, v_l, v_h = v_data[v_choice]
        
        st.markdown("---")
        st.subheader("📦 DODAJ ŁADUNEK")
        
        # Szybkie dodawanie TV 55" jako test
        if st.button("DODAJ 50szt. TV 55\" (TEST)"):
            st.session_state.manifest.append({
                "name": "TV 55 CALI", "width": 140, "length": 20, "height": 85, 
                "weight": 25, "canStack": True, "itemsPerCase": 1, "qty": 50
            })
            st.rerun()

        with st.expander("FORMULARZ RĘCZNY"):
            name = st.text_input("Nazwa produktu", "Paleta EURO")
            col1, col2 = st.columns(2)
            pw = col1.number_input("Szerokość [cm]", value=80)
            pl = col2.number_input("Długość [cm]", value=120)
            ph = col1.number_input("Wysokość [cm]", value=150)
            pweight = col2.number_input("Waga [kg]", value=450)
            pqty = st.number_input("Sztuk łącznie", value=1)
            pstack = st.checkbox("Można piętrować?", value=True)
            
            if st.button("DODAJ DO LISTY"):
                st.session_state.manifest.append({
                    "name": name, "width": pw, "length": pl, "height": ph, 
                    "weight": pweight, "canStack": pstack, "itemsPerCase": 1, "qty": pqty
                })
                st.rerun()

        if st.button("🗑️ WYCZYŚĆ LISTĘ"):
            st.session_state.manifest = []
            st.rerun()

    # MAIN AREA
    if st.session_state.manifest:
        packer = CargoPacker(v_w, v_l, v_h)
        packed_items, ldm_total = packer.pack(st.session_state.manifest)
        
        # Nagłówek statystyk
        c1, c2, c3, c4 = st.columns(4)
        
        with c1:
            st.markdown(f"""<div class='metric-card'><div class='metric-label'>Łączny LDM</div>
                        <div class='metric-value'>{round(ldm_total/100, 2)}m</div></div>""", unsafe_allow_html=True)
        with c2:
            st.markdown(f"""<div class='metric-card'><div class='metric-label'>Euro Palety (szac.)</div>
                        <div class='metric-value'>{round((ldm_total/100)*2.4, 1)}</div></div>""", unsafe_allow_html=True)
        with c3:
            total_w = sum(m['weight'] * m['qty'] for m in st.session_state.manifest)
            st.markdown(f"""<div class='metric-card'><div class='metric-label'>Waga (kg)</div>
                        <div class='metric-value'>{total_w}</div></div>""", unsafe_allow_html=True)
        with c4:
            util = round((ldm_total / v_l) * 100, 1)
            st.markdown(f"""<div class='metric-card'><div class='metric-label'>Zajętość naczepy</div>
                        <div class='metric-value'>{util}%</div></div>""", unsafe_allow_html=True)

        # Rendering 3D
        st.plotly_chart(draw_truck_3d(packed_items, v_w, max(v_l, ldm_total + 100), v_h), use_container_width=True)
        
        # Tabela ładunku
        st.subheader("📋 LISTA ZAŁADUNKOWA")
        st.dataframe(pd.DataFrame(st.session_state.manifest), use_container_width=True)
        
    else:
        st.markdown("""
            <div style='text-align: center; padding: 100px;'>
                <h2 style='color: #444;'>VORTEZA STACK ENGINE IS READY</h2>
                <p style='color: #666;'>Dodaj produkty w panelu bocznym, aby wyliczyć parametry załadunku.</p>
            </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
