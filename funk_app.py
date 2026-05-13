import streamlit as st
import music21
import os
import random
import copy
import tempfile
import streamlit.components.v1 as components

# --- CONFIGURACIÓ DE PÀGINA ---
st.set_page_config(page_title="Funk Generator Multitonal", page_icon="🎸", layout="wide")

st.title("🎸 Funk Generator: Tonalitats Aleatòries")

# --- FUNCIONS DE SUPORT ---

def obtenir_escala_blues(nota_base):
    """Genera una escala de blues a partir d'una nota base."""
    # Intervals de l'escala de blues: 0, 3, 5, 6, 7, 10 semitons
    intervals = [0, 3, 5, 6, 7, 10, 12]
    base = music21.pitch.Pitch(nota_base + "4")
    escala = []
    for i in intervals:
        p = base.transpose(i)
        # Forcem l'ús de sostinguts per a la "blue note" (quarta augmentada)
        if i == 6:
            p = p.getLowerEnharmonic() if p.accidental.name == 'flat' else p
        escala.append(p.nameWithOctave)
    return escala

def generar_frase_blues(n_notes, escala):
    direccio = random.choice([1, -1])
    idx = random.randint(0, len(escala) - 1)
    frase = []
    for _ in range(n_notes):
        frase.append(escala[idx])
        idx += direccio
        if idx >= len(escala) or idx < 0:
            direccio *= -1
            idx += (direccio * 2)
            idx = max(0, min(len(escala) - 1, idx))
    return frase

def render_musicxml(xml_data):
    xml_str = xml_data.decode('utf-8').replace('`', '\\`').replace('$', '\\$')
    html_code = f"""
    <div style="background-color: #f0f2f6; padding: 20px; display: flex; justify-content: center;">
        <div style="background-color: #FFFFFF; padding: 20px; border-radius: 10px; width: 100%; max-width: 1100px; box-shadow: 0 10px 25px rgba(0,0,0,0.1);">
            <div id="score-container"></div>
        </div>
    </div>
    <script src="https://cdn.jsdelivr.net/npm/opensheetmusicdisplay@1.5.8/build/opensheetmusicdisplay.min.js"></script>
    <script>
        const osmd = new opensheetmusicdisplay.OpenSheetMusicDisplay("score-container", {{
            autoResize: true, drawTitle: false, drawComposer: false, drawPartNames: false,
            drawPartAbbreviations: false, drawMetronomeMarks: false, drawMeasureNumbers: false
        }});
        osmd.setOptions({{
            zoom: 1.4, spacingFactor: 1.0, newSystemsFromMusicXml: true,
            pageFormat: "A4", pageBackgroundColor: "#FFFFFF"
        }});
        osmd.load(`{xml_str}`).then(() => osmd.render());
    </script>
    """
    components.html(html_code, height=700)

@st.cache_data
def carregar_pool_per_compassos(ruta):
    try:
        score = music21.converter.parse(ruta)
        pool = []
        for m in score.parts[0].getElementsByClass(music21.stream.Measure):
            notes_mesura = []
            for el in m.flatten().notes:
                if el.isChord: notes_mesura.append([p.nameWithOctave for p in el.pitches])
                elif el.isNote: notes_mesura.append([el.pitch.nameWithOctave])
            if notes_mesura: pool.append(notes_mesura)
        return pool
    except: return None

# --- RUTES ---
base_path = os.path.dirname(__file__) if "__file__" in locals() else os.getcwd()
path_ritme = os.path.join(base_path, "buidat_ritmic_funk.musicxml")
path_acords = os.path.join(base_path, "font acords funk.musicxml")

if not os.path.exists(path_ritme) or not os.path.exists(path_acords):
    st.error("⚠️ Falten fitxers XML.")
