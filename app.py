import streamlit as st
import pandas as pd
import math
import plotly.graph_objects as go

# --- KONFIGURACJA STRONY ---
st.set_page_config(page_title="SQM Cargo Planner Pro 3D", layout="wide", page_icon="🚚")

# --- SYSTEM HASŁA ---
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False
    if not st.session_state["password_correct"]:
        st.title("🔐 SQM Multimedia Solutions")
        st.subheader("System Planowania Załadunków")
        pwd = st.text_input("Hasło dostępowe:", type="password")
        if st.button("Zaloguj"):
            if pwd == "NowyRozdzial":
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("❌ Błędne hasło")
        return False
    return True

if check_password():
    # --- BAZA POJAZDÓW (Zgodnie z Twoją specyfikacją) ---
    VEHICLES = {
        "FTL (Tir)": {"l": 1360, "w": 245, "h": 265, "weight": 12000, "pallets": 33},
        "Solówka 7m": {"l": 700, "w": 245, "h": 245, "weight": 3500, "pallets": 16},
        "Solówka 6m": {"l": 600, "w": 245, "h": 245, "weight": 3500, "pallets": 14},
        "BUS": {"l": 450, "w": 150, "h": 245, "weight": 1100, "pallets": 8},
    }

    # --- PEŁNA BAZA PRODUKTÓW SQM (Przeniesiona 1:1 z Twojego pliku HTML) ---
    PRODUCTS = {
        "17-23\" - plastic case": {"l": 80, "w": 60, "h": 20, "weight": 20.0, "ipc": 1, "stack": True},
        "24-32\" - plastic case": {"l": 60, "w": 40, "h": 20, "weight": 15.0, "ipc": 1, "stack": True},
        "32\" - triple - STANDARD": {"l": 90, "w": 50, "h": 70, "weight": 50.0, "ipc": 3, "stack": True},
        "43\" - triple - STANDARD": {"l": 112, "w": 42, "h": 80, "weight": 90.0, "ipc": 3, "stack": True},
        "45\"-55\" - double - STANDARD": {"l": 140, "w": 42, "h": 100, "weight": 150.0, "ipc": 2, "stack": True},
        "60-65\" - double - STANDARD": {"l": 160, "w": 40, "h": 230, "weight": 200.0, "ipc": 2, "stack": True},
        "75-86\" - double - STANDARD": {"l": 210, "w": 40, "h": 230, "weight": 230.0, "ipc": 2, "stack": True},
        "98\" - double - STANDARD": {"l": 250, "w": 70, "h": 230, "weight": 400.0, "ipc": 1, "stack": True},
        "NEC E326 - STANDARD": {"l": 70, "w": 50, "h": 70, "weight": 90.0, "ipc": 3, "stack": True},
        "NEC C431 - STANDARD": {"l": 80, "w": 50, "h": 80, "weight": 120.0, "ipc": 3, "stack": True},
        "NEC C501 - STANDARD": {"l": 100, "w": 50, "h": 100, "weight": 140.0, "ipc": 2, "stack": True},
        "NEC C551 - STANDARD": {"l": 100, "w": 50, "h": 100, "weight": 140.0, "ipc": 2, "stack": True},
        "SAMSUNG series 7 - STANDARD": {"l": 110, "w": 50, "h": 60, "weight": 160.0, "ipc": 2, "stack": True},
        "NEC C861 86\" - STANDARD": {"l": 140, "w": 40, "h": 230, "weight": 210.0, "ipc": 1, "stack": True},
        "NEC C981 98\" - STANDARD": {"l": 170, "w": 70, "h": 230, "weight": 250.0, "ipc": 1, "stack": True},
        "NEC X981 98\" TOUCHSCREEN - STANDARD": {"l": 170, "w": 70, "h": 230, "weight": 250.0, "ipc": 1, "stack": True},
        "iiYama 46\" - TOUCHSCREEN - STANDARD": {"l": 100, "w": 50, "h": 100, "weight": 140.0, "ipc": 2, "stack": True},
        "NEC V554 TOUCHSCREEN - STANDARD": {"l": 100, "w": 50, "h": 100, "weight": 140.0, "ipc": 2, "stack": True},
        "Samsung UE43 - STANDARD": {"l": 80, "w": 50, "h": 80, "weight": 120.0, "ipc": 3, "stack": True},
        "LG 60 UH605V - STANDARD": {"l": 110, "w": 40, "h": 230, "weight": 160.0, "ipc": 2, "stack": True},
        "LG 65 UJ620V - STANDARD": {"l": 110, "w": 40, "h": 230, "weight": 160.0, "ipc": 2, "stack": True},
        "LG 75\" - STANDARD": {"l": 140, "w": 40, "h": 230, "weight": 210.0, "ipc": 1, "stack": True},
        "MULTIMEDIA TOTEM 55\"": {"l": 100, "w": 60, "h": 210, "weight": 210.0, "ipc": 1, "stack": False},
        "MULTIMEDIA TOTEM 55\" 4K i5": {"l": 100, "w": 80, "h": 200, "weight": 150.0, "ipc": 1, "stack": False},
        "P1 lub 1.58 ABSEN": {"l": 108, "w": 71, "h": 62, "weight": 103.0, "ipc": 8, "stack": True},
        "P1.9 UNILUMIN UPAD IV / S-FLEX": {"l": 117, "w": 57, "h": 79, "weight": 115.0, "ipc": 8, "stack": True},
        "P2.6 UNILUMIN UPAD IV": {"l": 117, "w": 57, "h": 79, "weight": 116.0, "ipc": 8, "stack": True},
        "P2.6 UNILUMIN UPAD IV / C-CUBE": {"l": 117, "w": 57, "h": 79, "weight": 125.0, "ipc": 8, "stack": True},
        "P2.6 UNILUMIN UPAD IV / S-FLEX": {"l": 117, "w": 57, "h": 79, "weight": 121.0, "ipc": 8, "stack": True},
        "P2.06 frameLED (STANDARD / CORNERS)": {"l": 86, "w": 62, "h": 100, "weight": 118.0, "ipc": 10, "stack": True},
        "P2.06 frameLED (CURVED INNER / OUTER)": {"l": 84, "w": 64, "h": 100, "weight": 76.5, "ipc": 5, "stack": True},
        "P2 ESD 2,84 - STANDARD": {"l": 110, "w": 60, "h": 80, "weight": 115.0, "ipc": 8, "stack": True},
        "P2 ESD Corner - nonstandard": {"l": 90, "w": 70, "h": 80, "weight": 104.0, "ipc": 8, "stack": True},
        "P3.9 Yestech - STANDARD": {"l": 114, "w": 60, "h": 80, "weight": 125.0, "ipc": 10, "stack": True},
        "P2.6 Yestech - INDOOR": {"l": 117, "w": 64, "h": 76, "weight": 122.0, "ipc": 10, "stack": True},
        "P2.6 Yestech - INDOOR CUBE": {"l": 117, "w": 64, "h": 76, "weight": 122.0, "ipc": 10, "stack": True},
        "P3 Yestech Corner - nonstandard": {"l": 120, "w": 60, "h": 80, "weight": 113.0, "ipc": 12, "stack": True},
        "P2.9 Yestech FLOOR - STANDARD": {"l": 114, "w": 60, "h": 76, "weight": 142.0, "ipc": 10, "stack": True},
        "P3.9 HOXLED / TRANSPARENT": {"l": 114, "w": 80, "h": 130, "weight": 144.0, "ipc": 10, "stack": True},
        "P2.06 / frameLED / KABINET": {"l": 86, "w": 62, "h": 100, "weight": 118.0, "ipc": 10, "stack": True},
        "P1,86 LED MODULE": {"l": 32, "w": 16, "h": 2, "weight": 0.34, "ipc": 1, "stack": True},
        "P2.0 LED SPHERE / d=1,5m": {"l": 160, "w": 160, "h": 220, "weight": 120.0, "ipc": 1, "stack": False},
        "P3.0 LED SPHERE 1 z 5": {"l": 192, "w": 192, "h": 200, "weight": 400.0, "ipc": 1, "stack": False},
        "P3.0 LED SPHERE 2 z 5": {"l": 192, "w": 192, "h": 200, "weight": 400.0, "ipc": 1, "stack": False},
        "P3.0 LED SPHERE 3 z 5": {"l": 270, "w": 101, "h": 200, "weight": 400.0, "ipc": 1, "stack": False},
        "P3.0 LED SPHERE 4 z 5": {"l": 183, "w": 182, "h": 200, "weight": 400.0, "ipc": 1, "stack": False},
        "P3.0 LED SPHERE 5 z 5": {"l": 180, "w": 120, "h": 220, "weight": 400.0, "ipc": 1, "stack": False},
        "P1.56 LED (Stack max 2)": {"l": 120, "w": 60, "h": 90, "weight": 125.0, "ipc": 10, "stack": True},
        "P1,29 MODULED CABINET": {"l": 94, "w": 60, "h": 100, "weight": 121.0, "ipc": 8, "stack": True},
        "DICOLOR US-261": {"l": 117, "w": 58, "h": 110, "weight": 118.0, "ipc": 8, "stack": True},
        "DICOLOR US-390": {"l": 110, "w": 82, "h": 110, "weight": 87.0, "ipc": 6, "stack": True},
        "P1.9 KINETIC LED CABINET": {"l": 120, "w": 63, "h": 65, "weight": 95.0, "ipc": 2, "stack": True},
        "P2.9 OUTDOOR RENTAL": {"l": 120, "w": 60, "h": 80, "weight": 120.0, "ipc": 9, "stack": True},
        "case for accessories RED": {"l": 120, "w": 60, "h": 80, "weight": 120.0, "ipc": 5, "stack": True},
        "case for accessories ARUM": {"l": 120, "w": 70, "h": 120, "weight": 140.0, "ipc": 1, "stack": True},
        "case for accessories NEC": {"l": 100, "w": 50, "h": 80, "weight": 120.0, "ipc": 3, "stack": True},
        "ELSTAR L42 LED": {"l": 80, "w": 50, "h": 50, "weight": 37.0, "ipc": 5, "stack": True},
        "CAMEO PAR 64 LED": {"l": 80, "w": 50, "h": 60, "weight": 31.0, "ipc": 6, "stack": True},
        "FLASH PAR 64 LED": {"l": 80, "w": 50, "h": 60, "weight": 47.0, "ipc": 8, "stack": True},
        "PROLIGHTS / ECLEXPO FLOOD300W": {"l": 120, "w": 70, "h": 90, "weight": 89.5, "ipc": 5, "stack": True},
        "PROLIGHTS / ASTRA HYBRID 330": {"l": 120, "w": 60, "h": 100, "weight": 120.0, "ipc": 2, "stack": True},
        "GRANDMA 2 LIGHTING": {"l": 100, "w": 81, "h": 37, "weight": 20.0, "ipc": 1, "stack": True},
        "PROLIGHTS / JET SPOT4Z": {"l": 110, "w": 60, "h": 130, "weight": 130.0, "ipc": 10, "stack": True},
        "PROLIGHTS / JET WASH19": {"l": 120, "w": 60, "h": 123, "weight": 123.0, "ipc": 8, "stack": True},
        "PROLIGHTS / SOLAR 27Q": {"l": 120, "w": 70, "h": 113, "weight": 113.0, "ipc": 10, "stack": True},
        "PROLIGHTS / STUDIO COB FC 150W": {"l": 140, "w": 60, "h": 95.4, "weight": 95.4, "ipc": 5, "stack": True},
        "CHAINMASTER / D8 PLUS / 320KG": {"l": 90, "w": 70, "h": 97, "weight": 97.0, "ipc": 2, "stack": True},
        "CHAINMASTER / D8 PLUS / 500KG": {"l": 90, "w": 70, "h": 98, "weight": 98.0, "ipc": 3, "stack": True},
        "MANUAL CHAIN HOIST": {"l": 30, "w": 30, "h": 40, "weight": 40.0, "ipc": 2, "stack": True},
        "speaker RCF 310": {"l": 60, "w": 40, "h": 40, "weight": 40.0, "ipc": 3, "stack": True},
        "speaker MASK 6": {"l": 40, "w": 30, "h": 60, "weight": 60.0, "ipc": 4, "stack": True},
        "truss cart 14x2 (200x70)": {"l": 200, "w": 70, "h": 350, "weight": 350.0, "ipc": 1, "stack": False},
        "truss cart 14x2 (300x70)": {"l": 300, "w": 70, "h": 350, "weight": 350.0, "ipc": 1, "stack": False},
        "truss corner": {"l": 40, "w": 40, "h": 40, "weight": 40.0, "ipc": 1, "stack": True},
        "Boxer Projector": {"l": 110, "w": 60, "h": 185, "weight": 185.0, "ipc": 1, "stack": False},
        "trap/ramp for van": {"l": 240, "w": 10, "h": 100, "weight": 240.0, "ipc": 1, "stack": False},
        "ALUSTAGE / AL34 / FD / 0,21M": {"l": 21, "w": 30, "h": 30, "weight": 3.0, "ipc": 1, "stack": True},
        "ALUSTAGE / AL34 / FD / 0,5M": {"l": 50, "w": 30, "h": 30, "weight": 4.0, "ipc": 1, "stack": True},
        "ALUSTAGE / AL34 / FD / 1M": {"l": 100, "w": 30, "h": 30, "weight": 6.0, "ipc": 1, "stack": True},
        "ALUSTAGE / AL34 / FD / 2M": {"l": 200, "w": 30, "h": 30, "weight": 11.0, "ipc": 1, "stack": True},
        "ALUSTAGE / AL34 / FD / 3M": {"l": 300, "w": 30, "h": 30, "weight": 16.0, "ipc": 1, "stack": True},
        "EUROTRUSS / HD34 / 0,5M": {"l": 50, "w": 29, "h": 29, "weight": 18.0, "ipc": 1, "stack": True},
        "EUROTRUSS / HD34 / 1M": {"l": 100, "w": 29, "h": 29, "weight": 18.0, "ipc": 1, "stack": True},
        "EUROTRUSS / HD34 / 2M": {"l": 200, "w": 29, "h": 29, "weight": 18.0, "ipc": 1, "stack": True},
        "EUROTRUSS / HD34 / 3M": {"l": 300, "w": 29, "h": 29, "weight": 18.0, "ipc": 1, "stack": True},
        "TRUSS x HANGED CIRCLE Ø5m": {"l": 300, "w": 80, "h": 170, "weight": 128.0, "ipc": 1, "stack": False},
        "TRUSS x HANGED CIRCLE Ø6m": {"l": 300, "w": 80, "h": 210, "weight": 140.0, "ipc": 1, "stack": False},
        "PODEST ALUDECK LIGHT 2 x 1M": {"l": 200, "w": 100, "h": 20, "weight": 45.0, "ipc": 1, "stack": True},
        "ALUMINIUM BLACK PIPE 4M": {"l": 400, "w": 6, "h": 6, "weight": 6.0, "ipc": 1, "stack": True},
        "ALUMINIUM BLACK PIPE 6M": {"l": 600, "w": 6, "h": 6, "weight": 9.0, "ipc": 1, "stack": True},
        "KINETIC Q / WINCH DMX": {"l": 110, "w": 56, "h": 70, "weight": 40.0, "ipc": 16, "stack": True},
        "POWERBOX RACK 63A": {"l": 71, "w": 55, "h": 70, "weight": 50.0, "ipc": 1, "stack": True},
        "LD SYSTEMS STINGER / 8 G3": {"l": 120, "w": 40, "h": 80, "weight": 85.0, "ipc": 4, "stack": True},
        "TRUSS CIRCLE HD D=6M": {"l": 240, "w": 60, "h": 220, "weight": 85.0, "ipc": 1, "stack": True},
        "TRUSS CIRCLE HD D=4M": {"l": 300, "w": 60, "h": 160, "weight": 85.0, "ipc": 1, "stack": True},
        "ALUSTAGE / AL31 / UNO / 1M": {"l": 100, "w": 5, "h": 5, "weight": 2.0, "ipc": 1, "stack": True},
        "ALUSTAGE / AL31 / UNO / 2M": {"l": 200, "w": 5, "h": 5, "weight": 4.0, "ipc": 1, "stack": True},
        "ALUSTAGE / AL32 / DUO / 2M": {"l": 200, "w": 5, "h": 30, "weight": 5.0, "ipc": 1, "stack": True},
        "Własny ładunek": {"l": 120, "w": 80, "h": 100, "weight": 100.0, "ipc": 1, "stack": True},
    }

    # --- FUNKCJA RYSOWANIA 3D ---
    def add_box(fig, x, y, z, l, w, h, name, color):
        gap = 0.5 
        l_g, w_g, h_g = l-gap, w-gap, h-gap
        x_c = [x, x+l_g, x+l_g, x, x, x+l_g, x+l_g, x]
        y_c = [y, y, y+w_g, y+w_g, y, y, y+w_g, y+w_g]
        z_c = [z, z, z, z, z+h_g, z+h_g, z+h_g, z+h_g]
        fig.add_trace(go.Mesh3d(
            x=x_c, y=y_c, z=z_c,
            i=[7,0,0,0,4,4,6,6,4,0,3,2], j=[3,4,1,2,5,6,5,2,0,1,6,3], k=[0,7,2,3,6,7,1,1,5,5,7,6],
            color=color, opacity=0.9, flatshading=True, name=name, hoverinfo="text",
            text=f"Produkt: {name}<br>Poziom Z: {z} cm"
        ))

    # --- ALGORYTM PAKOWANIA (Z UWZGLĘDNIENIEM LIMITÓW) ---
    def pack_cargo(cargo_list, v):
        to_pack = []
        for c in cargo_list:
            num = math.ceil(c['qty'] / c['ipc'])
            for _ in range(num):
                to_pack.append(c)
        
        to_pack.sort(key=lambda x: x['l']*x['w'], reverse=True)
        
        placed_stacks = []
        unplaced = []
        curr_x, curr_y, max_y_in_row = 0, 0, 0
        total_weight = 0
        
        for item in to_pack:
            # Sprawdzenie czy pojedynczy przedmiot mieści się w ogóle
            if item['h'] > v['h'] or (item['l'] > v['l'] and item['w'] > v['l']):
                unplaced.append(item)
                continue

            packed = False
            # 1. Próba dołożenia na istniejący stos (Stacking)
            if item.get('stack', True):
                for s in placed_stacks:
                    if (item['l'] <= s['l'] and item['w'] <= s['w']) or (item['w'] <= s['l'] and item['l'] <= s['w']):
                        if (s['cur_h'] + item['h']) <= v['h'] and (total_weight + item['weight']) <= v['weight']:
                            s['items'].append(item)
                            s['cur_h'] += item['h']
                            total_weight += item['weight']
                            packed = True
                            break
            
            # 2. Nowy stos na podłodze
            if not packed:
                for l_r, w_r in [(item['l'], item['w']), (item['w'], item['l'])]:
                    if curr_x + l_r <= v['l'] and curr_y + w_r <= v['w']:
                        if (total_weight + item['weight']) <= v['weight']:
                            placed_stacks.append({
                                'x': curr_x, 'y': curr_y, 'l': l_r, 'w': w_r,
                                'cur_h': item['h'], 'items': [item]
                            })
                            total_weight += item['weight']
                            max_y_in_row = max(max_y_in_row, w_r)
                            curr_x += l_r
                            packed = True
                            break
                
                # Nowa linia (jeśli się nie zmieściło w rzędzie)
                if not packed:
                    new_y = curr_y + max_y_in_row
                    if new_y + item['w'] <= v['w'] and item['l'] <= v['l']:
                        if (total_weight + item['weight']) <= v['weight']:
                            curr_x = 0
                            curr_y = new_y
                            placed_stacks.append({
                                'x': curr_x, 'y': curr_y, 'l': item['l'], 'w': item['w'],
                                'cur_h': item['h'], 'items': [item]
                            })
                            total_weight += item['weight']
                            max_y_in_row = item['w']
                            curr_x += item['l']
                            packed = True

            if not packed:
                unplaced.append(item)
        
        return placed_stacks, unplaced, total_weight

    # --- INTERFEJS UŻYTKOWNIKA ---
    st.title("🚚 SQM Cargo Planner Pro 3D")
    
    if 'cargo' not in st.session_state:
        st.session_state.cargo = []

    c1, c2 = st.columns([1, 2])
    
    with c1:
        st.subheader("Parametry Transportu")
        v_name = st.selectbox("Wybierz Pojazd", list(VEHICLES.keys()))
        v = VEHICLES[v_name]
        
        st.divider()
        st.subheader("Dodaj Sprzęt")
        search = st.text_input("🔍 Szukaj w bazie (np. P2.6, 98\", Truss)...")
        
        filtered_products = [k for k in PRODUCTS.keys() if search.lower() in k.lower()]
        sel = st.selectbox("Wyniki wyszukiwania:", sorted(filtered_products) if filtered_products else sorted(PRODUCTS.keys()))
        
        if st.button("➕ Dodaj do Listy"):
            it = PRODUCTS[sel].copy()
            it['name'] = sel
            it['qty'] = 1
            st.session_state.cargo.append(it)
            st.toast(f"Dodano: {sel}")
            
        st.divider()
        st.subheader("Twoja Lista Załadunkowa")
        for idx, it in enumerate(st.session_state.cargo):
            with st.expander(f"{it['name']} (x{it['qty']})"):
                it['qty'] = st.number_input("Ilość sztuk", 1, 500, it['qty'], key=f"q_{idx}")
                if st.button("Usuń", key=f"r_{idx}"):
                    st.session_state.cargo.pop(idx)
                    st.rerun()

    with c2:
        if st.session_state.cargo:
            stacks, unplaced, total_w = pack_cargo(st.session_state.cargo, v)
            
            # Wskaźniki
            m1, m2, m3 = st.columns(3)
            m1.metric("Waga całkowita", f"{round(total_w,1)} kg", f"Limit: {v['weight']} kg", delta_color="inverse")
            
            occ_area = sum(s['l'] * s['w'] for s in stacks)
            m2.metric("Zajęte m²", f"{round(occ_area/10000, 2)} m²", f"Z {round((v['l']*v['w'])/10000, 1)}")
            
            p_eq = round(occ_area / (120*80), 1)
            m3.metric("Miejsca Paletowe", f"~{p_eq}", f"Limit: {v['pallets']}")

            # Wizualizacja 3D
            fig = go.Figure()
            
            # Kontur pojazdu
            fig.add_trace(go.Scatter3d(
                x=[0, v['l'], v['l'], 0, 0, 0, v['l'], v['l'], 0, 0],
                y=[0, 0, v['w'], v['w'], 0, 0, 0, v['w'], v['w'], 0],
                z=[0, 0, 0, 0, 0, v['h'], v['h'], v['h'], v['h'], v['h']],
                mode='lines', line=dict(color='black', width=4), name='Pojazd'
            ))

            colors = ['#EF553B', '#00CC96', '#636EFA', '#AB63FA', '#FFA15A', '#19D3F3', '#FF6692']
            
            for i, s in enumerate(stacks):
                z_ptr = 0
                for item in s['items']:
                    add_box(fig, s['x'], s['y'], z_ptr, s['l'], s['w'], item['h'], item['name'], colors[i % len(colors)])
                    z_ptr += item['h']

            fig.update_layout(
                scene=dict(
                    xaxis_title='Długość (cm)',
                    yaxis_title='Szerokość (cm)',
                    zaxis_title='Wysokość (cm)',
                    aspectmode='data'
                ),
                margin=dict(l=0, r=0, b=0, t=0),
                height=700
            )
            st.plotly_chart(fig, use_container_width=True)
            
            if unplaced:
                st.warning(f"⚠️ Nie zmieszczono {len(unplaced)} elementów! (Przekroczenie wagi, wymiarów lub brak miejsca na podłodze)")
                with st.expander("Lista niezmieszczonych produktów"):
                    for up in unplaced:
                        st.write(f"- {up['name']}")
        else:
            st.info("Dodaj produkty z lewego panelu, aby zobaczyć wizualizację załadunku.")

    if st.sidebar.button("Wyloguj"):
        st.session_state["password_correct"] = False
        st.rerun()
