import streamlit as st
import music21
import os
import random
import copy
import tempfile
import streamlit.components.v1 as components

# --- CONFIGURACIÓ DE PÀGINA ---
st.set_page_config(page_title="Funk Generator Mixolydian", page_icon="🎸", layout="wide")

st.title("🎸 Funk Generator: Mode Mixolidi")
st.subheader("Armadura de la IV per a la I (Ex: C7 -> Armadura de F)")

# Escala de Blues Base (Do)
BLUES_C = ['C4', 'Eb4', 'F4', 'F#4', 'G4', 'Bb4', 'C5']

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

def generar_frase_blues(n_notes):
    direccio = random.choice([1, -1])
    idx = random.randint(0, len(BLUES_C) - 1)
    frase = []
    for _ in range(n_notes):
        frase.append(BLUES_C[idx])
        idx += direccio
        if idx >= len(BLUES_C) or idx < 0:
            direccio *= -1
            idx += (direccio * 2)
            idx = max(0, min(len(BLUES_C) - 1, idx))
    return frase

# --- RUTES ---
base_path = os.path.dirname(__file__) if "__file__" in locals() else os.getcwd()
path_ritme = os.path.join(base_path, "buidat_ritmic_funk.musicxml")
path_acords = os.path.join(base_path, "font acords funk.musicxml")

if not os.path.exists(path_ritme) or not os.path.exists(path_acords):
    st.error("⚠️ Falten fitxers XML.")
else:
    col1, col2 = st.columns(2)
    with col1:
        boto_generar = st.button("🎲 GENERAR MIXOLIDI", use_container_width=True)

    if boto_generar:
        with st.spinner("Construint en Do i transposant a Mixolidi..."):
            try:
                pool_compassos = carregar_pool_per_compassos(path_acords)
                score_ritme = music21.converter.parse(path_ritme)
                
                new_score = music21.stream.Score()
                memoria_A, memoria_B = {}, {}
                
                # Intervals interns (Db, F, G)
                opcions_internes = [music21.interval.Interval('m2'), music21.interval.Interval('P4'), music21.interval.Interval('P5')]
                itvl_compas2 = random.choice(opcions_internes)
                itvl_compas4 = random.choice(opcions_internes)

                num_m_originals = len(score_ritme.parts[0].getElementsByClass(music21.stream.Measure))
                start_m = random.randint(0, max(0, num_m_originals - 4))

                # --- 1. CONSTRUCCIÓ BASE EN DO ---
                for idx_p, part_original in enumerate(score_ritme.parts):
                    nova_part = music21.stream.Part()
                    nova_part.insert(0, music21.clef.TrebleClef() if idx_p == 0 else music21.clef.BassClef())
                    
                    mesures_originals = list(part_original.getElementsByClass(music21.stream.Measure))
                    seleccio = mesures_originals[start_m : start_m + 4]
                    
                    for i in range(4):
                        m_nova = copy.deepcopy(seleccio[i])
                        if i in [0, 2]:
                            if idx_p == 0:
                                grup_acords = random.choice(pool_compassos)
                                notes_elements = list(m_nova.flatten().notes)
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
                                    frase = generar_frase_blues(len(r))
                                    for idx_r, idx_orig in enumerate(r):
                                        map_notes_melodia[idx_orig] = frase[idx_r]

                                for idx_n, n in enumerate(notes_elements):
                                    if idx_n in indices_melodia:
                                        n_f = music21.note.Note(map_notes_melodia[idx_n])
                                    else:
                                        n_f = music21.chord.Chord(random.choice(grup_acords))
                                    n_f.duration = n.duration
                                    m_nova.replace(n, n_f)
                            
                            if i == 0: memoria_A[idx_p] = copy.deepcopy(m_nova)
                            else: memoria_B[idx_p] = copy.deepcopy(m_nova)

                        elif i == 1:
                            m_nova = copy.deepcopy(memoria_A[idx_p])
                            m_nova.transpose(itvl_compas2, inPlace=True)
                        elif i == 3:
                            m_nova = copy.deepcopy(memoria_B[idx_p])
                            m_nova.transpose(itvl_compas4, inPlace=True)
                            m_nova.rightBarline = music21.bar.Barline('final')

                        if i == 2: m_nova.insert(0, music21.layout.SystemLayout(isNew=True))
                        m_nova.number = i + 1
                        m_nova.makeBeams(inPlace=True)
                        nova_part.append(m_nova)
                    new_score.insert(0, nova_part)

                # --- 2. TRANSPOSICIÓ I ARMADURA MIXOLÍDIA ---
                tonalitats = ['C', 'G', 'D', 'A', 'E', 'B', 'F#', 'F', 'Bb', 'Eb', 'Ab', 'Db']
                to_base = random.choice(tonalitats)
                
                # CÀLCUL: L'armadura mixolídia és l'armadura de la tonalitat situada una 4a justa per sobre (o una 5a per sota)
                p_tonica = music21.pitch.Pitch(to_base)
                p_armadura = p_tonica.transpose('P4')
                num_sharps = music21.key.Key(p_armadura.name).sharps
                nova_ks = music21.key.KeySignature(num_sharps)
                
                itvl_final = music21.interval.Interval(music21.pitch.Pitch('C4'), music21.pitch.Pitch(to_base + '4'))
                new_score.transpose(itvl_final, inPlace=True)
                
                st.info(f"Tònica: **{to_base}7** | Armadura utilitzada: **{p_armadura.name} Major**")

                for p in new_score.parts:
                    p.insert(0, nova_ks)
                    # Neteja de restes de transposició per mantenir l'armadura mixolídia neta
                    for m in p.getElementsByClass(music21.stream.Measure):
                        for item in list(m.getElementsByClass(music21.key.KeySignature)):
                            m.remove(item)
                    
                    # Neteja de naturals redundants
                    for n in p.flatten().notes:
                        for pitch in n.pitches:
                            if pitch.accidental and pitch.accidental.name == 'natural':
                                pitch.accidental.displayStatus = False

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
                               file_name="funk_mixolydian.musicxml", use_container_width=True)
        render_musicxml(st.session_state['xml_data'])
