import streamlit as st
import music21
import os
import random
import copy
import tempfile
import streamlit.components.v1 as components

# --- CONFIGURACIÓ DE PÀGINA ---
st.set_page_config(page_title="Lectura Funk", page_icon="🎸", layout="wide")

st.title("Lectura Funk")
st.markdown("")

# --- FUNCIONS DE SUPORT ---

def obtenir_escala_blues_base():
    return ['C4', 'Eb4', 'F4', 'F#4', 'G4', 'Bb4', 'C5']

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
    # Creem dues columnes per als botons
    col1, col2 = st.columns(2)

    with col1:
        boto_generar = st.button("🎲 GENERAR EXERCICI", use_container_width=True)

    if boto_generar:
        with st.spinner("Generant..."):
            try:
                pool_compassos = carregar_pool_per_compassos(path_acords)
                score_ritme = music21.converter.parse(path_ritme)
                
                tonalitat_base = random.choice(['C', 'G', 'D', 'A', 'F', 'Bb', 'Eb'])
                p_armadura = music21.pitch.Pitch(tonalitat_base).transpose('P4')
                sharps = music21.key.Key(p_armadura.name).sharps
                
                new_score = music21.stream.Score()
                escala_blues = obtenir_escala_blues_base()

                num_m_originals = len(score_ritme.parts[0].getElementsByClass(music21.stream.Measure))
                start_m = random.randint(0, max(0, num_m_originals - 4))

                for idx_p, part_original in enumerate(score_ritme.parts):
                    nova_part = music21.stream.Part()
                    nova_part.insert(0, music21.clef.TrebleClef() if idx_p == 0 else music21.clef.BassClef())
                    
                    mesures = list(part_original.getElementsByClass(music21.stream.Measure))[start_m : start_m + 4]
                    mem_m1, mem_m3 = None, None

                    for i in range(4):
                        if i in [0, 2]:
                            m_original = mesures[i]
                            m_nova = copy.deepcopy(m_original)
                            g_acords = random.choice(pool_compassos)
                            
                            if idx_p == 0:
                                notes_actuals = list(m_nova.flatten().notes)
                                ratxes_trobades = []
                                notes_ja_processades = set()

                                for idx_n, n in enumerate(notes_actuals):
                                    if n in notes_ja_processades: continue
                                    if n.duration.quarterLength > 0.25: continue
                                    
                                    ratxa_temp = [idx_n]
                                    offset_esperat = n.offset + n.duration.quarterLength
                                    
                                    for seguent_idx in range(idx_n + 1, len(notes_actuals)):
                                        n_seg = notes_actuals[seguent_idx]
                                        if n_seg.offset == offset_esperat and n_seg.duration.quarterLength <= 0.25:
                                            ratxa_temp.append(seguent_idx)
                                            offset_esperat += n_seg.duration.quarterLength
                                        else:
                                            break
                                    
                                    if 3 <= len(ratxa_temp) <= 4:
                                        ratxes_trobades.append(ratxa_temp)
                                        for r_idx in ratxa_temp: notes_ja_processades.add(notes_actuals[r_idx])
                                
                                set_melodia = {idx for r in ratxes_trobades for idx in r}
                                map_blues = {}
                                for r in ratxes_trobades:
                                    frase = generar_frase_blues(len(r), escala_blues)
                                    for r_i, o_i in enumerate(r): map_blues[o_i] = frase[r_i]

                                for idx_n, n in enumerate(notes_actuals):
                                    if idx_n in set_melodia:
                                        res = music21.note.Note(map_blues[idx_n])
                                    else:
                                        res = music21.chord.Chord(random.choice(g_acords))
                                    res.duration = n.duration
                                    m_nova.replace(n, res)
                            
                            if i == 0: mem_m1 = copy.deepcopy(m_nova)
                            else: mem_m3 = copy.deepcopy(m_nova)

                        elif i == 1:
                            m_nova = copy.deepcopy(mem_m1)
                            m_nova.transpose(random.choice(['m2', 'P4', 'P5']), inPlace=True)
                        elif i == 3:
                            m_nova = copy.deepcopy(mem_m3)
                            m_nova.transpose(random.choice(['m2', 'P4', 'P5']), inPlace=True)
                            m_nova.rightBarline = music21.bar.Barline('final')

                        if i == 2: m_nova.insert(0, music21.layout.SystemLayout(isNew=True))
                        m_nova.number = i + 1
                        m_nova.makeBeams(inPlace=True)
                        nova_part.append(m_nova)
                    new_score.insert(0, nova_part)

                new_score.transpose(music21.interval.Interval(music21.pitch.Pitch('C4'), music21.pitch.Pitch(tonalitat_base + '4')), inPlace=True)
                ks = music21.key.KeySignature(sharps)
                for p in new_score.parts:
                    p.insert(0, ks)
                    for m in p.getElementsByClass(music21.stream.Measure):
                        for item in list(m.getElementsByClass(music21.key.KeySignature)): 
                            if item.offset > 0: m.remove(item)
                    for n in p.flatten().notes:
                        for pitch in n.pitches:
                            if pitch.accidental and pitch.accidental.name == 'natural': pitch.accidental.displayStatus = False

                st.session_state['tonalitat'] = tonalitat_base
                
                with tempfile.NamedTemporaryFile(delete=False, suffix=".musicxml") as tmp:
                    new_score.write('musicxml', fp=tmp.name)
                    with open(tmp.name, 'rb') as f:
                        st.session_state['xml_data'] = f.read()
                
            except Exception as e:
                st.error(f"Error: {e}")

    # Si ja hi ha dades, mostrem el botó de descàrrega a la col2
    if 'xml_data' in st.session_state:
        with col2:
            st.download_button(
                label="📥 DESCARREGAR XML",
                data=st.session_state['xml_data'],
                file_name=f"exercici_funk_{st.session_state.get('tonalitat', 'C')}.musicxml",
                mime="application/vnd.recordare.musicxml+xml",
                use_container_width=True
            )
        render_musicxml(st.session_state['xml_data'])
