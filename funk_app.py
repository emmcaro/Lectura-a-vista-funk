import streamlit as st
import music21
import os
import random
import copy
import tempfile
import streamlit.components.v1 as components

# --- CONFIGURACIÓ DE PÀGINA ---
st.set_page_config(page_title="Funk Generator AABB", page_icon="🎸", layout="wide")

st.title("🎸 Funk Generator: AABB Harmonitzat")
st.markdown("Estructura: **1=2** i **3=4**. Partitura neta sense alteracions de precaució i mida gran.")

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
    <div id="score-container" style="width: 100%;"></div>
    <script src="https://cdn.jsdelivr.net/npm/opensheetmusicdisplay@1.5.8/build/opensheetmusicdisplay.min.js"></script>
    <script>
        const osmd = new opensheetmusicdisplay.OpenSheetMusicDisplay("score-container", {{
            autoResize: true,
            drawTitle: false,
            drawPartNames: false,
            drawingParameters: "compacttight"
        }});
        osmd.setOptions({{
            zoom: 1.8, // <-- FONT MÉS GRAN (Abans 1.5)
            spacingFactor: 1.5,
            newSystemsFromMusicXml: true,
            pageFormat: "Endless"
        }});
        osmd.load(`{xml_str}`).then(() => {{
            osmd.Sheet.Rules.PageWidth = 80; 
            osmd.render();
        }});
    </script>
    """
    components.html(html_code, height=850, width=1000)

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

# --- LÒGICA DE GENERACIÓ ---
if not os.path.exists(path_ritme) or not os.path.exists(path_acords):
    st.error("⚠️ No es troben els fitxers .musicxml.")
else:
    if st.button("🔥 GENERAR EXERCICI A-A-B-B", use_container_width=True):
        with st.spinner("Sincronitzant mans, netejant alteracions i ampliant font..."):
            try:
                pool_compassos = carregar_pool_per_compassos(path_acords)
                score_ritme = music21.converter.parse(path_ritme)
                
                acords_A = random.choice(pool_compassos)
                acords_B = random.choice(pool_compassos)
                
                desti_m2 = random.choice(['Db', 'F'])
                desti_m4 = random.choice(['Db', 'F'])
                
                itvl_m2 = music21.interval.Interval(music21.pitch.Pitch('C'), music21.pitch.Pitch(desti_m2))
                itvl_m4 = music21.interval.Interval(music21.pitch.Pitch('C'), music21.pitch.Pitch(desti_m4))
                
                new_score = music21.stream.Score()
                armadura_fa = music21.key.KeySignature(-1) 
                
                memoria_A = {}
                memoria_B = {}

                num_m_originals = len(score_ritme.parts[0].getElementsByClass(music21.stream.Measure))
                start_m = random.randint(0, max(0, num_m_originals - 4))

                for idx_p, part_original in enumerate(score_ritme.parts):
                    nova_part = music21.stream.Part()
                    nova_part.insert(0, music21.clef.TrebleClef() if idx_p == 0 else music21.clef.BassClef())
                    nova_part.insert(0, armadura_fa)

                    mesures_originals = list(part_original.getElementsByClass(music21.stream.Measure))
                    seleccio = mesures_originals[start_m : start_m + 4]
                    
                    for i in range(4):
                        if i == 0: 
                            m_nova = copy.deepcopy(seleccio[0])
                            if idx_p == 0: 
                                for n in m_nova.flatten().notes:
                                    nou_acord = music21.chord.Chord(random.choice(acords_A))
                                    nou_acord.duration = n.duration
                                    m_nova.replace(n, nou_acord)
                            memoria_A[idx_p] = copy.deepcopy(m_nova)
                            
                        elif i == 1: 
                            m_nova = copy.deepcopy(memoria_A[idx_p])
                            m_nova.transpose(itvl_m2, inPlace=True)

                        elif i == 2: 
                            m_nova = copy.deepcopy(seleccio[2])
                            if idx_p == 0:
                                for n in m_nova.flatten().notes:
                                    nou_acord = music21.chord.Chord(random.choice(acords_B))
                                    nou_acord.duration = n.duration
                                    m_nova.replace(n, nou_acord)
                            memoria_B[idx_p] = copy.deepcopy(m_nova)
                            m_nova.insert(0, music21.layout.SystemLayout(isNew=True))
                            
                        elif i == 3: 
                            m_nova = copy.deepcopy(memoria_B[idx_p])
                            m_nova.transpose(itvl_m4, inPlace=True)

                        m_nova.number = i + 1
                        m_nova.makeBeams(inPlace=True)
                        nova_part.append(m_nova)
                    
                    # Generem notació (Això crea els becuadros de precaució)
                    nova_part = nova_part.makeNotation()
                    
                    # NETEJA D'ALTERACIONS (Ocultem els naturals/becuadros)
                    for p in nova_part.flatten().pitches:
                        if p.accidental is not None and p.accidental.name == 'natural':
                            p.accidental.displayStatus = False

                    new_score.insert(0, nova_part)

                with tempfile.NamedTemporaryFile(delete=False, suffix=".musicxml") as tmp:
                    new_score.write('musicxml', fp=tmp.name)
                    with open(tmp.name, 'rb') as f:
                        xml_data = f.read()

                st.subheader(f"🎼 Estructura: C7 | {desti_m2}7 | C7 | {desti_m4}7")
                render_musicxml(xml_data)
                st.download_button(label="📥 Descarregar XML", data=xml_data, file_name="funk_AABB_dinamic_net.musicxml")
                
            except Exception as e:
                st.error(f"Error: {e}")
