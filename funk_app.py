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
st.set_page_config(page_title="Generador de Funk (Mixolidi)", layout="wide")
st.title("🎸 Generador de Funk: Lògica de Dominants")
st.write("Estructura AA BB. L'armadura es calcula com a V7 de la tonalitat de destí.")

# INICIALITZACIÓ
if 'xml_data' not in st.session_state:
    st.session_state.xml_data = None
    st.session_state.score_generat = False
    st.session_state.tonalitat = None  

FITXER_BASE = 'patrons funk.musicxml'
if not os.path.exists(FITXER_BASE):
    if os.path.exists('patrons funk.xml'):
        FITXER_BASE = 'patrons funk.xml'
    else:
        st.error(f"⚠️ NO S'HA TROBAT EL FITXER: '{FITXER_BASE}'")
        st.stop()

# --- LÒGICA DE TRANSPORT ---

def obtenir_tonalitat_aleatoria():
    # Prioritzem tonalitats amb poques alteracions
    opcions = [
        ('C', 10), ('G', 8), ('F', 8), ('D', 6), ('Bb', 6), 
        ('A', 4), ('Eb', 4), ('E', 2), ('Ab', 2), ('B', 1), ('Db', 1)
    ]
    tonalitats, pesos = zip(*opcions)
    return random.choices(tonalitats, weights=pesos, k=1)[0]

# --- GENERACIÓ DE SCORE ---

def generar_estudi_final():
    score_in = converter.parse(FITXER_BASE)
    parts_in = list(score_in.parts)
    
    patrons_dreta, patrons_esquerra = [], []
    
    # 1. Extracció de patrons (Detecció robusta de mans)
    if len(parts_in) >= 2:
        mesures_d = list(parts_in[0].getElementsByClass(stream.Measure))
        mesures_e = list(parts_in[1].getElementsByClass(stream.Measure))
        for md, me in zip(mesures_d, mesures_e):
            patrons_dreta.append(copy.deepcopy(md))
            patrons_esquerra.append(copy.deepcopy(me))
    else:
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
    
    # 2. Tonalitat del Groove i Tonalitat de l'Armadura
    tonalitat_groove = obtenir_tonalitat_aleatoria() # Ex: 'G' (per a un G7)
    
    # Calcul d'interval des de Do (base del fitxer) fins a la nova fonamental
    itvl = interval.Interval(pitch.Pitch('C'), pitch.Pitch(tonalitat_groove))
    
    # LÒGICA DEMANADA: L'armadura és la de la tonalitat que resoldria (una 4a justa amunt)
    # Si el groove és G7, l'armadura és de Do Major (G -> C)
    tonalitat_resolucio = key.Key(tonalitat_groove).transpose('P4')
    armadura = key.KeySignature(tonalitat_resolucio.sharps)

    # 3. Muntatge
    score_out = stream.Score()
    p_d, p_e = stream.Part(), stream.Part()
    
    idx_A = random.randint(0, len(patrons_dreta) - 1)
    idx_B = random.randint(0, len(patrons_dreta) - 1)
    sequencia = [idx_A, idx_A, idx_B, idx_B]
    
    for i, idx in enumerate(sequencia):
        c_d = copy.deepcopy(patrons_dreta[idx])
        c_e = copy.deepcopy(patrons_esquerra[idx])
        c_d.number = c_e.number = i + 1
        
        for c in [c_d, c_e]:
            for cl in ['KeySignature', 'TimeSignature', 'Clef', 'SystemLayout']:
                c.removeByClass(cl)
            
            # Transportem les notes
            c.transpose(itvl, inPlace=True)
            
            # Netegem accidentals perquè l'armadura agafi el control
            for el in c.flatten().notes:
                if el.isNote:
                    el.pitch.accidental = None 
                elif el.isChord:
                    for p in el.pitches:
                        p.accidental = None

        if i == 0:
            c_d.insert(0, clef.TrebleClef()); c_e.insert(0, clef.BassClef())
            c_d.insert(0, meter.TimeSignature('4/4')); c_e.insert(0, meter.TimeSignature('4/4'))
            c_d.insert(0, copy.deepcopy(armadura)); c_e.insert(0, copy.deepcopy(armadura))
            
        if i == 2: c_d.insert(0, layout.SystemLayout(isNew=True))
        if i == 3: c_d.rightBarline = c_e.rightBarline = bar.Barline('final')

        p_d.append(c_d); p_e.append(c_e)
    
    grup = layout.StaffGroup([p_d, p_e], symbol='brace', barTogether=True)
    score_out.insert(0, p_d); score_out.insert(0, p_e); score_out.insert(0, grup)
    return score_out, tonalitat_groove

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
    if st.button('🚀 Generar Exercici Funk 7th', use_container_width=True):
        with st.spinner('Calculant transport Mixolidi...'):
            try:
                nou_score, nota_triada = generar_estudi_final()
                st.session_state.tonalitat = nota_triada  
                xml_path = nou_score.write('musicxml')
                with open(xml_path, 'rb') as f:
                    st.session_state.xml_data = f.read()
                st.session_state.score_generat = True
                os.remove(xml_path)
            except Exception as e:
                st.error(f"Error tècnic: {e}")

if st.session_state.score_generat:
    st.success(f"Groove en **{st.session_state.tonalitat}7**")
    with col2:
        st.download_button(f"📥 Baixar MusicXML", st.session_state.xml_data, f"Funk_{st.session_state.tonalitat}7.musicxml", use_container_width=True)
    st.divider()
    mostrar_partitura(st.session_state.xml_data)
