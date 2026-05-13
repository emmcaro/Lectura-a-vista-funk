import streamlit as st
import music21
import random
import copy
import os
import streamlit.components.v1 as components

# --- CONFIGURACIÓ INICIAL ---
try:
    us = music21.environment.UserSettings()
    us.create()
except:
    pass

st.set_page_config(page_title="Funk Generator", page_icon="🎸", layout="wide")

st.title("🎸 Funk Generator & Visualizer")

# --- RUTES ---
path_ritme = "buidat_ritmic_funk.musicxml"
path_acords = "font acords funk.musicxml"

def carregar_pool_acords(ruta):
    if not os.path.exists(ruta):
        st.error(f"⚠️ Falta: {ruta}")
        return []
    try:
        score = music21.converter.parse(ruta, format='musicxml')
        pool = []
        for el in score.parts[0].flatten().notes:
            if el.isChord:
                pool.append([p.nameWithOctave for p in el.pitches])
            elif el.isNote:
                pool.append([el.pitch.nameWithOctave])
        return pool
    except:
        return []

def visualitzar_partitura(xml_data):
    """Injecta OSMD per renderitzar el MusicXML en el navegador."""
    # Escapem les cometes del XML per no trencar el JS
    xml_str = xml_data.decode('utf-8').replace('`', '\\`').replace('$', '\\$')
    
    html_code = f"""
    <div id="osmd-container"></div>
    <script src="https://cdn.jsdelivr.net/npm/opensheetmusicdisplay@1.5.8/build/opensheetmusicdisplay.min.js"></script>
    <script>
        var osmd = new opensheetmusicdisplay.OpenSheetMusicDisplay("osmd-container", {{
            autoResize: true,
            drawTitle: false,
            drawSubtitle: false,
            drawComposer: false
        }});
        osmd.load(`{xml_str}`).then(function() {{
            osmd.render();
        }});
    </script>
    """
    components.html(html_code, height=600, scrolling=True)

# --- INTERFÍCIE ---

if st.button("🚀 Generar i Visualitzar"):
    if not os.path.exists(path_ritme):
        st.error(f"⚠️ Falta el fitxer de ritmes.")
    else:
        pool = carregar_pool_acords(path_acords)
        if pool:
            score_ritme = music21.converter.parse(path_ritme, format='musicxml')
            parts_originals = score_ritme.parts
            total_m = len(parts_originals[0].getElementsByClass(music21.stream.Measure))
            start_m = random.randint(0, max(0, total_m - 4))
            
            new_score = music21.stream.Score()
            for idx_p, part_vella in enumerate(parts_originals):
                nova_part = music21.stream.Part()
                mesures = list(part_vella.getElementsByClass(music21.stream.Measure))[start_m : start_m + 4]
                for i, m in enumerate(mesures):
                    m_nova = copy.deepcopy(m)
                    m_nova.number = i + 1 
                    if idx_p == 0: # Dreta
                        for n in m_nova.flatten().notes:
                            nou_set = random.choice(pool)
                            acord_nou = music21.chord.Chord(nou_set)
                            acord_nou.duration = n.duration
                            acord_nou.articulations = n.articulations
                            m_nova.replace(n, acord_nou)
                    nova_part.append(m_nova)
                new_score.insert(0, nova_part)
            
            # Generem dades
            tmp_fp = new_score.write('musicxml')
            with open(tmp_fp, 'rb') as f:
                xml_data = f.read()
            
            st.success(f"Generat! Compassos {start_m+1} a {start_m+4}")
            
            # --- VISUALITZACIÓ ---
            st.subheader("Visualització en pantalla:")
            visualitzar_partitura(xml_data)
            
            # --- DESCÀRREGA ---
            st.download_button(
                label="⬇️ Descarregar MusicXML",
                data=xml_data,
                file_name="funk_generat.musicxml",
                mime="application/vnd.recordare.musicxml+xml"
            )
            
            if os.path.exists(tmp_fp):
                os.remove(tmp_fp)
