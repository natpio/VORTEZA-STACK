import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import math

# --- KONFIGURACJA ---
st.set_page_config(page_title="VORTEZA RECOVERY PRO", layout="wide")

# Funkcja czyszcząca sesję, aby uniknąć konfliktów ze starymi wersjami kodu
if 'init_fix' not in st.session_state:
    st.session_state.clear()
    st.session_state.init_fix = True
    st.session_state.manifest = []

# --- SILNIK LOGISTYCZNY (SŁOWNIKOWY - ZERO KLAS) ---
def calculate_packing(raw_manifest, vw, vh):
    items_to_pack = []
    # Rozbijamy manifest na pojedyncze jednostki transportowe
    for item in raw_manifest:
        # Bezpieczne pobieranie danych ze słownika
        qty = item.get('qty', 1)
        name = item.get('name', 'N/A')
        w, l, h = item.get('w', 80), item.get('l', 120), item.get('h', 100)
        can_stack = item.get('stack', True)
        
        for _ in range(qty):
            items_to_pack.append({'name': name, 'w': w, 'l': l, 'h': h, 'stack': can_stack})

    # Sortowanie: największa podstawa na dół
    items_to_pack.sort(key=lambda x: x['w'] * x['l'], reverse=True)
    
    packed_results = []
    y_offset = 0.0
    
    while items_to_pack:
        # Bierzemy pierwszy element jako lidera rzędu
        leader = items_to_pack.pop(0)
        lw, ll, lh = leader['w'], leader['l'], leader['h']
        
        # Prosta rotacja dla LDM
        if lw < ll and ll <= vw:
            lw, ll = ll, lw
            
        # Obliczamy pionowy stos (Double/Triple Stacking)
        max_in_stack = math.floor(vh / lh) if leader['stack'] else 1
        current_stack_count = 1
        
        # Szukamy takich samych przedmiotów do wypełnienia pionu
        i = 0
        while i < len(items_to_pack) and current_stack_count < max_in_stack:
            if items_to_pack[i]['name'] == leader['name']:
                items_to_pack.pop(i)
                current_stack_count += 1
            else:
                i += 1
        
        # Zapisujemy stos w wynikach
        for s_idx in range(current_stack_count):
            packed_results.append({
                'n': leader['name'], 'x': 0, 'y': y_offset, 'z': s_idx * lh,
                'w': lw, 'l': ll, 'h': lh, 'color': '#d2a679'
            })
            
        # Side-filling: Czy coś wejdzie obok tego stosu w tym samym rzędzie?
        remaining_width = vw - lw
        current_row_length = ll
        
        j = 0
        while j < len(items_to_pack) and remaining_width > 10:
            cand = items_to_pack[j]
            cw, cl, ch = cand['w'], cand['l'], cand['h']
            
            # Próba dopasowania (z rotacją)
            can_fit = False
            if cw <= remaining_width and cl <= current_row_length:
                can_fit = True
            elif cl <= remaining_width and cw <= current_row_length:
                cw, cl = cl, cw
                can_fit = True
                
            if can_fit:
                # Tutaj też sprawdzamy stacking dla bocznego rzędu
                c_max_stack = math.floor(vh / ch) if cand['stack'] else 1
                c_current_stack = 1
                items_to_pack.pop(j)
                
                k = 0
                while k < len(items_to_pack) and c_current_stack < c_max_stack:
                    if items_to_pack[k]['name'] == cand['name']:
                        items_to_pack.pop(k)
                        c_current_stack += 1
                    else:
                        k += 1
                
                for cs_idx in range(c_current_stack):
                    packed_results.append({
                        'n': cand['name'], 'x': vw - remaining_width, 'y': y_offset, 
                        'z': cs_idx * ch, 'w': cw, 'l': cl, 'h': ch, 'color': '#a88664'
                    })
                remaining_width -= cw
            else:
                j += 1
                
        y_offset += current_row_length
        
    return packed_results, y_offset

# --- INTERFEJS ---
st.title("🛡️ VORTEZA STACK - EMERGENCY RECOVERY")

with st.sidebar:
    st.header("KONTROLA ŁADUNKU")
    if st.button("DODAJ 50x TV 55\" (TEST)"):
        st.session_state.manifest.append({
            'name': 'TV 55"', 'w': 140, 'l': 20, 'h': 85, 'qty': 50, 'stack': True
        })
    
    if st.button("WYCZYŚĆ WSZYSTKO"):
        st.session_state.manifest = []
        st.rerun()

# Główna logika
if st.session_state.manifest:
    # Parametry naczepy
    VW, VL, VH = 245, 1360, 265
    
    packed_data, total_ldm = calculate_packing(st.session_state.manifest, VW, VH)
    
    col1, col2 = st.columns(2)
    col1.metric("Łączny LDM", f"{round(total_ldm/100, 2)} m")
    col2.metric("Sztuk na naczepie", len(packed_data))

    # Wizualizacja 3D
    fig = go.Figure()
    # Naczepa
    fig.add_trace(go.Mesh3d(x=[0,VW,VW,0,0,VW,VW,0], y=[0,0,total_ldm,total_ldm,0,0,total_ldm,total_ldm], z=[0,0,0,0,VH,VH,VH,VH], opacity=0.05, color='white'))
    
    # Produkty
    for p in packed_data:
        x, y, z, w, l, h = p['x'], p['y'], p['z'], p['w'], p['l'], p['h']
        fig.add_trace(go.Mesh3d(
            x=[x, x+w, x+w, x, x, x+w, x+w, x],
            y=[y, y, y+l, y+l, y, y, y+l, y+l],
            z=[z, z, z, z, z+h, z+h, z+h, z+h],
            i=[7,0,0,0,4,4,6,6,4,0,3,2], j=[3,4,1,2,5,6,5,2,0,1,6,3], k=[0,7,2,3,6,7,1,1,5,5,7,6],
            color=p['color'], opacity=0.8, flatshading=True, name=p['n']
        ))

    fig.update_layout(scene=dict(aspectmode='data', bgcolor='black', xaxis_visible=False, yaxis_visible=False, zaxis_visible=False), margin=dict(l=0,r=0,b=0,t=0), height=700)
    st.plotly_chart(fig, use_container_width=True)
    
    st.write("### Surowe dane manifestu (Debug):")
    st.write(st.session_state.manifest)
else:
    st.info("Dodaj testowe TV lub własne dane w sidebarze.")