else:
    col1, col2 = st.columns(2)
    with col1:
        boto_generar = st.button("🎲 GENERAR EN QUALSEVOL TO", use_container_width=True)

    if boto_generar:
        with st.spinner("Transposant i generant..."):
            try:
                pool_compassos = carregar_pool_per_compassos(path_acords)
                score_ritme = music21.converter.parse(path_ritme)
                
                # 1. ESCOLLIR TONALITAT BASE ALEATÒRIA
                tonalitats_possibles = ['C', 'Db', 'D', 'Eb', 'E', 'F', 'Gb', 'G', 'Ab', 'A', 'Bb', 'B']
                to_base = random.choice(tonalitats_possibles)
                st.info(f"Tonalitat de l'exercici: **{to_base}**")
                
                # Calculem l'interval de transposició global respecte al Do original del fitxer
                itvl_global = music21.interval.Interval(music21.pitch.Pitch('C4'), music21.pitch.Pitch(to_base + '4'))
                
                # Generem l'escala de blues per a aquesta tonalitat
                escala_blues_actual = obtenir_escala_blues(to_base)
                
                # 2. DEFINIR INTERVALS PER ALS COMPASSOS 2 i 4 (Db7, F7, G7 respecte a la base)
                # Utilitzem noms d'intervals per seguretat (2a menor, 4a justa, 5a justa)
                opcions_itvl = [
                    music21.interval.Interval('m2'), # Equivalent a Db
                    music21.interval.Interval('P4'), # Equivalent a F
                    music21.interval.Interval('P5')  # Equivalent a G
                ]
                itvl2 = random.choice(opcions_itvl)
                itvl4 = random.choice(opcions_itvl)
                
                new_score = music21.stream.Score()
                memoria_A, memoria_B = {}, {}

                num_m_originals = len(score_ritme.parts[0].getElementsByClass(music21.stream.Measure))
                start_m = random.randint(0, max(0, num_m_originals - 4))

                for idx_p, part_original in enumerate(score_ritme.parts):
                    nova_part = music21.stream.Part()
                    nova_part.insert(0, music21.clef.TrebleClef() if idx_p == 0 else music21.clef.BassClef())
                    
                    # Posem una armadura buida (Do) perquè volem llegir-ho tot amb alteracions accidentals
                    nova_part.insert(0, music21.key.KeySignature(0)) 
                    
                    mesures_originals = list(part_original.getElementsByClass(music21.stream.Measure))
                    seleccio = [copy.deepcopy(m) for m in mesures_originals[start_m : start_m + 4]]
                    
                    for i in range(4):
                        if i in [0, 2]: # GENERACIÓ COMPASSOS BASE (1 i 3)
                            m_nova = seleccio[i]
                            # Transposem el compàs a la tonalitat base escollida
                            m_nova.transpose(itvl_global, inPlace=True)
                            
                            if idx_p == 0: # Mà dreta
                                grup_acords = random.choice(pool_compassos)
                                notes_elements = list(m_nova.flatten().notes)
                                
                                # Detector de ratxes
                                ratxes = []
                                ratxa_actual = []
                                for idx_n, n in enumerate(notes_elements):
                                    if n.duration.quarterLength <= 0.25: ratxa_actual.append(idx_n)
                                    else:
                                        if len(ratxa_actual) >= 3: ratxes.append(ratxa_actual)
                                        ratxa_actual = []
                                if len(ratxa_actual) >= 3: ratxes.append(ratxa_actual)
                                
                                indices_melodia = {idx for r in ratxes for idx in r}
                                map_notes_melodia = {}
                                for r in ratxes:
                                    frase = generar_frase_blues(len(r), escala_blues_actual)
                                    for idx_r, idx_orig in enumerate(r):
                                        map_notes_melodia[idx_orig] = frase[idx_r]

                                for idx_n, n in enumerate(notes_elements):
                                    if idx_n in indices_melodia:
                                        n_final = music21.note.Note(map_notes_melodia[idx_n])
                                    else:
                                        # Transposem també l'acord del pool a la nova tonalitat
                                        acord_original = random.choice(grup_acords)
                                        chord_obj = music21.chord.Chord(acord_original)
                                        chord_obj.transpose(itvl_global, inPlace=True)
                                        n_final = chord_obj
                                    
                                    n_final.duration = n.duration
                                    m_nova.replace(n, n_final)
                            
                            if i == 0: memoria_A[idx_p] = copy.deepcopy(m_nova)
                            else: memoria_B[idx_p] = copy.deepcopy(m_nova)

                        elif i == 1: 
                            m_nova = copy.deepcopy(memoria_A[idx_p])
                            m_nova.transpose(itvl2, inPlace=True)
                            for ks in m_nova.getElementsByClass(music21.key.KeySignature): m_nova.remove(ks)

                        elif i == 3: 
                            m_nova = copy.deepcopy(memoria_B[idx_p])
                            m_nova.transpose(itvl4, inPlace=True)
                            for ks in m_nova.getElementsByClass(music21.key.KeySignature): m_nova.remove(ks)
                            m_nova.rightBarline = music21.bar.Barline('final')

                        if i == 2: m_nova.insert(0, music21.layout.SystemLayout(isNew=True))
                        m_nova.number = i + 1
                        m_nova.makeBeams(inPlace=True)
                        nova_part.append(m_nova)
                    
                    nova_part = nova_part.makeNotation()
                    # Neteja d'alteracions
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
                               file_name="funk_multitonal.musicxml", use_container_width=True)
        render_musicxml(st.session_state['xml_data'])
