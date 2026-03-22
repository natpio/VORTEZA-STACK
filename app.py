import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import json
import os
import math

# --- KONFIGURACJA STRONY ---
st.set_page_config(
    page_title="VORTEZA SYSTEM - STACK PRO",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM CSS (Dla zachowania wyglądu ze screenów) ---
st.markdown("""
    <style>
    [data-testid="stSidebar"] { background-color: #0d1117; border-right: 1px solid #30363d; }
    .main { background-color: #0e1117; }
    .stMetric { 
        background-color: #000000; 
        border: 1px solid #30363d; 
        padding: 20px; 
        border-radius: 5px;
        color: white;
    }
    div[data-testid="stMetricValue"] { color: #ffffff; font-size: 32px; font-weight: bold; }
    .stButton>button { width: 100%; background-color: transparent; border: 1px solid #ff4b4b; color: white; }
    .stButton>button:hover { background-color: #ff4b4b; color: white; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNKCJE POMOCNICZE ---
def load_products():
    """Wczytuje bazę produktów z pliku JSON."""
    if os.path.exists("products.json"):
        try:
            with open("products.json", "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            st.error(f"Błąd ładowania bazy: {e}")
            return []
    return []

# --- ALGORYTM PAKOWANIA (Z DOPYCHANIEM BOCZNYM) ---
def pack_logic_advanced(cargo_list, v_w=245, v_l=1360, v_h=265):
    """
    Główny silnik obliczeniowy. 
    1. Rozbija pakiety na pojedyncze opakowania (boxy).
    2. Sortuje od największej podstawy.
    3. Wypełnia rzędy, szukając mniejszych przedmiotów do bocznych luk.
    """
    all_boxes_to_pack = []
    for item in cargo_list:
        # Obliczanie liczby opakowań (ceil)
        num_cases = math.ceil(item['qty'] / item['itemsPerCase'])
        for _ in range(num_cases):
            all_boxes_to_pack.append({
                'name': item['name'],
                'w': item['width'],
                'l': item['length'],
                'h': item['height'],
                'weight': item['weight'],
                'canStack': item.get('canStack', True)
            })

    # Sortowanie: Powierzchnia (W*L) malejąco
    all_boxes_to_pack.sort(key=lambda x: x['w'] * x['l'], reverse=True)
    
    packed_results = []
    current_y = 0  # Postęp wzdłuż naczepy (LDM)
    
    remaining = all_boxes_to_pack.copy()

    while remaining:
        # 1. Pobierz "lidera" rzędu (największy pozostały)
        leader = remaining.pop(0)
        
        # Orientacja lidera: dłuższy bok wzdłuż szerokości (X), jeśli wejdzie
        lw, ll, lh = leader['w'], leader['l'], leader['h']
        if lw < ll and ll <= v_w:
            lw, ll = ll, lw
        
        # Stacking dla lidera
        leader_stack = math.floor(v_h / lh) if leader['canStack'] else 1
        
        # Dodaj lidera do wyników
        for s in range(leader_stack):
            packed_results.append({
                'name': leader['name'],
                'x': 0, 'y': current_y, 'z': s * lh,
                'w': lw, 'l': ll, 'h': lh
            })
        
        row_width_filled = lw
        row_max_l = ll # Ten wymiar definiuje skok LDM dla całego rzędu
        
        # 2. PRÓBA DOPCHANIA BOKU (Side-Filling)
        # Przeszukujemy resztę listy w poszukiwaniu "zapychaczy"
        idx = 0
        while idx < len(remaining):
            candidate = remaining[idx]
            cw, cl, ch = candidate['w'], candidate['l'], candidate['h']
            
            fit = False
            # Opcja A: Standard
            if (row_width_filled + cw <= v_w) and (cl <= row_max_l):
                fit = True
            # Opcja B: Po rotacji
            elif (row_width_filled + cl <= v_w) and (cw <= row_max_l):
                cw, cl = cl, cw
                fit = True
            
            if fit:
                # Oblicz stacking dla zapychacza
                c_stack = math.floor(v_h / ch) if candidate['canStack'] else 1
                for s in range(c_stack):
                    packed_results.append({
                        'name': candidate['name'],
                        'x': row_width_filled, 'y': current_y, 'z': s * ch,
                        'w': cw, 'l': cl, 'h': ch
                    })
                row_width_filled += cw
                remaining.pop(idx) # Usuwamy z listy do spakowania
                # Nie zwiększamy idx, bo lista się przesunęła
            else:
                idx += 1
        
        # Przesunięcie LDM po skończeniu rzędu
        current_y += row_max_l

    return packed_results, current_y

# --- FUNKCJA RYSOWANIA 3D ---
def create_3d_viz(packed_items, v_w, v_l, v_h):
    fig = go.Figure()

    # Kontur naczepy
    fig.add_trace(go.Mesh3d(
        x=[0, v_w, v_w, 0, 0, v_w, v_w, 0],
        y=[0, 0, v_l, v_l, 0, 0, v_l, v_l],
        z=[0, 0, 0, 0, v_h, v_h, v_h, v_h],
        i=[7, 0, 0, 0, 4, 4, 6, 6, 4, 0, 3, 2],
        j=[3, 4, 1, 2, 5, 6, 5, 2, 0, 1, 6, 3],
        k=[0, 7, 2, 3, 6, 7, 1, 1, 5, 5, 7, 6],
        opacity=0.05, color='white', showlegend=False
    ))

    # Rysowanie skrzyń
    for item in packed_items:
        x, y, z = item['x'], item['y'], item['z']
        w, l, h = item['w'], item['l'], item['h']
        
        fig.add_trace(go.Mesh3d(
            x=[x, x+w, x+w, x, x, x+w, x+w, x],
            y=[y, y, y+l, y+l, y, y, y+l, y+l],
            z=[z, z, z, z, z+h, z+h, z+h, z+h],
            i=[7, 0, 0, 0, 4, 4, 6, 6, 4, 0, 3, 2],
            j=[3, 4, 1, 2, 5, 6, 5, 2, 0, 1, 6, 3],
            k=[0, 7, 2, 3, 6, 7, 1, 1, 5, 5, 7, 6],
            color='#d2a679', opacity=0.9, flatshading=True,
            text=f"Produkt: {item['name']}<br>Wymiary: {w}x{l}x{h}",
            hoverinfo="text"
        ))

    fig.update_layout(
        scene=dict(
            aspectmode='data',
            xaxis=dict(gridcolor='rgb(50,50,50)', zerolinecolor='rgb(50,50,50)'),
            yaxis=dict(gridcolor='rgb(50,50,50)', zerolinecolor='rgb(50,50,50)'),
            zaxis=dict(gridcolor='rgb(50,50,50)', zerolinecolor='rgb(50,50,50)'),
            bgcolor='black'
        ),
        margin=dict(l=0, r=0, b=0, t=0),
        paper_bgcolor='black',
        plot_bgcolor='black'
    )
    return fig

# --- APLIKACJA ---
def main():
    # Inicjalizacja ładunku
    if 'cargo_list' not in st.session_state:
        st.session_state.cargo_list = []

    # SIDEBAR
    with st.sidebar:
        st.image("https://vorteza.com/wp-content/uploads/2023/06/vorteza_logo_white.png", width=200) # Opcjonalne logo
        
        st.header("1. POJAZD")
        v_type = st.selectbox("TYP:", ["FTL (Tir)", "Solo (8m)", "Bus (4m)"])
        v_map = {
            "FTL (Tir)": (245, 1360, 265, 24000),
            "Solo (8m)": (245, 800, 250, 12000),
            "Bus (4m)": (170, 400, 180, 1200)
        }
        v_w, v_l, v_h, v_max_w = v_map[v_type]

        st.header("2. DODAJ ŁADUNEK")
        tab_db, tab_custom = st.tabs(["Z BAZY", "WŁASNY"])

        products = load_products()
        
        with tab_db:
            if products:
                p_names = [p['name'] for p in products]
                sel_name = st.selectbox("PRODUKT:", p_names)
                sel_qty = st.number_input("SZTUK:", min_value=1, value=1, key="db_qty")
                if st.button("DODAJ PRODUKT"):
                    p_data = next(p for p in products if p['name'] == sel_name)
                    st.session_state.cargo_list.append({**p_data, 'qty': sel_qty})
            else:
                st.warning("Brak pliku products.json")

        with tab_custom:
            c_name = st.text_input("NAZWA:", "luzny box")
            c_w = st.number_input("SZER (cm):", value=60)
            c_l = st.number_input("DŁ (cm):", value=40)
            c_h = st.number_input("WYS (cm):", value=100)
            c_wg = st.number_input("WAGA (kg):", value=100)
            c_qty = st.number_input("SZTUK ŁĄCZNIE:", value=10)
            c_ipc = st.number_input("SZT/OPAKOWANIE:", value=1)
            c_stack = st.checkbox("MOŻNA STACKOWAĆ?", value=True)
            if st.button("DODAJ WŁASNY"):
                st.session_state.cargo_list.append({
                    "name": c_name, "width": c_w, "length": c_l, "height": c_h,
                    "weight": c_wg, "canStack": c_stack, "itemsPerCase": c_ipc, "qty": c_qty
                })

        if st.button("WYCZYŚĆ WSZYSTKO"):
            st.session_state.cargo_list = []
            st.rerun()

    # PANEL GŁÓWNY
    if st.session_state.cargo_list:
        # Obliczenia algorytmem Side-Filling
        packed_items, total_ldm_cm = pack_logic_advanced(st.session_state.cargo_list, v_w, v_l, v_h)
        
        # Statystyki (Górny rząd)
        st.subheader("STATYSTYKI")
        m1, m2, m3 = st.columns(3)
        
        ldm_m = round(total_ldm_cm / 100, 2)
        ep_count = round((total_ldm_cm / 100) * 2.4, 1)
        total_weight = sum(item['weight'] * math.ceil(item['qty']/item['itemsPerCase']) for item in st.session_state.cargo_list)
        
        m1.metric("METRY BIEŻĄCE (LDM)", f"{ldm_m} m")
        m2.metric("ZAJĘTE EP (SZAC.)", f"{ep_count} / 33")
        m3.metric("WAGA", f"{total_weight} / {v_max_w} kg")

        # Wizualizacja 3D
        st.plotly_chart(create_3d_viz(packed_items, v_w, total_ldm_cm + 100, v_h), use_container_width=True)

        # Tabela zawartości
        st.subheader("ZAWARTOŚĆ:")
        df = pd.DataFrame(st.session_state.cargo_list)
        # Obliczanie liczby opakowań do wyświetlenia w tabeli
        df['OPAKOWANIA'] = df.apply(lambda x: math.ceil(x['qty'] / x['itemsPerCase']), axis=1)
        st.table(df[['name', 'qty', 'itemsPerCase', 'OPAKOWANIA', 'canStack']])
        
    else:
        st.title("VORTEZA STACK")
        st.info("System gotowy. Dodaj elementy ładunku w panelu bocznym, aby wyliczyć optymalne ułożenie.")

if __name__ == "__main__":
    main()
