import streamlit as st
import music21
import os
import random
import copy
import tempfile
import streamlit.components.v1 as components

# --- CONFIGURACIÓ DE PÀGINA ---
st.set_page_config(page_title="Funk Generator Mixolydian", page_icon="🎸", layout="wide")

st.title("🎸 Funk Generator: Lògica Harmònica C7")
st.markdown("Estructura: **1=3** (C7) | **2 i 4** (Db7 o F7). Disseny forçat 2x2.")

# --- RUTES ---
base_path = os.path.dirname(__file__) if "__file__" in locals() else os.getcwd()
nom_ritme = "buidat_ritmic_funk.musicxml"
nom_acords = "font acords funk.musicxml" # Aquest fitxer s'usarà per al "ritme" dels acords
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
            zoom: 1.3,
            spacingFactor: 1.4,
            newSystemsFromMusicXml: true,
            drawFromMeasureNumber: 1,
            drawUpToMeasureNumber: 4
        }});

        osmd.load(`{xml_str}`).then(() => {{
            // TRUC DE DISSENY: Forcem que cada compàs sigui molt ample
            // Això obliga a que només n'hi caben 2 per línia en el contenidor
            osmd.Sheet.Rules.MinMeasureWidth = 50; 
            osmd.render();
        }});
    </script>
    """
    components.html(html_code, height=750, width=1100)

# --- DEFINICIÓ D'ACORDS FIXES ---
# Definim les veus dels acords (voicings) per a C7, Db7 i F7
acords_vincle = {
    "I": [['C3', 'E3', 'Bb3', 'D4'], ['C3', 'Bb3', 'E4', 'G4']], # C7 (mixolidi)
    "bII": [['Db3', 'F3', 'B3', 'Eb4'], ['Db3', 'B3', 'F4', 'Ab4']], # Db7 (subV)
    "IV": [['F2', 'A3', 'Eb4', 'G4'], ['F2', 'Eb4', 'A4', 'C5']]  # F7
}

# --- LÒGICA DE GENERACIÓ ---
if not os.path.exists(path_ritme):
    st.error(f"⚠️ No s'ha trobat el fitxer de ritme: {nom_ritme}")
else:
    if st.button("🔥 GENERAR GROOVE C7 - Mixolidi", use_container_width=True):
        with st.spinner("Assignant graus harmònics..."):
            try:
                score_ritme = music21.converter.parse(path_ritme)
                new_score = music21.stream.Score()
                armadura_fa = music21.key.KeySignature(-1) # Mantenim Fa Major (per el Bb de C7)

                num_m_originals = len(score_ritme.parts[0].getElementsByClass(music21.stream.Measure))
                start_m = random.randint(0, max(0, num_m_originals - 4))
                
                # Triem quin acord anirà als compassos parells (2 i 4)
                acord_parell_grau = random.choice(["bII", "IV"])
                
                memoria_compassos = {}

                for idx_p, part_original in enumerate(score_ritme.parts):
                    nova_part = music21.stream.Part()
                    nova_part.insert(0, music21.clef.TrebleClef() if idx_p == 0 else music21.clef.BassClef())
                    nova_part.insert(0, armadura_fa)

                    mesures_originals = list(part_original.getElementsByClass(music21.stream.Measure))
                    seleccio = mesures_originals[start_m : start_m + 4]
                    
                    for i, m in enumerate(seleccio):
                        m_nova = copy.deepcopy(m)
                        m_nova.number = i + 1
                        
                        # Determinem quin "grau" toca segons el compàs
                        if i == 0 or i == 2: # Compàs 1 i 3 (C7)
                            grau_actual = "I"
                        else: # Compàs 2 i 4 (Db7 o F7)
                            grau_actual = acord_parell_grau

                        if idx_p == 0: # Mà dreta: assignem les notes de l'acord triat
                            pool_voicings = acords_vincle[grau_actual]
                            voicing_escollit = random.choice(pool_voicings)
                            
                            for n in m_nova.flatten().notes:
                                nou_acord = music21.chord.Chord(voicing_escollit)
                                nou_acord.duration = n.duration
                                m_nova.replace(n, nou_acord)

                        # Forçar salt de línia al compàs 3
                        if i == 2:
                            m_nova.insert(0, music21.layout.SystemLayout(isNew=True))
                        
                        m_nova.makeBeams(inPlace=True)
                        nova_part.append(m_nova)
                    
                    nova_part = nova_part.makeNotation()
                    new_score.insert(0, nova_part)

                with tempfile.NamedTemporaryFile(delete=False, suffix=".musicxml") as tmp:
                    new_score.write('musicxml', fp=tmp.name)
                    with open(tmp.name, 'rb') as f:
                        xml_data = f.read()

                st.subheader(f"🎼 Estructura: C7 (1,3) i {acord_parell_grau}7 (2,4)")
                render_musicxml(xml_data)
                
                st.download_button(label="📥 Descarregar XML", data=xml_data, 
                                 file_name="funk_mixolidi.musicxml", 
                                 mime="application/vnd.recordare.musicxml+xml",
                                 use_container_width=True)
                
            except Exception as e:
                st.error(f"Error: {e}")
