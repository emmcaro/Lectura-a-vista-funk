import streamlit as st
import music21
import os
import random
import copy
import tempfile
import streamlit.components.v1 as components

# --- CONFIGURACIÓ ---
st.set_page_config(page_title="Funk Generator Pro", page_icon="🎸", layout="wide")
st.title("🎸 Funk Generator: Fa Major & Layout")

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
            drawingParameters: "compacttight",
            drawPartNames: false
        }});
        osmd.load(`{xml_str}`).then(() => osmd.render());
    </script>
    """
    components.html(html_code, height=700, scrolling=True)

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
    st.error("⚠️ No es troben els fitxers .musicxml.")
else:
    if st.button("🚀 Generar en Fa Major (2 compassos/línia)", use_container_width=True):
        with st.spinner("Preparant el layout... 📐"):
            try:
                pool_acords = carregar_pool_acords(path_acords)
                score_ritme = music21.converter.parse(path_ritme)
                
                num_mesures = len(score_ritme.parts[0].getElementsByClass(music21.stream.Measure))
                start_m = random.randint(0, max(0, num_mesures - 4))
                
                new_score = music21.stream.Score()
                
                # Definim l'armadura de Fa Major (1 bemoll)
                armadura_fa = music21.key.KeySignature(-1) 
                
                for idx_p, part_original in enumerate(score_ritme.parts):
                    nova_part = music21.stream.Part()
                    
                    # 1. Configurar l'inici de la part (Clau i Armadura)
                    if idx_p == 0:
                        nova_part.insert(0, music21.clef.TrebleClef())
                    else:
                        nova_part.insert(0, music21.clef.BassClef())
                    
                    nova_part.insert(0, armadura_fa)

                    mesures_originals = list(part_original.getElementsByClass(music21.stream.Measure))
                    seleccio = mesures_originals[start_m : start_m + 4]
                    
                    for i, m in enumerate(seleccio):
                        m_nova = copy.deepcopy(m)
                        m_nova.number = i + 1 # Re-numerar compassos de 1 a 4
                        
                        # 2. Forçar salt de línia al compàs 3 (per tenir 2 per línia)
                        if i == 2: # L'índex 2 és el tercer compàs
                            m_nova.insert(0, music21.layout.SystemLayout(isNew=True))
                        
                        # Substitució d'acords a la mà dreta
                        if idx_p == 0: 
                            for n in m_nova.flatten().notes:
                                nou_set = random.choice(pool_acords)
                                acord_nou = music21.chord.Chord(nou_set)
                                acord_nou.duration = n.duration
                                m_nova.replace(n, acord_nou)
                        
                        m_nova.makeBeams(inPlace=True)
                        nova_part.append(m_nova)
                    
                    # Consolidar notació
                    nova_part = nova_part.makeNotation()
                    new_score.insert(0, nova_part)

                # Exportació
                with tempfile.NamedTemporaryFile(delete=False, suffix=".musicxml") as tmp:
                    new_score.write('musicxml', fp=tmp.name)
                    with open(tmp.name, 'rb') as f:
                        xml_data = f.read()

                st.subheader(f"🎼 Funk en Fa Major (Compassos {start_m+1}-{start_m+4})")
                render_musicxml(xml_data)
                
                st.download_button(
                    label="📥 Descarregar XML (Fa Major)",
                    data=xml_data,
                    file_name="funk_Fa_Major.musicxml",
                    mime="application/vnd.recordare.musicxml+xml",
                    use_container_width=True
                )
                
            except Exception as e:
                st.error(f"Error: {e}")
