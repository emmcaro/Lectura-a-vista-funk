import streamlit as st
import music21
import os
import random
import copy
import tempfile
import streamlit.components.v1 as components

# --- CONFIGURACIÓ ---
st.set_page_config(page_title="Funk Generator Blues", page_icon="🎸", layout="wide")
st.title("🎸 Funk Generator: Estètica Professional + Blues Lines")

# --- DEFINICIÓ D'ESCALES DE BLUES ---
# Escala de blues: 1, b3, 4, #4, 5, b7
blues_scales = {
    'C': ['C4', 'Eb4', 'F4', 'F#4', 'G4', 'Bb4', 'C5'],
    'Db': ['Db4', 'E4', 'Gb4', 'G4', 'Ab4', 'B4', 'Db5'],
    'F': ['F4', 'Ab4', 'Bb4', 'B4', 'C5', 'Eb5', 'F5']
}

# --- RUTES ---
base_path = os.path.dirname(__file__) if "__file__" in locals() else os.getcwd()
path_ritme = os.path.join(base_path, "buidat_ritmic_funk.musicxml")
path_acords = os.path.join(base_path, "font acords funk.musicxml")

# --- VISUALITZADOR ---
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
            drawPartAbbreviations: false, drawMetronomeMarks: false, drawMeasureNumbers: false
        }});
        osmd.setOptions({{ zoom: 2.0, spacingFactor: 1.5, newSystemsFromMusicXml: true, pageFormat: "Endless" }});
        osmd.load(`{xml_str}`).then(() => osmd.render());
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

# --- LÒGICA PRINCIPAL ---
if not os.path.exists(path_ritme) or not os.path.exists(path_acords):
    st.error("⚠️ Falten fitxers XML.")
else:
    col1, col2 = st.columns(2)
    with col1:
        boto_generar = st.button("🔥 GENERAR EXERCICI AMB BLUES", use_container_width=True)

    if boto_generar:
        try:
            pool_compassos = carregar_pool_per_compassos(path_acords)
            score_ritme = music21.converter.parse(path_ritme)
            
            desti_m2 = random.choice(['Db', 'F'])
            desti_m4 = random.choice(['Db', 'F'])
            destins = ['C', desti_m2, 'C', desti_m4]
            intervals = [music21.interval.Interval(music21.pitch.Pitch('C'), music21.pitch.Pitch(d)) for d in destins]
            
            new_score = music21.stream.Score()
            new_score.insert(0, music21.metadata.Metadata(title='', composer=''))
            armadura_fa = music21.key.KeySignature(-1)
            
            memoria_parts = [music21.stream.Part(), music21.stream.Part()]
            memoria_parts[0].insert(0, music21.clef.TrebleClef())
            memoria_parts[1].insert(0, music21.clef.BassClef())
            
            # Guardem els compassos A i B per repetir-los (AABB)
            estructura_A = [None, None] # [Part0_m, Part1_m]
            estructura_B = [None, None]

            num_m_originals = len(score_ritme.parts[0].getElementsByClass(music21.stream.Measure))
            start_m = random.randint(0, max(0, num_m_originals - 4))

            for i in range(4): # 4 compassos
                current_root = destins[i]
                current_scale = blues_scales.get(current_root, blues_scales['C'])
                
                for idx_p in range(2): # 2 mans
                    mesures_originals = list(score_ritme.parts[idx_p].getElementsByClass(music21.stream.Measure))
                    m_base = copy.deepcopy(mesures_originals[start_m + (0 if i < 2 else 2)])
                    
                    # Si és la mà dreta, apliquem la lògica de notes/acords
                    if idx_p == 0:
                        acord_triat = random.choice(pool_compassos)
                        notes_m = list(m_base.flatten().notes)
                        for n in notes_m:
                            # SI ÉS SEMICORXERA O MÉS RÀPIDA -> NOTA BLUES
                            if n.duration.quarterLength <= 0.25:
                                n_nova = music21.note.Note(random.choice(current_scale))
                            else:
                                n_nova = music21.chord.Chord(acord_triat)
                            
                            n_nova.duration = n.duration
                            m_base.replace(n, n_nova)
                    
                    # Transposar segons l'acord del compàs
                    m_base.transpose(intervals[i], inPlace=True)
                    m_base.number = i + 1
                    if i == 2: m_base.insert(0, music21.layout.SystemLayout(isNew=True))
                    if i == 3: m_base.rightBarline = music21.bar.Barline('final')
                    
                    # Neteja de becuadres
                    for p in m_base.flatten().pitches:
                        if p.accidental and p.accidental.name == 'natural': p.accidental.displayStatus = False
                    
                    memoria_parts[idx_p].append(m_base)

            for p in memoria_parts: new_score.insert(0, p.makeNotation())
            
            # Unim pentagrames
            new_score.insert(0, music21.layout.StaffGroup(list(new_score.parts), symbol='brace', barTogether=True))

            with tempfile.NamedTemporaryFile(delete=False, suffix=".musicxml") as tmp:
                new_score.write('musicxml', fp=tmp.name)
                with open(tmp.name, 'rb') as f:
                    st.session_state['xml_data'] = f.read()
                    
        except Exception as e:
            st.error(f"Error: {e}")

    if 'xml_data' in st.session_state:
        with col2:
            st.download_button("📥 Descarregar XML", data=st.session_state['xml_data'], 
                               file_name="funk_blues.musicxml", use_container_width=True)
        render_musicxml(st.session_state['xml_data'])
