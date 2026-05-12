import streamlit as st
import streamlit.components.v1 as components
import json
import os
import random
import copy
import warnings
from music21 import *

warnings.filterwarnings("ignore")

# --- CONFIGURACIÓ ---
st.set_page_config(page_title="Generador de Funk", layout="wide")
st.title("🎸 Generador de Funk")

# --- INICIALITZACIÓ COMPLETA DE L'ESTAT ---
variables_estat = ['xml_data', 'score_generat', 'tonalitat', 'variacio_nom']
for var in variables_estat:
    if var not in st.session_state:
        st.session_state[var] = None if var != 'score_generat' else False
        if var == 'variacio_nom': st.session_state[var] = ""

FITXER_BASE = 'patrons funk.xml' # Prioritzem el format .xml que tens pujat
if not os.path.exists(FITXER_BASE):
    if os.path.exists('patrons funk.musicxml'):
        FITXER_BASE = 'patrons funk.musicxml'
    else:
        st.error(f"⚠️ No s'ha trobat el fitxer base.")
        st.stop()

# --- LÒGICA HARMÒNICA ---

def obtenir_tonalitat_aleatoria():
    opcions = [('C', 10), ('G', 8), ('F', 8), ('D', 6), ('Bb', 6), ('A', 4), ('Eb', 4)]
    tonalitats, pesos = zip(*opcions)
    return random.choices(tonalitats, weights=pesos, k=1)[0]

def ajustar_a_menor(measure, root_pitch):
    """Baixa la 3a un semitó per convertir dominant en menor."""
    for el in measure.flatten().notes:
        pitches = el.pitches if el.isChord else [el.pitch]
        for p in pitches:
            if (p.pitchClass - root_pitch.pitchClass) % 12 == 4:
                p.transpose(-1, inPlace=True)

def generar_estudi_final():
    score_in = converter.parse(FITXER_BASE)
    parts_in = list(score_in.parts)
    patrons_dreta, patrons_esquerra = [], []

    # 1. Extracció robusta de mans (Doble pista o Staff ID)
    if len(parts_in) >= 2:
        # Cas 1: El fitxer té dues mans en pistes separades
        mesures_d = list(parts_in[0].getElementsByClass(stream.Measure))
        mesures_e = list(parts_in[1].getElementsByClass(stream.Measure))
        for md, me in zip(mesures_d, mesures_e):
            patrons_dreta.append(copy.deepcopy(md))
            patrons_esquerra.append(copy.deepcopy(me))
    else:
        # Cas 2: Tot en una pista, detectem per atribut 'staff'
        for m in parts_in[0].getElementsByClass(stream.Measure):
            m_rh, m_lh = stream.Measure(), stream.Measure()
            for n in m.flatten().notesAndRests:
                staff_val = getattr(n, 'staff', 1)
                if staff_val is None and n.isChord:
                    try: staff_val = n.notes[0].staff
                    except: staff_val = 1
                
                if staff_val == 2: m_lh.insert(n.offset, copy.deepcopy(n))
                else: m_rh.insert(n.offset, copy.deepcopy(n))
            patrons_dreta.append(m_rh); patrons_esquerra.append(m_lh)

    # 2. Selecció de tonalitats
    v7_root_name = obtenir_tonalitat_aleatoria()
    v7_root = pitch.Pitch(v7_root_name)
    
    tipus_var = random.choice(['VI', 'bVI7', 'I7'])
    if tipus_var == 'VI':
        var_root = v7_root.transpose('M2')
        var_nom = f"{var_root.name}m7"
        is_minor = True
    elif tipus_var == 'bVI7':
        var_root = v7_root.transpose('m2')
        var_nom = f"{var_root.name}7"
        is_minor = False
    else: # I7
        var_root = v7_root.transpose('P4')
        var_nom = f"{var_root.name}7"
        is_minor = False

    # Armadura fixa (Mixolídia del V7 inicial)
    armadura_inicial = key.KeySignature(key.Key(v7_root.transpose('P4').name).sharps)

    # 3. Muntatge
    score_out = stream.Score()
    p_d, p_e = stream.Part(), stream.Part()
    
    idx_A = random.randint(0, len(patrons_dreta) - 1)
    idx_B = random.randint(0, len(patrons_dreta) - 1)
    
    for i in range(4):
        idx = idx_A if i < 2 else idx_B
        c_d = copy.deepcopy(patrons_dreta[idx])
        c_e = copy.deepcopy(patrons_esquerra[idx])
        c_d.number = c_e.number = i + 1
        
        # Neteja de signatures del fitxer base
        for cl in ['KeySignature', 'TimeSignature', 'Clef', 'SystemLayout']:
            c_d.removeByClass(cl); c_e.removeByClass(cl)
        
        # Transport a l'acord base (V7)
        itvl_base = interval.Interval(pitch.Pitch('C'), v7_root)
        c_d.transpose(itvl_base, inPlace=True); c_e.transpose(itvl_base, inPlace=True)

        # Si és compàs parell, apliquem la variació harmònica
        if i % 2 != 0:
            itvl_var = interval.Interval(v7_root, var_root)
            c_d.transpose(itvl_var, inPlace=True); c_e.transpose(itvl_var, inPlace=True)
            if is_minor:
                ajustar_a_menor(c_d, var_root); ajustar_a_menor(c_e, var_root)

        # Inserim armadura, clau i compàs només al primer compàs (sense canvis visuals després)
        if i == 0:
            c_d.insert(0, copy.deepcopy(armadura_inicial)); c_e.insert(0, copy.deepcopy(armadura_inicial))
            c_d.insert(0, clef.TrebleClef()); c_e.insert(0, clef.BassClef())
            c_d.insert(0, meter.TimeSignature('4/4')); c_e.insert(0, meter.TimeSignature('4/4'))
            
        if i == 2: c_d.insert(0, layout.SystemLayout(isNew=True))
        if i == 3: c_d.rightBarline = c_e.rightBarline = bar.Barline('final')

        p_d.append(c_d); p_e.append(c_e)
    
    grup = layout.StaffGroup([p_d, p_e], symbol='brace', barTogether=True)
    score_out.insert(0, p_d); score_out.insert(0, p_e); score_out.insert(0, grup)
    return score_out, f"{v7_root_name}7", var_nom

