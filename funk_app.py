import streamlit as st
import streamlit.components.v1 as components
import json
import os
import random
import copy
import warnings
from music21 import *

# Configuració per evitar que music21 busqui programes externs al servidor
environment.set('musicxmlDirectives', 'no-playback')

warnings.filterwarnings("ignore")

# --- 1. CONFIGURACIÓ DE PÀGINA ---
st.set_page_config(page_title="Generador de Funk", layout="wide")
st.title("🎸 Generador de Funk: Bucles Harmònics")

# Inicialitzem l'estat si no existeix
if 'xml_data' not in st.session_state:
    st.session_state.xml_data = None
    st.session_state.score_generat = False

# --- 2. COMPROVACIÓ DEL FITXER ---
# Aquesta part és vital: si el fitxer no es diu EXACTAMENT així, l'app t'ho avisarà
FITXER_BASE = 'patrons funk.xml'

if not os.path.exists(FITXER_BASE):
    st.error(f"⚠️ NO S'HA TROBAT EL FITXER: '{FITXER_BASE}'")
    st.info("Assegura't que el fitxer XML està a la mateixa carpeta que aquest script de Python.")
    st.stop() # Atura l'execució fins que el fitxer hi sigui
else:
    st.success(f"✅ Fitxer base '{FITXER_BASE}' detectat correctament.")

# --- 3. LÒGICA HARMÒNICA ---

def generar_progressio_custom():
    roots_base = ['C', 'F', 'G', 'Bb', 'Eb', 'D', 'A']
    progressio = []
    arrel_actual = pitch.Pitch(random.choice(roots_base))
    
    for _ in range(4):
        especie_bucle = random.choice([('m7', '7'), ('7', '7')])
        relacio = random.choice(['4J', 'C+', 'C-'])
        
        if relacio == '4J': interval_rel = interval.Interval('P4')
        elif relacio == 'C+': interval_rel = interval.Interval('m2')
        else: interval_rel = interval.Interval('m2').reverse()
            
        arrel_2 = arrel_actual.transpose(interval_rel)
        progressio.append({'root': arrel_actual.name, 'especie': especie_bucle[0]})
        progressio.append({'root': arrel_2.name, 'especie': especie_bucle[1]})
        arrel_actual = pitch.Pitch(random.choice(roots_base))
    return progressio

def ajustar_a_especie(pitch_obj, arrel_nom, especie):
    arrel_pitch = pitch.Pitch(arrel_nom)
    itvl = interval.Interval(arrel_pitch, pitch_obj)
    semitons = itvl.semitones % 12
    if especie == 'm7' and semitons == 4: pitch_obj.transpose(-1, inPlace=True)
    elif especie == '7' and semitons == 3: pitch_obj.transpose(1, inPlace=True)
    if semitons == 11: pitch_obj.transpose(-1, inPlace=True)

# --- 4. FUNCIÓ DE GENERACIÓ ---

def generar_estudi_final():
    score_in = converter.parse(FITXER_BASE)
    part_in = score_in.getElementsByClass(stream.Part)[0]
    all_measures = list(part_in.getElementsByClass(stream.Measure))
    
    patrons_dreta, patrons_esquerra = [], []
    for m in all_measures:
        m_rh, m_lh = stream.Measure(), stream.Measure()
        for el in m.flatten().notesAndRests:
            if el.staff == 1: m_rh.insert(el.offset, copy.deepcopy(el))
            elif el.staff == 2: m_lh.insert(el.offset, copy.deepcopy(el))
        patrons_dreta.append(m_rh)
        patrons_esquerra.append(m_lh)
    
    progressio = generar_progressio_custom()
    score_out = stream.Score()
    part_d, part_e = stream.Part(), stream.Part()
    
    for i, dada in enumerate(progressio):
        arrel, especie = dada['root'], dada['especie']
        idx = random.randint(0, len(patrons_dreta) - 1)
        c_d, c_e = copy.deepcopy(patrons_dreta[idx]), copy.deepcopy(patrons_esquerra[idx])
        c_d.number = c_e.number = i + 1
        
        itvl_base = interval.Interval(pitch.Pitch('C4'), pitch.Pitch(arrel + '4'))
        for c in [c_d, c_e]:
            c.transpose(itvl_base, inPlace=True)
            for n in c.flatten().notes:
                if n.isNote: ajustar_a_especie(n.pitch, arrel, especie)
                elif n.isChord:
                    for p in n.pitches: ajustar_a_especie(p, arrel, especie)
            for cl in ['KeySignature', 'TimeSignature', 'Clef', 'SystemLayout']:
                c.removeByClass(cl)

        if i == 0:
            c_d.insert(0, clef.TrebleClef()); c_d.insert(0, meter.TimeSignature('4/4'))
            c_e.insert(0, clef.BassClef()); c_e.insert(0, meter.TimeSignature('4/4'))
        if i == 4: c_d.insert(0, layout.SystemLayout(isNew=True))
        if i == 7:
            c_d.rightBarline = bar.Barline('final')
            c_e.rightBarline = bar.Barline('final')

        part_d.append(c_d)
        part_e.append(c_e)
        
    grup = layout.StaffGroup([part_d, part_e], symbol='brace', barTogether=True)
    score_out.insert(0, part_d); score_out.insert(0, part_e); score_out.insert(0, grup)
    return score_out

def mostrar_partitura(xml_bytes):
    xml_str = xml_bytes.decode('utf-8')
    xml_escapat = json.dumps(xml_str)
    html_code = f"""
    <div id="osmdCanvas"></div>
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

# --- 5. INTERFÍCIE D'USUARI ---

col1, col2 = st.columns([1, 1])

with col1:
    # EL BOTÓ HA DE SORTIR AQUÍ
    if st.button('🚀 Generar Nova Lectura Funk', use_container_width=True):
        with st.spinner('Treballant...'):
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
        st.download_button("📥 Descarregar MusicXML", st.session_state.xml_data, "Funk.musicxml", use_container_width=True)
    st.divider()
    mostrar_partitura(st.session_state.xml_data)
