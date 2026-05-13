import streamlit as st
import music21
import os
import random
import copy
import tempfile
import streamlit.components.v1 as components

# --- CONFIGURACIÓ ---
st.set_page_config(page_title="Funk Generator Logic", page_icon="🎸", layout="wide")
st.title("🎸 Funk Generator: Estructura 1=3 i Coherència Harmònica")

base_path = os.path.dirname(__file__) if "__file__" in locals() else os.getcwd()
nom_ritme = "buidat_ritmic_funk.musicxml"
nom_acords = "font acords funk.musicxml"
path_ritme = os.path.join(base_path, nom_ritme)
path_acords = os.path.join(base_path, nom_acords)

def render_musicxml(xml_data):
    xml_str = xml_data.decode('utf-8').replace('`', '\\`').replace('$', '\\$')
    html_code = f"""
    <div id="score-container"></div>
    <script src="https://cdn.jsdelivr.net/npm/opensheetmusicdisplay@1.5.8/build/opensheetmusicdisplay.min.js"></script>
    <script>
        const osmd = new opensheetmusicdisplay.OpenSheetMusicDisplay("score-container", {{
            autoResize: true, drawTitle: false, drawingParameters: "compacttight", drawPartNames: false
        }});
        osmd.load(`{xml_str}`).then(() => osmd.render());
    </script>
    """
    components.html(html_code, height=700, scrolling=True)

# --- NOVA FUNCIÓ PER GRUP D'ACORDS PER COMPÀS ---
@st.cache_data
def carregar_pool_per_compassos(ruta):
    try:
        score = music21.converter.parse(ruta)
        pool_per_m = []
        part = score.parts[0]
        for m in part.getElementsByClass(music21.stream.Measure):
            notes_compas = []
            for el in m.flatten().notes:
                if el.isChord: notes_compas.append([p.nameWithOctave for p in el.pitches])
                elif el.isNote: notes_compas.append([el.pitch.nameWithOctave])
            if notes_compas: # Només afegim si el compàs no és buit
                pool_per_m.append(notes_compas)
        return pool_per_m
    except: return None

# --- LÒGICA ---
if not os.path.exists(path_ritme) or not os.path.exists(path_acords):
    st.error("⚠️ No es troben els fitxers .musicxml.")
else:
    if st.button("🚀 Generar amb Estructura 1=3", use_container_width=True):
        with st.spinner("Dissenyant l'estructura harmònica... 🧠"):
            try:
                # 1. Carreguem el pool estructurat per compassos
                pool_compassos = carregar_pool_per_compassos(path_acords)
                score_ritme = music21.converter.parse(path_ritme)
                
                # 2. Triem el compàs d'acords de referència per a l'exercici
                # Aquests seran els únics acords disponibles per a la Mà Dreta
                acords_referencia = random.choice(pool_compassos)
                
                num_m_ritme = len(score_ritme.parts[0].getElementsByClass(music21.stream.Measure))
                start_m = random.randint(0, max(0, num_m_ritme - 4))
                
                new_score = music21.stream.Score()
                armadura_fa = music21.key.KeySignature(-1) 
                
                # Guardarem els compassos generats per poder repetir el 1 al 3
                compassos_memoria = {0: None, 1: None, 2: None, 3: None}

                for idx_p, part_original in enumerate(score_ritme.parts):
                    nova_part = music21.stream.Part()
                    nova_part.insert(0, music21.clef.TrebleClef() if idx_p == 0 else music21.clef.BassClef())
                    nova_part.insert(0, armadura_fa)

                    mesures_originals = list(part_original.getElementsByClass(music21.stream.Measure))
                    seleccio = mesures_originals[start_m : start_m + 4]
                    
                    for i, m in enumerate(seleccio):
                        # LÒGICA ESTRUCTURAL: Si és el compàs 3 (índex 2) i som a la mateixa part, 
                        # recuperem el compàs 1 (índex 0)
                        if i == 2 and compassos_memoria[0] is not None:
                            m_nova = copy.deepcopy(compassos_memoria[0])
                        else:
                            m_nova = copy.deepcopy(m)
                            if idx_p == 0: # Mà dreta: apliquem combinatòria d'acords de referència
                                for n in m_nova.flatten().notes:
                                    nou_set = random.choice(acords_referencia)
                                    acord_nou = music21.chord.Chord(nou_set)
                                    acord_nou.duration = n.duration
                                    m_nova.replace(n, acord_nou)
                            
                            # Guardem a la memòria (per a la mà esquerra també si cal repetir-la)
                            if i == 0: compassos_memoria[0] = copy.deepcopy(m_nova)
                        
                        m_nova.number = i + 1
                        if i == 2: m_nova.insert(0, music21.layout.SystemLayout(isNew=True))
                        
                        m_nova.makeBeams(inPlace=True)
                        nova_part.append(m_nova)
                    
                    nova_part = nova_part.makeNotation()
                    new_score.insert(0, nova_part)

                # Exportació
                with tempfile.NamedTemporaryFile(delete=False, suffix=".musicxml") as tmp:
                    new_score.write('musicxml', fp=tmp.name)
                    with open(tmp.name, 'rb') as f:
                        xml_data = f.read()

                st.subheader("🎼 Estructura: A - B - A - C")
                render_musicxml(xml_data)
                
                st.download_button(
                    label="📥 Descarregar XML (Estructura 1=3)",
                    data=xml_data,
                    file_name="funk_estructurat.musicxml",
                    mime="application/vnd.recordare.musicxml+xml",
                    use_container_width=True
                )
                
            except Exception as e:
                st.error(f"Error: {e}")