def mostrar_partitura(xml_bytes):
    xml_str = xml_bytes.decode('utf-8')
    xml_escapat = json.dumps(xml_str)
    html_code = f"""
    <div style="background-color: white; padding: 20px; border-radius: 10px;">
        <div id="osmdCanvas"></div>
    </div>
    <script src="https://cdn.jsdelivr.net/npm/opensheetmusicdisplay@1.8.8/build/opensheetmusicdisplay.min.js"></script>
    <script>
      var osmd = new opensheetmusicdisplay.OpenSheetMusicDisplay("osmdCanvas", {{
        autoResize: true, backend: "svg", drawTitle: false, drawComposer: false, 
        drawPartNames: false, newSystemFromXML: true, stretchLastSystemLine: true
      }});
      osmd.load({xml_escapat}).then(function() {{ osmd.render(); }});
    </script>
    """
    components.html(html_code, height=600, scrolling=True)

# --- INTERFÍCIE ---
col1, col2 = st.columns([1, 1])
with col1:
    if st.button('🚀 Generar Exercici', use_container_width=True):
        try:
            nou_score, v7_nom, var_nom = generar_estudi_final()
            st.session_state.tonalitat = v7_nom
            st.session_state.variacio_nom = var_nom
            xml_path = nou_score.write('musicxml')
            with open(xml_path, 'rb') as f:
                st.session_state.xml_data = f.read()
            st.session_state.score_generat = True
            os.remove(xml_path)
        except Exception as e:
            st.error(f"Error: {e}")

if st.session_state.score_generat:
    with col2:
        st.download_button(f"📥 Baixar MusicXML ({st.session_state.tonalitat})", st.session_state.xml_data, f"Funk.musicxml", use_container_width=True)
    st.divider()
    mostrar_partitura(st.session_state.xml_data)
