import streamlit as st
import music21
import os
import random
import copy
import tempfile
import streamlit.components.v1 as components

# --- CONFIGURACIÓ DE PÀGINA ---
st.set_page_config(page_title="Funk Generator AABB", page_icon="🎸", layout="wide")

st.title("🎸 Funk Generator: Melodies de Blues Fluides")

# Escala de Blues de Do
BLUES_C = ['C4', 'Eb4', 'F4', 'F#4', 'G4', 'Bb4', 'C5']

# --- VISUALITZADOR JS (OSMD) ---
def render_musicxml(xml_data):
    xml_str = xml_data.decode('utf-8').replace('`', '\\`').replace('$', '\\$')
    html_code = f"""
    <div style="background-color: #f0f2f6; padding: 20px; display: flex; justify-content: center;">
        <div style="background-color: #FFFFFF; padding: 30px 8%; border-radius: 10px; width: 100%; max-width: 1200px; box-sizing: border-box; box-shadow: 0 10px 25px rgba(0,0,0,0.1);">
            <div id="score-container"></div>
        </div>
    </div>
    <script src="https://cdn.jsdelivr.net/npm/opensheetmusicdisplay@1.5.8/build/opensheetmusicdisplay.min.js"></script>
    <script>
        const osmd = new opensheetmusicdisplay.OpenSheetMusicDisplay("score-container", {{
            autoResize: true, drawTitle: false, drawComposer: false, drawPartNames: false,
            drawPartAbbreviations: false, drawMetronomeMarks: false, drawMeasureNumbers: false,
            drawingParameters: "default"
        }});
        osmd.setOptions({{
            zoom: 2.0, spacingFactor: 1.5, newSystemsFromMusicXml: true, 
            pageFormat: "Endless", pageBackgroundColor: "#FFFFFF"
        }});
        osmd.load(`{xml_str}`).then(() => {{
            osmd.Sheet.Rules.MinMeasureWidth = 40; 
            osmd.render();
        }});
    </script>
    """
    components.html(html_code, height=900)

@st.cache_data
def carregar_pool_per_compassos(ruta):
    try:
        score = music21.converter.parse(ruta)
        pool = []
        for m in score.parts[0].getElementsByClass(music21.stream.Measure):
            notes = [[p.nameWithOctave for p in el.pitches] if el.isChord else [el.pitch.nameWithOctave] 
                     for el in m.flatten().notes if el.isNote or el.isChord]
            if notes: pool.append(notes)
        return pool
    except: return None

# --- FUNCIONS AUXILIARS DE MELODIA ---
def generar_frase_blues(n_notes):
    """Genera una llista de notes de l'escala de blues que es mouen per grau conjunt."""
    direccio = random.choice([1, -1]) # 1 per pujar, -1 per baixar
    index_actual = random.randint(0, len(BLUES_C) - 1)
    frase = []
    
    for _ in range(n_notes):
        frase.append(BLUES_C[index_actual])
        # Movem l'índex un pas en la direcció escollida, sense sortir dels límits
        index_actual += direccio
        if index_actual >= len(BLUES_C) or index_actual < 0:
            direccio *= -1 # Si arribem al final, rebem (canvi de direcció)
            index_actual += (direccio * 2)
            index_actual = max(0, min(len(BLUES_C) - 1, index_actual))
            
    return frase

# --- LÒGICA DE GENERACIÓ ---
base_path = os.path.dirname(__file__) if "__file__" in locals() else os.getcwd()
path_ritme = os.path.join(base_path, "buidat_ritmic_funk.musicxml")
path_acords = os.path.join(base_path, "font acords funk.musicxml")

if not os.path.exists(path_ritme) or not os.path.exists(path_acords):
    st.error("⚠️ Falten fitxers XML.")
