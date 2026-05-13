import streamlit as st
import music21
import os
import random
import copy
import tempfile
import streamlit.components.v1 as components

# Configuració
st.set_page_config(page_title="Funk Generator & Viewer", page_icon="🎸", layout="wide")
st.title("🎸 Funk Generator + 🎼 Visualitzador")

base_path = os.path.dirname(__file__) if "__file__" in locals() else os.getcwd()
nom_ritme = "buidat_ritmic_funk.musicxml"
nom_acords = "font acords funk.musicxml"
path_ritme = os.path.join(base_path, nom_ritme)
path_acords = os.path.join(base_path, nom_acords)

# --- FUNCIÓ PER VISUALITZAR (JavaScript) ---
def render_musicxml(xml_data):
    """Injecta JavaScript per renderitzar el MusicXML al navegador."""
    xml_str = xml_data.decode('utf-8').replace('`', '\\`')
    html_code = f"""
    <div id="score-container"></div>
    <script src="https://cdn.jsdelivr.net/npm/opensheetmusicdisplay@1.5.8/build/opensheetmusicdisplay.min.js"></script>
    <script>
        const osmd = new opensheetmusicdisplay.OpenSheetMusicDisplay("score-container", {{
            autoResize: true,
            drawTitle: false,
        }});
        osmd.load(`{xml_str}`).then(() => osmd.render());
    </script>
    """
    components.html(html_code, height=500, scrolling=True)

@st.cache_data
def carregar_pool_acords(ruta):
    score = music21.converter.parse(ruta)
    pool = []
    part = score.parts[0]
    for el in part.flatten().notes:
        if el.isChord: pool.append([p.nameWithOctave for p in el.pitches])
        elif el.isNote: pool.append([el.pitch.nameWithOctave])
    return pool

# --- INTERFÍCIE I LÒGICA ---
if not os.path.exists(path_ritme) or not os.path.exists(path_acords):
    st.error("⚠️ Fitxers no trobats.")
    st.info(f"Assegura't que '{nom_ritme}' i '{nom_acords}' estan al teu GitHub.")
else:
    if st.button("🔥 Generar i Veure Partitura", use_container_width=True):
        with st.spinner("Dibuixant la partitura... ✍️"):
            try:
                pool_acords = carregar_pool_acords(path_acords)
                score_ritme = music21.converter.parse(path_ritme)
                
                # Generació de 4 compassos
                part_original = score_ritme.parts[0]
                mesures_totals = list(part_original.getElementsByClass(music21.stream.Measure))
                start_m = random.randint(0, max(0, len(mesures_totals) - 4))

                new_score = music21.stream.Score()
                nova_part = music21.stream.Part()
                
                for m in mesures_totals[start_m : start_m + 4]:
                    m_nova = copy.deepcopy(m)
                    for n in m_nova.flatten().notes:
                        new_chord = music21.chord.Chord(random.choice(pool_acords))
                        new_chord.duration = n.duration
                        m_nova.replace(n, new_chord)
                    nova_part.append(m_nova)
                
                new_score.insert(0, nova_part)

                # Exportar per a visualitzador i descàrrega
                with tempfile.NamedTemporaryFile(delete=False, suffix=".musicxml") as tmp:
                    new_score.write('musicxml', fp=tmp.name)
                    with open(tmp.name, 'rb') as f:
                        xml_data = f.read()

                # --- MOSTRAR RESULTATS ---
                st.subheader("🎼 Partitura Generada")
                render_musicxml(xml_data) # <--- AQUÍ ES MOSTRA
                
                st.download_button(
                    label="📥 Descarregar XML",
                    data=xml_data,
                    file_name="funk_reading.musicxml",
                    mime="application/vnd.recordare.musicxml+xml",
                    use_container_width=True
                )
                
            except Exception as e:
                st.error(f"Error: {e}")

st.divider()
st.caption("Fent servir OpenSheetMusicDisplay per a la renderització web.")
