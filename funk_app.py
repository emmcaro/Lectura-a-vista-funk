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
st.set_page_config(page_title="Generador de Funk (C7)", layout="wide")
st.title("🎸 Generador de Funk: Groove en C7")
st.write("Aquesta versió genera 8 compassos aleatoris basats exclusivament en l'acord de C7 (mono-acord).")

if 'xml_data' not in st.session_state:
    st.session_state.xml_data = None
    st.session_state.score_generat = False

FITXER_BASE = 'patrons funk.xml'

if not os.path.exists(FITXER_BASE):
    st.error(f"⚠️ NO S'HA TROBAT EL FITXER: '{FITXER_BASE}'")
    st.stop()

# --- GENERACIÓ DE SCORE ---

def generar_estudi_final():
    score_in = converter.parse(FITXER_BASE)
    part_in = score_in.getElementsByClass(stream.Part)[0]
    all_measures = list(part_in.getElementsByClass(stream.Measure))
    
    patrons_dreta, patrons_esquerra = [], []
    
    # Extraiem els compassos assegurant les dues mans (per problemes de veus ocultes)
    for m in all_measures:
        m_rh, m_lh = stream.Measure(), stream.Measure()
        
        for n in m.flatten().notesAndRests:
            staff_val = getattr(n, 'staff', None)
            if staff_val is None and n.isChord and len(n.notes) > 0:
                staff_val = getattr(n.notes[0], 'staff', 1)
            elif staff_val is None:
                staff_val = 1 
                
            if staff_val == 2:
                m_lh.insert(n.offset, copy.deepcopy(n))
            else:
                m_rh.insert(n.offset, copy.deepcopy(n))
                
        patrons_dreta.append(m_rh)
        patrons_esquerra.append(m_lh)
    
    score_out = stream.Score()
    p_d, p_e = stream.Part(), stream.Part()
    
    # Generem els 8 compassos en C7
    for i in range(8):
        idx = random.randint(0, len(patrons_dreta) - 1)
        c_d, c_e = copy.deepcopy(patrons_dreta[idx]), copy.deepcopy(patrons_esquerra[idx])
        c_d.number = c_e.number = i + 1
        
        # Ja no cal transposar, només netegem les claus i signes ocults
        for c in [c_d, c_e]:
            for cl in ['KeySignature', 'TimeSignature', 'Clef', 'SystemLayout']:
                c.removeByClass(cl)

        # Afegim armadura i compàs només al primer
        if i == 0:
            c_d.insert(0, clef.TrebleClef()); c_d.insert(0, meter.TimeSignature('4/4'))
            c_e.insert(0, clef.BassClef()); c_e.insert(0, meter.TimeSignature('4/4'))
            
        # Salt de línia al compàs 5
        if i == 4: 
            c_d.insert(0, layout.SystemLayout(isNew=True))
            
        # Barra final al compàs 8
        if i == 7:
            c_d.rightBarline = c_e.rightBarline = bar.Barline('final')

        p_d.append(c_d)
        p_e.append(c_e)
        
    grup = layout.StaffGroup([p_d, p_e], symbol='brace', barTogether=True)
    score_out.insert(0, p_d); score_out.insert(0, p_e); score_out.insert(0, grup)
    return score_out

def mostrar_partitura(xml_bytes):
    xml_str = xml_bytes.decode('utf-8')
    xml_escapat = json.dumps(xml_str)
    # Fons blanc i arrodonit perquè en mode fosc es llegeixi perfectament
    html_code = f"""
    <div style="background-color: white; padding: 20px; border-radius: 10px; box-shadow: 0px 4px 6px rgba(0,0,0,0.1);">
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
    components.html(html_code, height=650, scrolling=True)

# --- UI ---
col1, col2 = st.columns([1, 1])
with col1:
    if st.button('🚀 Generar Groove Funk (C7)', use_container_width=True):
        with st.spinner('Barrejant compassos...'):
            try:
                nou_score = generar_estudi_final()
                xml_path = nou_score.write('musicxml')
                with open(xml_path, 'rb') as f:
                    st.session_state.xml_data = f.read()
                st.session_state.score_generat = True
                os.remove(xml_path)
            except Exception as e:
                st.error(f"Error: {e}")

if st.session_state.score_generat:
    with col2:
        st.download_button("📥 Descarregar MusicXML", st.session_state.xml_data, "Funk_C7.musicxml", use_container_width=True)
    st.divider()
    mostrar_partitura(st.session_state.xml_data)
