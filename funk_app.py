Entesos, fem marxa enrere i ens quedem exactament amb aquesta versió neta, estable i funcional. Sense experiments, només l'estructura AABB i els acords purs.

Aquí tens el codi restaurat tal com l'has demanat:

```python
import streamlit as st
import music21
import os
import random
import copy
import tempfile
import streamlit.components.v1 as components

# --- CONFIGURACIÓ DE PÀGINA ---
st.set_page_config(page_title="Funk Generator AABB", page_icon="🎸", layout="wide")

st.title("🎸 Funk Generator: Estètica Professional")

# --- RUTES ---
base_path = os.path.dirname(__file__) if "__file__" in locals() else os.getcwd()
nom_ritme = "buidat_ritmic_funk.musicxml"
nom_acords = "font acords funk.musicxml"
path_ritme = os.path.join(base_path, nom_ritme)
path_acords = os.path.join(base_path, nom_acords)

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
            autoResize: true,
            drawTitle: false,
            drawComposer: false,
            drawPartNames: false,
            drawPartAbbreviations: false,
            drawMetronomeMarks: false,
            drawMeasureNumbers: false,
            drawingParameters: "default"
        }});
        osmd.setOptions({{
            zoom: 2.0, 
            spacingFactor: 1.5, 
            newSystemsFromMusicXml: true, 
            pageFormat: "Endless",
            pageBackgroundColor: "#FFFFFF"
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

# --- LÒGICA DE GENERACIÓ I INTERFÍCIE ---
if not os.path.exists(path_ritme) or not os.path.exists(path_acords):
    st.error("⚠️ Falten fitxers XML.")
else:
    # Creem dues columnes per posar els botons de costat
    col1, col2 = st.columns(2)
    
    with col1:
        boto_generar = st.button("🔥 GENERAR EXERCICI NET", use_container_width=True)

    if boto_generar:
        with st.spinner("Generant..."):
            try:
                pool_compassos = carregar_pool_per_compassos(path_acords)
                score_ritme = music21.converter.parse(path_ritme)
                
                desti_m2 = random.choice(['Db', 'F'])
                desti_m4 = random.choice(['Db', 'F'])
                itvl_m2 = music21.interval.Interval(music21.pitch.Pitch('C'), music21.pitch.Pitch(desti_m2))
                itvl_m4 = music21.interval.Interval(music21.pitch.Pitch('C'), music21.pitch.Pitch(desti_m4))
                
                new_score = music21.stream.Score()
                
                new_score.insert(0, music21.metadata.Metadata())
                new_score.metadata.title = ''
                new_score.metadata.composer = ''
                
                armadura_fa = music21.key.KeySignature(-1) 
                memoria_A, memoria_B = {}, {}

                num_m_originals = len(score_ritme.parts[0].getElementsByClass(music21.stream.Measure))
                start_m = random.randint(0, max(0, num_m_originals - 4))

                for idx_p, part_original in enumerate(score_ritme.parts):
                    nova_part = music21.stream.Part()
                    nova_part.partName = ""
                    nova_part.partAbbreviation = ""
                    
                    nova_part.insert(0, music21.clef.TrebleClef() if idx_p == 0 else music21.clef.BassClef())
                    nova_part.insert(0, armadura_fa)
                    mesures_originals = list(part_original.getElementsByClass(music21.stream.Measure))
                    seleccio = mesures_originals[start_m : start_m + 4]
                    
                    for i in range(4):
                        if i == 0: 
                            m_nova = copy.deepcopy(seleccio[0])
                            if idx_p == 0: 
                                grup_A = random.choice(pool_compassos)
                                for n in m_nova.flatten().notes:
                                    n_nova = music21.chord.Chord(random.choice(grup_A))
                                    n_nova.duration = n.duration
                                    m_nova.replace(n, n_nova)
                            memoria_A[idx_p] = copy.deepcopy(m_nova)
                        elif i == 1: 
                            m_nova = copy.deepcopy(memoria_A[idx_p])
                            m_nova.transpose(itvl_m2, inPlace=True)
                        elif i == 2: 
                            m_nova = copy.deepcopy(seleccio[2])
                            if idx_p == 0:
                                grup_B = random.choice(pool_compassos)
                                for n in m_nova.flatten().notes:
                                    n_nova = music21.chord.Chord(random.choice(grup_B))
                                    n_nova.duration = n.duration
                                    m_nova.replace(n, n_nova)
                            memoria_B[idx_p] = copy.deepcopy(m_nova)
                            m_nova.insert(0, music21.layout.SystemLayout(isNew=True))
                        elif i == 3: 
                            m_nova = copy.deepcopy(memoria_B[idx_p])
                            m_nova.transpose(itvl_m4, inPlace=True)
                            m_nova.rightBarline = music21.bar.Barline('final')

                        m_nova.number = i + 1
                        m_nova.makeBeams(inPlace=True)
                        nova_part.append(m_nova)
                    
                    nova_part = nova_part.makeNotation()
                    
                    for p in nova_part.flatten().pitches:
                        if p.accidental and p.accidental.name == 'natural':
                            p.accidental.displayStatus = False

                    new_score.insert(0, nova_part)

                agrupacio_piano = music21.layout.StaffGroup(
                    list(new_score.parts), 
                    symbol='brace', 
                    barTogether=True
                )
                new_score.insert(0, agrupacio_piano)

                with tempfile.NamedTemporaryFile(delete=False, suffix=".musicxml") as tmp:
                    new_score.write('musicxml', fp=tmp.name)
                    with open(tmp.name, 'rb') as f:
                        xml_data = f.read()

                # Guardem les dades a la memòria de la sessió
                st.session_state['xml_data'] = xml_data
                st.session_state['desti_m2'] = desti_m2
                st.session_state['desti_m4'] = desti_m4
                
            except Exception as e:
                st.error(f"Error: {e}")

    # Si tenim l'XML guardat a la sessió, mostrem el botó de descàrrega i el visualitzador
    if 'xml_data' in st.session_state:
        with col2:
            st.download_button(
                label="📥 Descarregar XML", 
                data=st.session_state['xml_data'], 
                file_name="funk_AABB_final.musicxml",
                mime="application/vnd.recordare.musicxml+xml",
                use_container_width=True
            )
            
        render_musicxml(st.session_state['xml_data'])

```
