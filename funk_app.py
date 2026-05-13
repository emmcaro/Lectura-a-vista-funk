import streamlit as st
import music21
import os
import random
import copy
import tempfile
import streamlit.components.v1 as components

# --- CONFIGURACIÓ ---
st.set_page_config(page_title="Funk Generator", page_icon="🎸", layout="wide")
st.title("🎸 Funk Generator: Estètica Professional")

# Escales de blues molt simples (només noms de notes)
blues_notes = {
    'C': ['C4', 'Eb4', 'F4', 'F#4', 'G4', 'Bb4', 'C5'],
    'Db': ['Db4', 'Fb4', 'Gb4', 'G4', 'Ab4', 'Cb5', 'Db5'],
    'F': ['F4', 'Ab4', 'Bb4', 'B4', 'C5', 'Eb5', 'F5']
}

# --- RUTES ---
base_path = os.path.dirname(__file__) if "__file__" in locals() else os.getcwd()
path_ritme = os.path.join(base_path, "buidat_ritmic_funk.musicxml")
path_acords = os.path.join(base_path, "font acords funk.musicxml")

# --- VISUALITZADOR JS ---
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

# --- LÒGICA ---
if not os.path.exists(path_ritme) or not os.path.exists(path_acords):
    st.error("⚠️ Falten fitxers XML.")
else:
    col1, col2 = st.columns(2)
    with col1:
        boto_generar = st.button("🔥 GENERAR EXERCICI", use_container_width=True)

    if boto_generar:
        try:
            pool_compassos = carregar_pool_per_compassos(path_acords)
            score_ritme = music21.converter.parse(path_ritme)
            
            # Decidir acords destí
            desti_m2 = random.choice(['Db', 'F'])
            desti_m4 = random.choice(['Db', 'F'])
            roots = ['C', desti_m2, 'C', desti_m4]
            
            new_score = music21.stream.Score()
            p0 = music21.stream.Part()
            p1 = music21.stream.Part()
            p0.insert(0, music21.clef.TrebleClef())
            p1.insert(0, music21.clef.BassClef())
            
            num_m_originals = len(score_ritme.parts[0].getElementsByClass(music21.stream.Measure))
            start_m = random.randint(0, max(0, num_m_originals - 4))

            for i in range(4):
                root = roots[i]
                itvl = music21.interval.Interval(music21.pitch.Pitch('C'), music21.pitch.Pitch(root))
                
                for idx_p in range(2):
                    m_base = copy.deepcopy(score_ritme.parts[idx_p].getElementsByClass(music21.stream.Measure)[start_m + (0 if i < 2 else 2)])
                    
                    if idx_p == 0: # Mà dreta: Lògica d'acords o melodia
                        grup_acord = random.choice(pool_compassos)
                        scale = blues_notes.get(root, blues_notes['C'])
                        
                        for n in m_base.flatten().notes:
                            # Si és semicorxera (0.25) o menys, posem una nota sola de l'escala
                            if n.duration.quarterLength <= 0.25:
                                n_nova = music21.note.Note(random.choice(scale))
                            else:
                                n_nova = music21.chord.Chord(random.choice(grup_acord))
                            
                            n_nova.duration = n.duration
                            m_base.replace(n, n_nova)
                    
                    m_base.transpose(itvl, inPlace=True)
                    m_base.number = i + 1
                    if i == 2: m_base.insert(0, music21.layout.SystemLayout(isNew=True))
                    if i == 3: m_base.rightBarline = music21.bar.Barline('final')
                    
                    # Neteja de naturals redundants
                    for p in m_base.flatten().pitches:
                        if p.accidental and p.accidental.name == 'natural': p.accidental.displayStatus = False
                    
                    if idx_p == 0: p0.append(m_base)
                    else: p1.append(m_base)

            new_score.insert(0, p0.makeNotation())
            new_score.insert(0, p1.makeNotation())
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
                               file_name="funk_AABB.musicxml", use_container_width=True)
        render_musicxml(st.session_state['xml_data'])