else:
    col1, col2 = st.columns(2)
    with col1:
        boto_generar = st.button("🔥 GENERAR EXERCICI", use_container_width=True)

    if boto_generar:
        with st.spinner("Generant..."):
            try:
                pool_compassos = carregar_pool_per_compassos(path_acords)
                score_ritme = music21.converter.parse(path_ritme)
                
                # Transposicions aleatòries
                itvls = { 'Db': music21.interval.Interval('C4', 'Db4'), 'F': music21.interval.Interval('C4', 'F4') }
                t2 = random.choice(['Db', 'F'])
                t4 = random.choice(['Db', 'F'])
                
                new_score = music21.stream.Score()
                armadura_fa = music21.key.KeySignature(-1) 
                memoria_A, memoria_B = {}, {}

                num_m_originals = len(score_ritme.parts[0].getElementsByClass(music21.stream.Measure))
                start_m = random.randint(0, max(0, num_m_originals - 4))

                for idx_p, part_original in enumerate(score_ritme.parts):
                    nova_part = music21.stream.Part()
                    nova_part.insert(0, music21.clef.TrebleClef() if idx_p == 0 else music21.clef.BassClef())
                    nova_part.insert(0, armadura_fa)
                    
                    mesures_originals = list(part_original.getElementsByClass(music21.stream.Measure))
                    seleccio = mesures_originals[start_m : start_m + 4]
                    
                    for i in range(4):
                        if i in [0, 2]: # Creem base per compassos 1 i 3
                            m_nova = copy.deepcopy(seleccio[i])
                            if idx_p == 0: # Només mà dreta
                                grup_acords = random.choice(pool_compassos)
                                notes_list = list(m_nova.flatten().notes)
                                
                                # --- DETECTOR DE RATXES DE SEMICORXERES ---
                                # Busquem grups de 3 o més semicorxeres consecutives
                                ratxes = []
                                ratxa_actual = []
                                for idx_n, n in enumerate(notes_list):
                                    if n.duration.quarterLength <= 0.25: # Semicorxera o menys
                                        ratxa_actual.append(idx_n)
                                    else:
                                        if len(ratxa_actual) >= 3:
                                            ratxes.append(ratxa_actual)
                                        ratxa_actual = []
                                if len(ratxa_actual) >= 3:
                                    ratxes.append(ratxa_actual)
                                
                                # Convertim les ratxes en melodia i la resta en acords
                                indices_melodia = {idx for r in ratxes for idx in r}
                                
                                # Per cada ratxa, generem una frase de blues per grau conjunt
                                map_notes_melodia = {}
                                for r in ratxes:
                                    frase = generar_frase_blues(len(r))
                                    for idx_en_ratxa, idx_original in enumerate(r):
                                        map_notes_melodia[idx_original] = frase[idx_en_ratxa]

                                for idx_n, n in enumerate(notes_list):
                                    if idx_n in indices_melodia:
                                        n_nova = music21.note.Note(map_notes_melodia[idx_n])
                                    else:
                                        n_nova = music21.chord.Chord(random.choice(grup_acords))
                                    
                                    n_nova.duration = n.duration
                                    m_nova.replace(n, n_nova)
                            
                            if i == 0: memoria_A[idx_p] = copy.deepcopy(m_nova)
                            else: memoria_B[idx_p] = copy.deepcopy(m_nova)

                        elif i == 1: # Compàs 2
                            m_nova = copy.deepcopy(memoria_A[idx_p])
                            m_nova.transpose(itvls[t2], inPlace=True)
                        elif i == 3: # Compàs 4
                            m_nova = copy.deepcopy(memoria_B[idx_p])
                            m_nova.transpose(itvls[t4], inPlace=True)
                            m_nova.rightBarline = music21.bar.Barline('final')

                        if i == 2: m_nova.insert(0, music21.layout.SystemLayout(isNew=True))
                        m_nova.number = i + 1
                        m_nova.makeBeams(inPlace=True)
                        nova_part.append(m_nova)
                    
                    nova_part = nova_part.makeNotation()
                    for p in nova_part.flatten().pitches:
                        if p.accidental and p.accidental.name == 'natural':
                            p.accidental.displayStatus = False
                    new_score.insert(0, nova_part)

                new_score.insert(0, music21.layout.StaffGroup(list(new_score.parts), symbol='brace', barTogether=True))

                with tempfile.NamedTemporaryFile(delete=False, suffix=".musicxml") as tmp:
                    new_score.write('musicxml', fp=tmp.name)
                    with open(tmp.name, 'rb') as f:
                        st.session_state['xml_data'] = f.read()
                
            except Exception as e:
                st.error(f"Error: {e}")

    if 'xml_data' in st.session_state:
        with col2:
            st.download_button(label="📥 Descarregar XML", data=st.session_state['xml_data'], 
                               file_name="funk_blues_AABB.musicxml", use_container_width=True)
        render_musicxml(st.session_state['xml_data'])
