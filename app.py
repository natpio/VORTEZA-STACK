import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import json
import os
import math
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional

# --- ARCHITEKTURA DANYCH ---

@dataclass
class Box:
    name: str
    w: float
    l: float
    h: float
    weight: float
    can_stack: bool
    qty: int
    items_per_case: int
    id: Optional[int] = None

class VortezaPacker:
    """Zaawansowany silnik pakowania 3D z logiką side-filling i stacking optimization."""
    
    def __init__(self, vehicle_w: float, vehicle_l: float, vehicle_h: float):
        self.v_w = vehicle_w
        self.v_l = vehicle_l
        self.v_h = vehicle_h
        self.packed_items = []
        self.current_ldm = 0.0

    def pack(self, boxes: List[Box]) -> Tuple[List[Dict], float]:
        # 1. Rozbicie na jednostki wysyłkowe (cases)
        to_pack = []
        for b in boxes:
            num_cases = math.ceil(b.qty / b.items_per_case)
            for _ in range(num_cases):
                to_pack.append({
                    'name': b.name, 'w': b.w, 'l': b.l, 'h': b.h,
                    'weight': b.weight, 'can_stack': b.can_stack
                })

        # 2. Sortowanie heurystyczne (Area & Height)
        to_pack.sort(key=lambda x: (x['w'] * x['l'], x['h']), reverse=True)
        
        y_offset = 0.0
        while to_pack:
            # Wybór lidera rzędu
            leader = to_pack.pop(0)
            lw, ll, lh = self._orient_item(leader['w'], leader['l'], self.v_w)
            
            # Obliczanie stackingu dla lidera
            l_stack = math.floor(self.v_h / lh) if leader['can_stack'] else 1
            
            # Dodanie kolumny lidera
            self.packed_items.append({
                'name': leader['name'], 'x': 0, 'y': y_offset, 'z': 0,
                'w': lw, 'l': ll, 'h': lh * l_stack, 'count': l_stack
            })
            
            current_x = lw
            row_l = ll
            
            # 3. SIDE-FILLING: Wypełnianie szerokości rzędu
            idx = 0
            while idx < len(to_pack) and current_x < self.v_w:
                sub = to_pack[idx]
                sw, sl, sh = self._orient_item(sub['w'], sub['l'], self.v_w - current_x)
                
                # Sprawdzenie czy pasuje w głąb rzędu (row_l)
                if sw <= (self.v_w - current_x) and sl <= row_l:
                    s_stack = math.floor(self.v_h / sh) if sub['can_stack'] else 1
                    self.packed_items.append({
                        'name': sub['name'], 'x': current_x, 'y': y_offset, 'z': 0,
                        'w': sw, 'l': sl, 'h': sh * s_stack, 'count': s_stack
                    })
                    current_x += sw
                    to_pack.pop(idx)
                else:
                    idx += 1
            
            y_offset += row_l
            
        self.current_ldm = y_offset
        return self.packed_items, self.current_ldm

    def _orient_item(self, w: float, l: float, max_w: float) -> Tuple[float, float, float]:
        """Logika rotacji: zawsze staraj się ustawić szerszym bokiem do frontu naczepy."""
        if w < l and l <= max_w:
            return l, w
        return w, l

# --- INTERFEJS UŻYTKOWNIKA ---

def set_vorteza_style():
    st.markdown("""
        <style>
        .stApp {
            background: linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 100%);
            background-image: url("https://www.transparenttextures.com/patterns/carbon-fibre.png");
            color: #e0e0e0;
        }
        [data-testid="stSidebar"] {
            background-color: rgba(0,0,0,0.9) !important;
            border-right: 1px solid #d2a67933;
        }
        .metric-card {
            background: rgba(255,255,255,0.03);
            border-left: 3px solid #d2a679;
            padding: 20px;
            border-radius: 4px;
            margin-bottom: 10px;
        }
        .stMetricValue { font-family: 'IBM Plex Mono', monospace !important; color: #d2a679 !important; }
        h1, h2, h3 { font-family: 'Orbitron', sans-serif; text-transform: uppercase; }
        </style>
    """, unsafe_allow_html=True)

def render_vorteza_3d(items, v_w, v_l, v_h):
    fig = go.Figure()

    # Naczepa (Wireframe)
    fig.add_trace(go.Mesh3d(
        x=[0, v_w, v_w, 0, 0, v_w, v_w, 0],
        y=[0, 0, v_l, v_l, 0, 0, v_l, v_l],
        z=[0, 0, 0, 0, v_h, v_h, v_h, v_h],
        i=[7, 0, 0, 0, 4, 4, 6, 6, 4, 0, 3, 2],
        j=[3, 4, 1, 2, 5, 6, 5, 2, 0, 1, 6, 3],
        k=[0, 7, 2, 3, 6, 7, 1, 1, 5, 5, 7, 6],
        opacity=0.02, color='white', hoverinfo='none'
    ))

    # Skrzynie (Zoptymalizowane rysowanie kolumn)
    for i in items:
        x, y, z, w, l, h = i['x'], i['y'], i['z'], i['w'], i['l'], i['h']
        
        # Generowanie prostopadłościanu
        fig.add_trace(go.Mesh3d(
            x=[x, x+w, x+w, x, x, x+w, x+w, x],
            y=[y, y, y+l, y+l, y, y, y+l, y+l],
            z=[z, z, z, z, z+h, z+h, z+h, z+h],
            i=[7, 0, 0, 0, 4, 4, 6, 6, 4, 0, 3, 2],
            j=[3, 4, 1, 2, 5, 6, 5, 2, 0, 1, 6, 3],
            k=[0, 7, 2, 3, 6, 7, 1, 1, 5, 5, 7, 6],
            color='#d2a679' if i['count'] > 1 else '#a88664',
            opacity=0.85,
            flatshading=True,
            name=i['name'],
            text=f"PRODUKT: {i['name']}<br>LDM POSITION: {round(y/100,2)}m<br>STACKED: x{i['count']}",
            hoverinfo="text"
        ))

    fig.update_layout(
        scene=dict(
            aspectmode='data',
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            zaxis=dict(visible=False),
            camera=dict(eye=dict(x=1.5, y=-1.5, z=1.2))
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=0, r=0, b=0, t=0),
        height=700,
        showlegend=False
    )
    return fig

