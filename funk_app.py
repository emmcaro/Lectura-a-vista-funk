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
try:
    base_path = os.path.dirname(__file__) if "__file__" in locals() else os.getcwd()
except Exception:
    base_path = os.getcwd()

nom_ritme = "buidat_ritmic_funk.musicxml"
nom_acords = "font_acords_funk.musicxml" # Nota: He posat un subratlla per seguretat, ajusta'l si el teu fitxer no és així
path_ritme = os.path.join(base_path, nom_ritme)
path_acords = os.path.join(base_path, nom_acords)

# --- VISUALITZADOR JS (OSMD) ---
def render_musicxml(xml_data):
    # Limpiem el string XML per evitar errors amb caràcters especials a JS
    try:
        xml_str = xml_data.decode('utf-8').replace('\r', '').replace('`', '\\`').replace('$', '\\$')
    except:
        xml_str = ""

    html_code = f"""
    <div style="background-color: #f0f2f6; padding: 10px; display: flex; justify-content: center;">
        <div style="background-color: #FFFFFF; padding: 20px; border-radius: 10px; width: 95%; max-width: 1200px; box-sizing: border-box; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
            <div id="score-container"></div>
        </div>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/opensheetmusicdisplay@1.5.8/build/opensheetmusicdisplay.min.js"></script>
    <script>
        const osmd = new opensheetmusicdisplay.OpenSheetMusicDisplay("score-container", {{
            autoResize: true,
            drawTitle: false,
            drawComposer: false,
            drawPartNames: true, 
            drawPartAbbreviations: false,
            drawMetronomeMarks: false,
            drawingParameters: "default"
        }});
        
        osmd.setOptions({{
            zoom: 2.0, 
            spacingFactor: 1.5, 
            newSystemsFromMusicXml: true, 
            pageFormat: "Endless",
            pageBackgroundColor: "#FFFFFF",
            disableScrolling: false
        }});

        osmd.load(`{xml_str}`).then(() => {{
            osmd.render();
        }}).catch(err => {{
            console.error("Error carregant el document:", err);
            const div = document.getElementById('score-container');
            div.innerHTML = "<p style='color:red;'>Error al visualitzar: Prova de descarregar i obrir el fitxer a una altra eina.</p>";
        }});
    </script>
    """
    components.html(html_code, height=900)

@st.cache_data
def carregar_pool_per_compassos(ruta):
    try:
        if not os.path.exists(ruta):
            return []
        score = music21.converter.parse(ruta)
        pool = []
        # Obtenim només la part 1 (sovint és la de veu principal o piano) per no complicar si n'hi ha diverses
        # Ombrem tots els compassos de la primera part
        part_principal = score.parts[0] if len(score.parts) > 0 else None
        
        if part_principal:
            for m in part_principal.getElementsByClass(music21.stream.Measure):
                notes = []
                for el in m.flatten().notes:
                    # Obtenim les notes com a 'Pitch' (ex: C
