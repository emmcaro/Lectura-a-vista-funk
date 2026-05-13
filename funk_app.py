import streamlit as st
import music21
import os
import random
import copy
import tempfile
import streamlit.components.v1 as components

# --- CONFIGURACIÓ DE PÀGINA ---
st.set_page_config(page_title="Funk Generator Wide", page_icon="🎸", layout="wide")

st.title("🎸 Funk Reading Generator")
st.markdown("Semicorxeres més espaiades per a una lectura més còmoda.")

# --- RUTES I FITXERS ---
base_path = os.path.dirname(__file__) if "__file__" in locals() else os.getcwd()
nom_ritme = "buidat_ritmic_funk.musicxml"
nom_acords = "font acords funk.musicxml"
path_ritme = os.path.join(base_path, nom_ritme)
path_acords = os.path.join(base_path, nom_acords)

# --- VISUALITZADOR JS (OSMD) ---
def render_musicxml(xml_data):
    xml_str = xml_data.decode('utf-8').replace('`', '\\`').replace('$', '\\$')
    html_code = f"""
    <div id="score-container"></div>
    <script src="https://cdn.jsdelivr.net/npm/opensheetmusicdisplay@1.5.8/build/opensheetmusicdisplay.min.js"></script>
    <script>
        const osmd = new opensheetmusicdisplay.OpenSheetMusicDisplay("score-container", {{
            autoResize: true,
            drawTitle: false,
            drawSubtitle: false,
            drawComposer: false,
            drawPartNames: false,
            drawingParameters: "compacttight",
            renderBackend: "svg"
        }});
        // Augmentem el zoom i forcem que el dibuix sigui més ample
        osmd.setOptions({{
            zoom: 1.4, 
            spacingFactor: 1.5, // Augmenta l'espai entre notes
            unitsPerFullMeasure: 4.0 // Força compassos més amples
        }});
        osmd.load(`{xml_str}`).then(() => osmd.render());
    </script>
    """
    # Augmentem el width del component per donar aire
    components.html(html_code, height=750, width=1200, scrolling=True)

# --- FUNCIONS DE CÀRREGA ---
@st.cache_data
def carregar_pool_per_compassos(ruta):
    try:
        score = music21.converter.parse(ruta)
        pool_per_m = []
        part = score.parts[0]
        for m in part.getElementsByClass(music21.stream.Measure):
            notes_compas = []
            for el in m.flatten().notes:
                if el.isChord:
                    notes_compas.append([p.nameWithOctave for p in el.pitches])
                elif el.isNote:
                    notes_compas.append([el.pitch.nameWithOctave])
            if notes_compas:
                pool_per_m.append(notes_compas)
        return pool_per_m
    except:
        return None

# --- LÒGICA DE GENERACIÓ ---
if not os.path.exists(path_ritme) or not os.path.exists(path_acords):
    st.error("⚠️ No es troben els fitxers .musicxml.")
else:
    if st.button("🔥 GENERAR EXERCICI ESPAIAT", use_container_width=True):
        with st.spinner("Espaiant pentagrames..."):
            try:
                pool_compassos = carregar_pool_per_compassos(path_acords)
                score_ritme = music21.converter.parse(path_ritme)
                acords_referencia = random.choice(pool_compassos)
                
                new_score = music21.stream.Score()
                armadura_fa = music21.key.KeySignature(-1) 
                
                # Ajustem l'escalat global del document perquè tot sigui més gran
                new_score.insert(0, music21.layout.ScoreLayout(scalingNumber=7.0))

                memoria_compassos = {}
                num_m_originals = len(score_ritme.parts[0].getElementsByClass(music21.stream.Measure))
                start_m = random.randint(0, max(0, num_m_originals - 4))

                for idx_p, part_original in enumerate(score_ritme.parts):
                    nova_part = music21.stream.Part()
                    nova_part.insert(0, music21.clef.TrebleClef() if idx_p == 0 else music21.clef.BassClef())
                    nova_part.insert(0, armadura_fa)

                    mesures_originals = list(part_original.getElementsByClass(music21.stream.Measure))
                    seleccio = mesures_originals[start_m : start_m + 4]
                    
                    for i, m in enumerate(seleccio):
                        if i == 2 and idx_p in memoria_compassos:
                            m_nova = copy.deepcopy(memoria_compassos[idx_p])
                            m_nova.insert(0, music21.layout.SystemLayout(isNew=True))
                        else:
                            m_nova = copy.deepcopy(m)
                            if idx_p == 0:
                                for n in m_nova.flatten().notes:
                                    acord_nou = music21.chord.Chord(random.choice(acords_referencia))
                                    acord_nou.duration = n.duration
                                    m_nova.replace(n, acord_nou)
                            if i == 0:
                                memoria_compassos[idx_p] = copy.deepcopy(m_nova)

                        m_nova.number = i + 1
                        m_nova.makeBeams(inPlace=True)
                        nova_part.append(m_nova)
                    
                    nova_part = nova_part.makeNotation()
                    new_score.insert(0, nova_part)

                with tempfile.NamedTemporaryFile(delete=False, suffix=".musicxml") as tmp:
                    new_score.write('musicxml', fp=tmp.name)
                    with open(tmp.name, 'rb') as f:
                        xml_data = f.read()

                st.subheader("🎼 Previsualització d'Alta Llegibilitat")
                render_musicxml(xml_data)
                
                st.download_button(label="📥 Descarregar XML", data=xml_data, 
                                 file_name="funk_espaiat.musicxml", 
                                 mime="application/vnd.recordare.musicxml+xml",
                                 use_container_width=True)
                
            except Exception as e:
                st.error(f"Error: {e}")