# --- GŁÓWNA LOGIKA APLIKACJI ---

def main():
    set_vorteza_style()
    
    # Inicjalizacja stanu
    if 'cargo_manifest' not in st.session_state:
        st.session_state.cargo_manifest = []

    # SIDEBAR: LOGO I STEROWANIE
    with st.sidebar:
        # Prawdziwe logo Vorteza (SVG lub Text stylizowany)
        st.markdown("<h1 style='color:#d2a679; border-bottom: 2px solid #d2a679;'>VORTEZA SYSTEM</h1>", unsafe_allow_html=True)
        st.write("Professional Packing Intelligence")
        
        st.header("1. KONFIGURACJA POJAZDU")
        v_type = st.selectbox("TYP POJAZDU:", ["Standard FTL (13.6m)", "Solo (8.0m)", "Jumbo (15.0m)"])
        v_map = {"Standard FTL (13.6m)": (245, 1360, 265), "Solo (8.0m)": (245, 800, 250), "Jumbo (15.0m)": (245, 1500, 300)}
        v_w, v_l, v_h = v_map[v_type]
        
        st.header("2. KREATOR ŁADUNKU")
        tab_db, tab_manual = st.tabs(["DATABASE", "MANUAL ENTRY"])
        
        with tab_db:
            if os.path.exists("products.json"):
                with open("products.json", "r", encoding="utf-8") as f:
                    db = json.load(f)
                p_names = [p['name'] for p in db]
                sel = st.selectbox("WYBIERZ Z BAZY:", p_names)
                qty = st.number_input("ILOŚĆ SZTUK:", min_value=1, value=1)
                if st.button("DODAJ DO MANIFESTU"):
                    item = next(p for p in db if p['name'] == sel)
                    st.session_state.cargo_manifest.append(Box(**item, qty=qty))
            else:
                st.error("DATABASE NOT FOUND (products.json)")

        with tab_manual:
            m_name = st.text_input("NAZWA ELEMENTU:", "Custom Case")
            c1, c2 = st.columns(2)
            m_w = c1.number_input("SZER [cm]", value=60)
            m_l = c2.number_input("DŁ [cm]", value=40)
            m_h = c1.number_input("WYS [cm]", value=80)
            m_wg = c2.number_input("WAGA [kg]", value=50)
            m_ipc = st.number_input("SZTUK W CASE:", value=1)
            m_stk = st.checkbox("STACKOWALNY?", value=True)
            if st.button("DODAJ NIESTANDARDOWY"):
                st.session_state.cargo_manifest.append(Box(m_name, m_w, m_l, m_h, m_wg, m_stk, 1, m_ipc))

        if st.button("RESETUJ CAŁY ŁADUNEK"):
            st.session_state.cargo_manifest = []
            st.rerun()

    # GŁÓWNY PANEL ANALITYCZNY
    st.subheader("SYSTEM ANALIZY PRZESTRZENNEJ")
    
    if st.session_state.cargo_manifest:
        # Obliczenia
        packer = VortezaPacker(v_w, v_l, v_h)
        packed_items, ldm = packer.pack(st.session_state.cargo_manifest)
        
        col_viz, col_metrics = st.columns([0.7, 0.3])
        
        with col_metrics:
            st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
            st.metric("METRY BIEŻĄCE (LDM)", f"{round(ldm/100, 2)} m")
            st.markdown("</div>", unsafe_allow_html=True)
            
            st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
            st.metric("EURO-PALETY (SZAC.)", f"{round((ldm/100)*2.4, 1)} / 33")
            st.markdown("</div>", unsafe_allow_html=True)

            # Wskaźniki procentowe
            total_area_m2 = (v_w * v_l) / 10000
            used_area_m2 = sum((i['w'] * i['l']) / 10000 for i in packed_items)
            area_p = min(100.0, (used_area_m2 / total_area_m2) * 100)
            
            st.write(f"Zajętość powierzchni: {round(area_p, 1)}%")
            st.progress(area_p / 100)
            
            total_weight = sum(b.weight * math.ceil(b.qty/b.items_per_case) for b in st.session_state.cargo_manifest)
            st.write(f"Waga całkowita: {total_weight} kg")
            st.progress(min(1.0, total_weight / 24000))

        with col_viz:
            st.plotly_chart(render_vorteza_3d(packed_items, v_w, ldm + 100, v_h), use_container_width=True)

        # TABELA MANIFESTU
        st.subheader("DOKUMENTACJA ZAŁADUNKOWA")
        df = pd.DataFrame([vars(b) for b in st.session_state.cargo_manifest])
        st.dataframe(df[['name', 'qty', 'width', 'length', 'height', 'weight', 'can_stack']], use_container_width=True)
        
    else:
        st.info("OCZEKIWANIE NA DANE ŁADUNKOWE... UŻYJ PANELU BOCZNEGO.")

if __name__ == "__main__":
    main()
