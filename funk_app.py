import streamlit as st
import streamlit.components.v1 as components
import json
import os
import random
import copy
import warnings
from music21 import *

# Ignorem avisos de music21 que poden embrutar la consola
warnings.filterwarnings("ignore")

# --- 1. CONFIGURACIÓ DE L'APLICACIÓ ---
st.set_page_config(page_title="Generador de Funk Harmònic", layout="wide")
st.title("🎸 Generador de Funk: Bucles Harmònics")
st.write("Genera 8 compassos basats en bucles de 2, amb relacions de 4ª o cromatismes (espècies m7 i 7).")

# Inicialitzem l'estat de la sessió
if 'xml_data' not in st.session_state:
    st.session_state.xml_data = None
    st.session_state.score_generat = False

# --- 2. LÒGICA HARMÒNICA ---

def generar_progressio_custom():
    """Crea una llista de 8 acords basats en 4 bucles de 2 compassos."""
    roots_base = ['C', 'F', 'G', 'Bb', 'Eb', 'D', 'A']
    progressio = []
    
    # Triem l'arrel inicial
    arrel_actual = pitch.Pitch(random.choice(roots_base))
    
    for _ in range(4): # 4 bucles * 2 compassos = 8 compassos
        # Triem l'especie per aquest bucle: (m7 -> 7) o (7 -> 7)
        especie_bucle = random.choice([('m7', '7'), ('7', '7')])
        
        # Relació per al segon acord del bucle
        relacio = random.choice(['4J', 'C+', 'C-']) # 4a Justa, Cromatisme +, Cromatisme -
        
        if relacio == '4J':
            interval_rel = interval.Interval('P4')
        elif relacio == 'C+':
            interval_rel = interval.Interval('m2')
        else: # C-
            interval_rel = interval.Interval('m2').reverse()
            
        arrel_2 = arrel_actual.transpose(interval_rel)
        
        # Afegim els dos compassos
        progressio.append({'root': arrel_actual.name, 'especie': especie_bucle[0]})
        progressio.append({'root': arrel_2.name, 'especie': especie_bucle[1]})
        
        # Saltem a una nova arrel aleatòria per al següent bucle per donar varietat
        arrel_actual = pitch.Pitch(random.choice(roots_base))
        
    return progressio

def ajustar_a_especie(pitch_obj, arrel_nom, especie):
    """Modifica les notes del patró original per quadrar amb m7 o 7."""
    arrel_pitch = pitch.Pitch(arrel_nom)
    itvl = interval.Interval(arrel_pitch, pitch_obj)
    semitons = itvl.semitones % 12
    
    # Ajust de la 3ª (semitons 3=m, 4=M)
    if especie == 'm7' and semitons == 4: # Si és Major i volem menor
        pitch_obj.transpose(-1, inPlace=True)
    elif especie == '7' and semitons == 3: # Si és menor i volem Major (dominant)
        pitch_obj.transpose(1, inPlace=True)
        
    # Ajust de la 7ª (semitons 10=m, 11=M)
    # En funk quasi sempre volem 7a menor (dominant)
    if semitons == 11: 
        pitch_obj.transpose(-1, inPlace=True)

# --- 3. LÒGICA DE RENDERITZACIÓ ---

def mostrar_partitura(xml_bytes):
    """Injecta OpenSheetMusicDisplay per veure la partitura al navegador."""
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

# --- 4. GENERACIÓ DEL SCORE ---

def generar_estudi_final():
    ruta_funk = 'patrons funk.xml'
    if not os.path.exists(ruta_funk):
        raise FileNotFoundError(f"No s'ha trobat el fitxer {ruta_funk}")

    # Carregar base de dades
    score_in = converter.parse(ruta_funk)
    part_in = score_in.getElementsByClass(stream.Part)[0]
    all_measures = list(part_in.getElementsByClass(stream.Measure))
    
    # 1. Separar els pentagrames de la base de dades (Staff 1 i 2)
    patrons_dreta = []
    patrons_esquerra = []
    for m in all_measures:
        m_rh, m_lh = stream.Measure(), stream.Measure()
        for el in m.flatten().notesAndRests:
            if el.staff == 1: m_rh.insert(el.offset, copy.deepcopy(el))
            elif el.staff == 2: m_lh.insert(el.offset, copy.deepcopy(el))
        patrons_dreta.append(m_rh)
        patrons_esquerra.append(m_lh)
    
    # 2. Crear estructura de sortida
    progressio = generar_progressio_custom()
    score_out = stream.Score()
    part_d, part_e = stream.Part(), stream.Part()
    
    # 3. Construir els 8 compassos
    for i, dada in enumerate(progressio):
        arrel = dada['root']
        especie = dada['especie']
        
        # Triem un patró rítmic a l'atzar
        idx = random.randint(0, len(patrons_dreta) - 1)
        c_d = copy.deepcopy(patrons_dreta[idx])
        c_e = copy.deepcopy(patrons_esquerra[idx])
        c_d.number = c_e.number = i + 1
        
        # Transposició i ajust harmònic
        itvl_base = interval.Interval(pitch.Pitch('C4'), pitch.Pitch(arrel + '4'))
        for c in [c_d, c_e]:
            c.transpose(itvl_base, inPlace=True)
            for n in c.flatten().notes:
                if n.isNote: ajustar_a_especie(n.pitch, arrel, especie)
                elif n.isChord:
                    for p in n.pitches: ajustar_a_especie(p, arrel, especie)
            
            # Neteja de metadades per compàs
            for cl in ['KeySignature', 'TimeSignature', 'Clef', 'SystemLayout']:
                c.removeByClass(cl)

        # Afegir clefs i temps al primer compàs
        if i == 0:
            c_d.insert(0, clef.TrebleClef()); c_d.insert(0, meter.TimeSignature('4/4'))
            c_e.insert(0, clef.BassClef()); c_e.insert(0, meter.TimeSignature('4/4'))
        
        # Salt de sistema al compàs 5
        if i == 4: c_d.insert(0, layout.SystemLayout(isNew=True))
        
        # Doble barra final
        if i == 7:
            c_d.rightBarline = bar.Barline('final')
            c_e.rightBarline = bar.Barline('final')

        part_d.append(c_d)
        part_e.append(c_e)
        
    #
