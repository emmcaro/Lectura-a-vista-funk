import streamlit as st
import music21
import os
import random
import copy
import tempfile
import streamlit.components.v1 as components

# --- CONFIGURACIÓ DE PÀGINA ---
st.set_page_config(page_title="Funk Generator Pro", page_icon="🎸", layout="wide")

st.title("🎸 Funk Generator: Mixolidi & Semicorxeres")
st.markdown("""
- **Lògica Mixolídia**: Si la tònica és C7, l'armadura serà de Fa Major.
- **Detector de Ratxes**: Melodia de blues només en grups de 3-4 semicorxeres sense silencis entremig.
- **Maquetació**: 2 compassos per línia exactes.
""")

# --- FUNCIONS DE SUPORT ---

def obtenir_escala_blues_base():
    """Escala de blues de Do amb l'ortografia de F# corregida."""
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
            zoom: 1.4,
            spacingFactor: 1.0,
            newSystemsFromMusicXml: true,
            pageFormat: "A4",
            pageBackgroundColor: "#FFFFFF"
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
    st.error("⚠️ Falten fitxers XML a la carpeta del projecte.")
else:
    col1, col2 = st.columns(2)
    with col1:
        boto_generar = st.button("🎲 GENERAR EXERCICI UNIVERSAL", use_container_width=True)

    if boto_generar:
        with st.spinner("Generant rítmica, melodia i aplicant Mixolidi..."):
            try:
                pool_compassos = carregar_pool_per_compassos(path_acords)
                score_ritme = music21.converter.parse(path_ritme)
                
                # 1. PARAMETRES ALEATORIS
                # Opcions harmòniques per compassos 2 i 4 (Db, F, G respecte a Do)
                opcions_itvl = [music21.interval.Interval('m2'), music21.interval.Interval('P4'), music21.interval.Interval('P5')]
                itvl_c2 = random.choice(opcions_itvl)
                itvl_c4 = random.choice(opcions_itvl)
                
                # Tonalitat Mixolídia final
                tonalitat_base = random.choice(['C', 'G', 'D', 'A', 'E', 'B', 'F#', 'F', 'Bb', 'Eb', 'Ab', 'Db'])
                p_tonica = music21.pitch.Pitch(tonalitat_base)
                p_armadura = p_tonica.transpose('P4') # Regla Mixolídia: Armadura de la IV
                sharps = music21.key.Key(p_armadura.name).sharps
                
                new_score = music21.stream.Score()
                memoria_A, memoria_B = {}, {}
                escala_blues = obtenir_escala_blues_base()

                num_m_originals = len(score_ritme.parts[0].getElementsByClass(music21.stream.Measure))
                start_m = random.randint(0, max(0, num_m_originals - 4))

                # 2. CONSTRUCCIÓ EN DO
                for idx_p, part_original in enumerate(score_ritme.parts):
                    nova_part = music21.stream.Part()
                    nova_part.insert(0, music21.clef.TrebleClef() if idx_p == 0 else music21.clef.BassClef())
                    
                    mesures_originals = list(part_original.getElementsByClass(music21.stream.Measure))
                    seleccio = mesures_originals[start_m : start_m + 4]
                    
                    for i in range(4):
                        if i in [0, 2]: # Compassos base 1 i 3
                            m_nova = copy.deepcopy(seleccio[i])
                            g_acords = random.choice(pool_compassos) # Pool d'acords per aquest compàs
                            
                            if idx_p == 0: # Analitzem rítmica a la mà dreta
                                notes_soles = list(m_nova.flatten().notes)
                                ratxes = []
                                ratxa_actual = []
                                
                                # DETECTOR DE CONTINUÏTAT TEMPORAL (SENSE SILENCIS)
                                for idx_n in range(len(notes_soles)):
                                    n_act = notes_soles[idx_n]
                                    if n_act.duration.quarterLength <= 0.25:
                                        if not ratxa_actual:
                                            ratxa_actual.append(idx_n)
                                        else:
                                            n_ant = notes_soles[ratxa_actual[-1]]
                                            # Si el final de l'anterior coincideix amb l'inici de l'actual
                                            # vol dir que no hi ha silenci entremig.
                                            distancia = n_act.offset - (n_ant.offset + n_ant.duration.quarterLength)
                                            if distancia == 0:
                                                ratxa_actual.append(idx_n)
                                            else:
                                                if 3 <= len(ratxa_actual) <= 4: ratxes.append(ratxa_actual)
                                                ratxa_actual = [idx_n]
                                    else:
                                        if 3 <= len(ratxa_actual) <= 4: ratxes.append(ratxa_actual)
                                        ratxa_actual = []
                                if 3 <= len(ratxa_actual) <= 4: ratxes.append(ratxa_actual)
                                
                                # Aplicar melodia o acords
                                indices_blues = {idx for r in ratxes for idx in r}
                                map_notes = {}
                                for r in ratxes:
                                    frase = generar_frase_blues(len(r), escala_blues)
                                    for r_idx, orig_idx in enumerate(r):
                                        map_notes[orig_idx] = frase[r_idx]

                                for idx_n, n in enumerate(notes_soles):
                                    if idx_n in indices_blues:
                                        res = music21.note.Note(map_notes[idx_n])
                                    else:
                                        res = music21.chord.Chord(random.choice(g_acords))
                                    res.duration = n.duration
                                    m_nova.replace(n, res)
                            
                            if i == 0: memoria_A[idx_p] = copy.deepcopy(m_nova)
                            else: memoria_B[idx_p] = copy.deepcopy(m_nova)

                        elif i == 1:
                            m_nova = copy.deepcopy(memoria_A[idx_p])
                            m_nova.transpose(itvl_c2, inPlace=True)
                        elif i == 3:
                            m_nova = copy.deepcopy(memoria_B[idx_p])
                            m_nova.transpose(itvl_c4, inPlace=True)
                            m_nova.rightBarline = music21.bar.Barline('final')

                        # Maquetació: 2 per línia
                        if i == 2:
                            m_nova.insert(0, music21.layout.SystemLayout(isNew=True))
                        
                        m_nova.number = i + 1
                        m_nova.makeBeams(inPlace=True)
                        nova_part.append(m_nova)
                    new_score.insert(0, nova_part)

                # 3. TRANSPOSICIÓ GLOBAL I NETEJA
                itvl_global = music21.interval.Interval(music21.pitch.Pitch('C4'), music21.pitch.Pitch(tonalitat_base + '4'))
                new_score.transpose(itvl_global, inPlace=True)
                
                ks = music21.key.KeySignature(sharps)
                for p in new_score.parts:
                    p.insert(0, ks)
                    # Neteja de fantasmes i naturals redundants
                    for m in p.getElementsByClass(music21.stream.Measure):
                        for item in list(m.getElementsByClass(music21.key.KeySignature)):
                            if item.offset > 0: m.remove(item)
                    for n in p.flatten().notes:
                        for pitch in n.pitches:
                            if pitch.accidental and pitch.accidental.name == 'natural':
                                pitch.accidental.displayStatus = False

                st.info(f"Tònica: **{tonalitat_base}7** | Armadura Mixolídia: **{p_armadura.name} Major**")
                new_score.insert(0, music21.layout.StaffGroup(list(new_score.parts), symbol='brace', barTogether=True))

                # Escriure fitxer
                with tempfile.NamedTemporaryFile(delete=False, suffix=".musicxml") as tmp:
                    new_score.write('musicxml', fp=tmp.name)
                    with open(tmp.name, 'rb') as f:
                        st.session_state['xml_data'] = f.read()
                
            except Exception as e:
                st.error(f"Error en la generació: {e}")

    if 'xml_data' in st.session_state:
        with col2:
            st.download_button(label="📥 Descarregar XML", data=st.session_state['xml_data'], 
                               file_name=f"funk_mixolydian_{random.randint(100,999)}.musicxml", use_container_width=True)
        render_musicxml(st.session_state['xml_data'])
