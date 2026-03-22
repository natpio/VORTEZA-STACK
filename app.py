import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import json
import os
import math

# --- KONFIGURACJA STRONY ---
st.set_page_config(
    page_title="VORTEZA SYSTEM",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- DOPRACOWANY DESIGN (CSS) ---
st.markdown("""
    <style>
    /* Tło całej strony - ciemny motyw z teksturą */
    .stApp {
        background-color: #050505;
        background-image: url("https://www.transparenttextures.com/patterns/carbon-fibre.png");
    }
    
    /* Sidebar - ciemniejszy i oddzielony */
    [data-testid="stSidebar"] {
        background-color: #0a0a0a !important;
        border-right: 1px solid #1f1f1f;
    }

    /* Styl metryk (Statystyki po prawej) */
    div[data-testid="stMetric"] {
        background-color: rgba(0, 0, 0, 0.5);
        border-bottom: 2px solid #333;
        padding: 10px;
    }
    
    div[data-testid="stMetricValue"] {
        color: #ffffff !important;
        font-family: 'Courier New', monospace;
        font-size: 36px !important;
    }

    /* Nagłówki sekcji */
    h1, h2, h3 {
        color: #e0e0e0;
        text-transform: uppercase;
        letter-spacing: 2px;
    }

    /* Paski postępu (Custom Progress Bar) */
    .stProgress > div > div > div > div {
        background-color: #d2a679;
    }

    /* Styl tabeli */
    .stTable {
        background-color: #0f0f0f;
    }
    </style>
    """, unsafe_allow_html=True)

# --- FUNKCJE DANYCH ---
def load_products():
    if os.path.exists("products.json"):
        with open("products.json", "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def pack_logic_pro(cargo_list, v_w=245, v_l=1360, v_h=265):
    flat_items = []
    for item in cargo_list:
        num_cases = math.ceil(item['qty'] / item['itemsPerCase'])
        for _ in range(num_cases):
            flat_items.append({
                'name': item['name'], 'w': item['width'], 'l': item['length'], 
                'h': item['height'], 'weight': item['weight'], 'canStack': item['canStack']
            })

    flat_items.sort(key=lambda x: x['w'] * x['l'], reverse=True)
    
    packed = []
    curr_y = 0
    remaining = flat_items.copy()

    while remaining:
        leader = remaining.pop(0)
        lw, ll, lh = leader['w'], leader['l'], leader['h']
        if lw < ll and ll <= v_w: lw, ll = ll, lw
        
        stack = math.floor(v_h / lh) if leader['canStack'] else 1
        for s in range(stack):
            packed.append({'name': leader['name'], 'x': 0, 'y': curr_y, 'z': s*lh, 'w': lw, 'l': ll, 'h': lh})
        
        filled_w = lw
        row_l = ll
        
        # Side-filling logic
        i = 0
        while i < len(remaining):
            c = remaining[i]
            cw, cl, ch = c['w'], c['l'], c['h']
            fit = False
            if filled_w + cw <= v_w and cl <= row_l: fit = True
            elif filled_w + cl <= v_w and cw <= row_l: cw, cl = cl, cw; fit = True
            
            if fit:
                c_stack = math.floor(v_h / ch) if c['canStack'] else 1
                for s in range(c_stack):
                    packed.append({'name': c['name'], 'x': filled_w, 'y': curr_y, 'z': s*ch, 'w': cw, 'l': cl, 'h': ch})
                filled_w += cw
                remaining.pop(i)
            else: i += 1
        curr_y += row_l
    return packed, curr_y

# --- INTERFEJS ---
with st.sidebar:
    # LOGO (Podmień 'logo.png' na swoją ścieżkę lub URL)
    # Jeśli masz plik lokalnie: st.image("logo.png")
    st.markdown("<h1 style='text-align: center; color: #d2a679;'>VORTEZA</h1>", unsafe_allow_html=True)
    st.markdown("---")
    
    st.header("1. POJAZD")
    v_type = st.selectbox("TYP:", ["FTL (Tir)", "Solo", "Bus"])
    v_w, v_l, v_h = (245, 1360, 265) if "Tir" in v_type else (245, 750, 250)
    
    st.header("2. DODAJ ŁADUNEK")
    if 'cargo' not in st.session_state: st.session_state.cargo = []
    
    db_tab, cust_tab = st.tabs(["Z BAZY", "WŁASNY"])
    products = load_products()
    
    with db_tab:
        p_names = [p['name'] for p in products]
        sel = st.selectbox("PRODUKT:", p_names)
        num = st.number_input("SZTUK:", min_value=1, value=1)
        if st.button("DODAJ PRODUKT"):
            p_data = next(p for p in products if p['name'] == sel)
            st.session_state.cargo.append({**p_data, "qty": num})
            
    with cust_tab:
        c_name = st.text_input("NAZWA:", "luzny box")
        c_w = st.number_input("SZER:", value=60)
        c_l = st.number_input("DŁ:", value=40)
        c_h = st.number_input("WYS:", value=100)
        c_qty = st.number_input("SZT:", value=10)
        if st.button("DODAJ WŁASNY"):
            st.session_state.cargo.append({
                "name": c_name, "width": c_w, "length": c_l, "height": c_h,
                "weight": 50, "canStack": True, "itemsPerCase": 1, "qty": c_qty
            })

    if st.button("WYCZYŚĆ"):
        st.session_state.cargo = []; st.rerun()

# --- GŁÓWNY WIDOK ---
if st.session_state.cargo:
    packed, ldm_cm = pack_logic_pro(st.session_state.cargo, v_w, v_l, v_h)
    
    col_viz, col_stats = st.columns([0.7, 0.3])
    
    with col_stats:
        st.subheader("STATYSTYKI")
        st.metric("METRY BIEŻĄCE (LDM)", f"{round(ldm_cm/100, 2)} m")
        st.metric("ZAJĘTE EP (SZAC.)", f"{round((ldm_cm/100)*2.4, 1)} / 33")
        
        area_used = sum(b['w']*b['l'] for b in packed if b['z'] == 0)
        area_perc = round((area_used / (v_w * v_l)) * 100, 1)
        st.write(f"POWIERZNIA: {area_perc}%")
        st.progress(area_perc/100)
        
        vol_used = sum(b['w']*b['l']*b['h'] for b in packed)
        vol_perc = round((vol_used / (v_w * v_l * v_h)) * 100, 1)
        st.write(f"OBJĘTOŚĆ: {vol_perc}%")
        st.progress(vol_perc/100)

    with col_viz:
        fig = go.Figure()
        # Naczepa
        fig.add_trace(go.Mesh3d(x=[0,v_w,v_w,0,0,v_w,v_w,0], y=[0,0,ldm_cm,ldm_cm,0,0,ldm_cm,ldm_cm], z=[0,0,0,0,v_h,v_h,v_h,v_h], i=[7,0,0,0,4,4,6,6,4,0,3,2], j=[3,4,1,2,5,6,5,2,0,1,6,3], k=[0,7,2,3,6,7,1,1,5,5,7,6], opacity=0.03, color='white'))
        # Boxy
        for b in packed:
            x,y,z,w,l,h = b['x'],b['y'],b['z'],b['w'],b['l'],b['h']
            fig.add_trace(go.Mesh3d(x=[x,x+w,x+w,x,x,x+w,x+w,x], y=[y,y,y+l,y+l,y,y,y+l,y+l], z=[z,z,z,z,z+h,z+h,z+h,z+h], i=[7,0,0,0,4,4,6,6,4,0,3,2], j=[3,4,1,2,5,6,5,2,0,1,6,3], k=[0,7,2,3,6,7,1,1,5,5,7,6], color='#8b5a2b', opacity=0.8, flatshading=True))
        
        fig.update_layout(scene=dict(aspectmode='data', bgcolor='black', xaxis=dict(visible=False), yaxis=dict(visible=False), zaxis=dict(visible=False)), paper_bgcolor='rgba(0,0,0,0)', margin=dict(l=0,r=0,b=0,t=0), height=600)
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("ZAWARTOŚĆ:")
    df = pd.DataFrame(st.session_state.cargo)
    st.table(df[['name', 'qty', 'itemsPerCase', 'canStack']])
else:
    st.info("Dodaj ładunek, aby zobaczyć analizę.")
