import streamlit as st
import music21
import os
import random
import copy
import tempfile
import streamlit.components.v1 as components

# --- CONFIGURACIÓ ---
st.set_page_config(page_title="Funk Generator Full", page_icon="🎸", layout="wide")
st.title("🎸 Funk Generator (Mà Dreta + Esquerra)")

base_path = os.path.dirname(__file__) if "__file__" in locals() else os.getcwd()
nom_ritme = "buidat_ritmic_funk.musicxml"
nom_acords = "font acords funk.musicxml"
path_ritme = os.path.join(base_path, nom_ritme)
path_acords = os.path.join(base_path, nom_acords)

# --- VISUALITZADOR JS ---
def render_musicxml(xml_data):
    xml_str = xml_data.decode('utf-8').replace('`', '\\`').replace('$', '\\$')
    html_code = f"""
    <div id="score-container"></div>
    <script src="https://cdn.jsdelivr.net/npm/opensheetmusicdisplay@1.5.8/build/opensheetmusicdisplay.min.js"></script>
    <script>
        const osmd = new opensheetmusicdisplay.OpenSheetMusicDisplay("score-container", {{
            autoResize: true,
            drawTitle: false,
            drawingParameters: "compacttight"
        }});
        osmd.load(`{xml_str}`).then(() => osmd.render());
    </script>
    """
    components.html(html_code, height=600, scrolling=True)

@st.cache_data
def carregar_pool_acords(ruta):
    try:
        score = music21.converter.parse(ruta)
        pool = []
        for el in score.parts[0].flatten().notes:
            if el.isChord: pool.append([p.nameWithOctave for p in el.pitches])
            elif el.isNote: pool.append([el.pitch.nameWithOctave])
        return pool
    except: return None

# --- LÒGICA ---
if not os.path.exists(path_ritme) or not os.path.exists(path_acords):
    st.error("⚠️ No es troben els fitxers .musicxml al repositori.")
else:
    if st.button("🔥 Generar Groove Complet (2 mans)", use_container_width=True):
        with st.spinner("Sincronitzant mans... 🕺"):
            try:
                pool_acords = carregar_pool_acords(path_acords)
                score_ritme = music21.converter.parse(path_ritme)
                
                # Calculem el punt d'inici un sol cop per a totes les mans
                num_mesures = len(score_ritme.parts[0].getElementsByClass(music21.stream.Measure))
                start_m = random.randint(0, max(0, num_mesures - 4))
                
                new_score = music21.stream.Score()
                
                # Iterem per TOTES les parts del fitxer de ritme
                for idx_p, part_original in enumerate(score_ritme.parts):
                    nova_part = music21.stream.Part()
                    
                    # Copiem metadades de la part (nom, clau, etc.)
                    mesures_originals = list(part_original.getElementsByClass(music21.stream.Measure))
                    seleccio = mesures_originals[start_m : start_m + 4]
                    
                    for m in seleccio:
                        m_nova = copy.deepcopy(m)
                        
                        # NOMÉS modifiquem la Mà Dreta (Part 0) amb els acords
                        # La Mà Esquerra (Part 1) es queda amb el ritme/notes originals
                        if idx_p == 0: 
                            for n in m_nova.flatten().notes:
                                nou_set = random.choice(pool_acords)
                                new_chord = music21.chord.Chord(nou_set)
                                new_chord.duration = n.duration
                                m_nova.replace(n, new_chord)
                        
                        nova_part.append(m_nova)
                    
                    new_score.insert(0, nova_part) # Afegim la part (dreta o esquerra) al score final

                # Exportació
                with tempfile.NamedTemporaryFile(delete=False, suffix=".musicxml") as tmp:
                    new_score.write('musicxml', fp=tmp.name)
                    with open(tmp.name, 'rb') as f:
                        xml_data = f.read()

                # Visualització i Descàrrega
                st.subheader(f"🎼 Exercici Generat (Compassos {start_m+1}-{start_m+4})")
                render_musicxml(xml_data)
                
                st.download_button(
                    label="📥 Descarregar Partitura Completa (XML)",
                    data=xml_data,
                    file_name="funk_2_mans.musicxml",
                    mime="application/vnd.recordare.musicxml+xml",
                    use_container_width=True
                )
                
            except Exception as e:
                st.error(f"Error en la generació: {e}")
