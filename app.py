import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import json
import os
import math
from dataclasses import dataclass

# ==========================================
# 1. KONFIGURACJA SYSTEMU I STYLIZACJA UI
# ==========================================
st.set_page_config(
    page_title="VORTEZA STACK PRO v3.0",
    layout="wide",
    initial_sidebar_state="expanded"
)

def apply_custom_theme():
    st.markdown("""
        <style>
        /* Główne tło z teksturą Carbon Fibre */
        .stApp {
            background-color: #050505;
            background-image: url("https://www.transparenttextures.com/patterns/carbon-fibre.png");
            color: #e0e0e0;
        }
        
        /* Stylizacja Sidebaru */
        [data-testid="stSidebar"] {
            background-color: #0a0a0a !important;
            border-right: 2px solid #d2a679;
        }
        
        /* Customowe Karty Metryk */
        .metric-container {
            background: rgba(20, 20, 20, 0.8);
            border: 1px solid #333;
            border-left: 5px solid #d2a679;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 10px;
        }
        
        .metric-label {
            color: #888;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .metric-value {
            color: #d2a679;
            font-size: 28px;
            font-family: 'IBM Plex Mono', monospace;
            font-weight: bold;
        }

        /* Przyciski */
        .stButton>button {
            width: 100%;
            background-color: transparent;
            border: 1px solid #d2a679;
            color: #d2a679;
            transition: 0.3s;
        }
        .stButton>button:hover {
            background-color: #d2a679;
            color: black;
        }
        
        /* Tabela */
        .styled-table {
            width: 100%;
            border-collapse: collapse;
            background: #0f0f0f;
        }
        </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. SILNIK LOGISTYCZNY (BACKEND)
# ==========================================
@dataclass
class CargoItem:
    name: str
    width: float
    length: float
    height: float
    weight: float
    can_stack: bool
    qty_total: int
    items_per_case: int

class PackingEngine:
    def __init__(self, v_w, v_l, v_h):
        self.v_w = v_w
        self.v_l = v_l
        self.v_h = v_h

    def execute_packing(self, manifest: list):
        # Rozbicie na fizyczne jednostki (skrzynie)
        physical_boxes = []
        for item in manifest:
            num_boxes = math.ceil(item.qty_total / item.items_per_case)
            for _ in range(num_boxes):
                physical_boxes.append({
                    'name': item.name, 'w': item.width, 'l': item.length,
                    'h': item.height, 'weight': item.weight, 'stackable': item.can_stack
                })

        # Sortowanie: Najpierw największa podstawa (Area)
        physical_boxes.sort(key=lambda x: (x['w'] * x['l']), reverse=True)
        
        packed_structure = []
        current_y = 0.0
        to_pack = physical_boxes.copy()

        while to_pack:
            # Wybór lidera rzędu
            leader = to_pack.pop(0)
            lw, ll = leader['w'], leader['l']
            
            # Autootacja dla optymalizacji szerokości
            if lw < ll and ll <= self.v_w:
                lw, ll = ll, lw
            
            # Obliczanie pionowego stosu (Stacking)
            max_stack = math.floor(self.v_h / leader['h']) if leader['stackable'] else 1
            
            packed_structure.append({
                'name': leader['name'], 'x': 0, 'y': current_y, 'z': 0,
                'w': lw, 'l': ll, 'h': leader['h'] * max_stack, 'is_stack': max_stack > 1
            })
            
            filled_width = lw
            max_row_length = ll
            
            # SIDE-FILLING: Szukanie mniejszych elementów do tego samego rzędu
            idx = 0
            while idx < len(to_pack):
                candidate = to_pack[idx]
                cw, cl = candidate['w'], candidate['l']
                
                # Próba dopasowania w pozostałej szerokości
                can_fit = False
                if filled_width + cw <= self.v_w and cl <= max_row_length:
                    can_fit = True
                elif filled_width + cl <= self.v_w and cw <= max_row_length:
                    cw, cl = cl, cw
                    can_fit = True
                
                if can_fit:
                    c_stack = math.floor(self.v_h / candidate['h']) if candidate['stackable'] else 1
                    packed_structure.append({
                        'name': candidate['name'], 'x': filled_width, 'y': current_y, 'z': 0,
                        'w': cw, 'l': cl, 'h': candidate['h'] * c_stack, 'is_stack': c_stack > 1
                    })
                    filled_width += cw
                    to_pack.pop(idx)
                else:
                    idx += 1
            
            current_y += max_row_length

        return packed_structure, current_y

# ==========================================
# 3. WIZUALIZACJA 3D (RENDERER)
# ==========================================
def create_vorteza_visual(packed_data, v_w, v_l, v_h):
    fig = go.Figure()

    # Naczepa (Kontur)
    fig.add_trace(go.Mesh3d(
        x=[0, v_w, v_w, 0, 0, v_w, v_w, 0],
        y=[0, 0, v_l, v_l, 0, 0, v_l, v_l],
        z=[0, 0, 0, 0, v_h, v_h, v_h, v_h],
        i=[7, 0, 0, 0, 4, 4, 6, 6, 4, 0, 3, 2],
        j=[3, 4, 1, 2, 5, 6, 5, 2, 0, 1, 6, 3],
        k=[0, 7, 2, 3, 6, 7, 1, 1, 5, 5, 7, 6],
        opacity=0.05, color='white', hoverinfo='none'
    ))

    # Ładunek
    for b in packed_data:
        x, y, z, w, l, h = b['x'], b['y'], b['z'], b['w'], b['l'], b['h']
        color = '#d2a679' if b['is_stack'] else '#a88664'
        
        fig.add_trace(go.Mesh3d(
            x=[x, x+w, x+w, x, x, x+w, x+w, x],
            y=[y, y, y+l, y+l, y, y, y+l, y+l],
            z=[z, z, z, z, z+h, z+h, z+h, z+h],
            i=[7, 0, 0, 0, 4, 4, 6, 6, 4, 0, 3, 2],
            j=[3, 4, 1, 2, 5, 6, 5, 2, 0, 1, 6, 3],
            k=[0, 7, 2, 3, 6, 7, 1, 1, 5, 5, 7, 6],
            color=color, opacity=0.9, flatshading=True,
            name=b['name'], text=f"PRODUKT: {b['name']}", hoverinfo="text"
        ))

    fig.update_layout(
        scene=dict(
            aspectmode='data',
            xaxis=dict(visible=False), yaxis=dict(visible=False), zaxis=dict(visible=False),
            bgcolor='black'
        ),
        paper_bgcolor='rgba(0,0,0,0)', margin=dict(l=0, r=0, b=0, t=0), height=700
    )
    return fig

# ==========================================
# 4. APLIKACJA GŁÓWNA (FRONTEND)
# ==========================================
def main():
    apply_custom_theme()
    
    if 'manifest' not in st.session_state:
        st.session_state.manifest = []

    # SIDEBAR
    with st.sidebar:
        st.markdown("<h1 style='text-align:center; color:#d2a679;'>VORTEZA STACK</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center; font-size:10px;'>PRECISION LOADING ENGINE v3.0</p>", unsafe_allow_html=True)
        st.markdown("---")
        
        st.header("POJAZD")
        v_type = st.selectbox("MODEL:", ["Standard 13.6m", "Solo 8.0m", "Delivery Bus"])
        v_dims = {"Standard 13.6m": (245, 1360, 265), "Solo 8.0m": (245, 800, 250), "Delivery Bus": (170, 400, 180)}
        v_w, v_l, v_h = v_dims[v_type]
        
        st.header("ŁADUNEK")
        tab1, tab2 = st.tabs(["BAZA", "RĘCZNIE"])
        
        with tab1:
            if os.path.exists("products.json"):
                with open("products.json", "r", encoding="utf-8") as f:
                    db = json.load(f)
                selected_prod = st.selectbox("PRODUKT:", [p['name'] for p in db])
                qty = st.number_input("ILOŚĆ:", min_value=1, value=1)
                if st.button("DODAJ PRODUKT"):
                    p = next(x for x in db if x['name'] == selected_prod)
                    st.session_state.manifest.append(CargoItem(
                        p['name'], p['width'], p['length'], p['height'], p['weight'], 
                        p['canStack'], qty, p['itemsPerCase']
                    ))
            else:
                st.error("Brak pliku products.json")

        with tab2:
            n = st.text_input("NAZWA:", "Box")
            c1, c2 = st.columns(2)
            w = c1.number_input("SZER [cm]", value=80)
            l = c2.number_input("DŁ [cm]", value=120)
            h = c1.number_input("WYS [cm]", value=100)
            stk = st.checkbox("MOŻNA STACKOWAĆ", value=True)
            if st.button("DODAJ RĘCZNIE"):
                st.session_state.manifest.append(CargoItem(n, w, l, h, 50, stk, 1, 1))

        if st.button("WYCZYŚĆ LISTĘ"):
            st.session_state.manifest = []
            st.rerun()

    # PANEL GŁÓWNY
    if st.session_state.manifest:
        engine = PackingEngine(v_w, v_l, v_h)
        packed_data, total_ldm = engine.execute_packing(st.session_state.manifest)
        
        # Statystyki po prawej
        col_main, col_stat = st.columns([0.75, 0.25])
        
        with col_stat:
            st.markdown(f"""
                <div class="metric-container">
                    <div class="metric-label">Metry Bieżące (LDM)</div>
                    <div class="metric-value">{round(total_ldm/100, 2)} m</div>
                </div>
                <div class="metric-container">
                    <div class="metric-label">Euro Palety (est.)</div>
                    <div class="metric-value">{round((total_ldm/100)*2.4, 1)}</div>
                </div>
            """, unsafe_allow_html=True)
            
            total_weight = sum(m.weight * math.ceil(m.qty_total/m.items_per_case) for m in st.session_state.manifest)
            st.write(f"Waga całkowita: **{total_weight} kg**")
            st.progress(min(1.0, total_weight / 24000))
            
            vol_eff = min(100.0, (total_ldm / v_l) * 100)
            st.write(f"Zajętość długości: **{round(vol_eff, 1)}%**")
            st.progress(vol_eff / 100)

        with col_main:
            st.plotly_chart(create_vorteza_visual(packed_data, v_w, total_ldm + 50, v_h), use_container_width=True)

        # Tabela ładunkowa
        st.subheader("MANIFEST ZAŁADUNKOWY")
        df_display = pd.DataFrame([
            {"Produkt": m.name, "Sztuk": m.qty_total, "Wymiary": f"{m.width}x{m.length}x{m.height}", "Stacking": "TAK" if m.can_stack else "NIE"}
            for m in st.session_state.manifest
        ])
        st.table(df_display)
    else:
        st.markdown("<h2 style='text-align:center; margin-top:100px;'>SYSTEM GOTOWY DO PRACY</h2>", unsafe_allow_html=True)
        st.info("Wprowadź dane ładunku w panelu bocznym, aby wygenerować plan załadunku 3D.")

if __name__ == "__main__":
    main()
