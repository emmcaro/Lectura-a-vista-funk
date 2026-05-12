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
st.write("Genera 8 compassos aleatoris (mà dreta i esquerra) basats en la teva base de dades.")

if 'xml_data' not in st.session_state:
    st.session_state.xml_data = None
    st.session_state.score_generat = False

FITXER_BASE = 'patrons funk.musicxml'
if not os.path.exists(FITXER_BASE):
    if os.path.exists('patrons funk.xml'):
        FITXER_BASE = 'patrons funk.xml'
    else:
        st.error(f"⚠️ NO S'HA TROBAT EL FITXER: '{FITXER_BASE}'")
        st.stop()

# --- GENERACIÓ DE SCORE ---

def generar_estudi_final():
    score_in = converter.parse(FITXER_BASE)
    parts_in = list(score_in.parts)
    
    patrons_dreta = []
    patrons_esquerra = []
    
    # CAS A: Music21 ja ha separat la clau de Sol i la clau de Fa (Molt comú amb Logic Pro)
    if len(parts_in) >= 2:
        mesures_d = list(parts_in[0].getElementsByClass(stream.Measure))
        mesures_e = list(parts_in[1].getElementsByClass(stream.Measure))
        
        # Emparellem els compassos de la dreta amb la esquerra
        for md, me in zip(mesures_d, mesures_e):
            patrons_dreta.append(copy.deepcopy(md))
            patrons_esquerra.append(copy.deepcopy(me))
            
    # CAS B: Està tot junt en una sola part i ho hem de separar manualment
    else:
        all_measures = list(parts_in[0].getElementsByClass(stream.Measure))
        for m in all_measures:
            m_rh, m_lh = stream.Measure(), stream.Measure()
            for n in m.flatten().notesAndRests:
                staff_val = getattr(n, 'staff', None)
                if staff_val is None and n.isChord and len(n.notes) > 0:
                    staff_val = getattr(n.notes[0], 'staff', 1)
                
                if staff_val == 2:
                    m_lh.insert(n.offset, copy.deepcopy(n))
                else:
                    m_rh.insert(n.offset, copy.deepcopy(n))
            patrons_dreta.append(m_rh)
            patrons_esquerra.append(m_lh)
    
    # Ara que tenim els patrons de les dues mans, muntem la partitura nova
    score_out = stream.Score()
    p_d, p_e = stream.Part(), stream.Part()
    
    for i in range(8):
        idx = random.randint(0, len(patrons_dreta) - 1)
        c_d, c_e = copy.deepcopy(patrons_dreta[idx]), copy.deepcopy(patrons_esquerra[idx])
        c_d.number = c_e.number = i + 1
        
        # Neteja de formats
        for c in [c_d, c_e]:
            for cl in ['KeySignature', 'TimeSignature', 'Clef', 'SystemLayout']:
                c.removeByClass(cl)

        # Posem la informació inicial al compàs 1
        if i == 0:
            c_d.insert(0, clef.TrebleClef()); c_d.insert(0, meter.TimeSignature('4/4'))
            c_e.insert(0, clef.BassClef()); c_e.insert(0, meter.TimeSignature('4/4'))
            
        # Salt de sistema al compàs 5
        if i == 4: 
            c_d.insert(0, layout.SystemLayout(isNew=True))
            
        # Barra final
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
        with st.spinner('Barrejant compassos de les dues mans...'):
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
