import streamlit as st
import music21
import os
import random
import copy
import tempfile
import streamlit.components.v1 as components

# --- CONFIGURACIÓ DE PÀGINA ---
st.set_page_config(page_title="Funk Generator Pro", page_icon="🎸", layout="wide")

st.title("🎸 Funk Reading Generator")
st.markdown("Generació aleatòria amb estructura **1=3**, Fa Major i layout de 2 compassos per línia.")

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
        osmd.setOptions({{
            zoom: 1.1,
            drawingParameters: "compacttight"
        }});
        osmd.load(`{xml_str}`).then(() => osmd.render());
    </script>
    """
    components.html(html_code, height=600, width=1000, scrolling=True)

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
    except Exception as e:
        st.error(f"Error carregant acords: {e}")
        return None

# --- LÒGICA DE GENERACIÓ ---
if not os.path.exists(path_ritme) or not os.path.exists(path_acords):
    st.error("⚠️ No es troben els fitxers .musicxml al repositori.")
    st.info(f"Busco: {nom_ritme} i {nom_acords}")
else:
    if st.button("🔥 GENERAR NOU EXERCICI", use_container_width=True):
        with st.spinner("Dissenyant el groove..."):
            try:
                # 1. Carregar recursos
                pool_compassos = carregar_pool_per_compassos(path_acords)
                score_ritme = music21.converter.parse(path_ritme)
                
                # 2. Triar un compàs d'acords de referència per a tot l'exercici
                acords_referencia = random.choice(pool_compassos)
                
                # 3. Preparar el Score final
                new_score = music21.stream.Score()
                armadura_fa = music21.key.KeySignature(-1) # Fa Major (1 bemoll)
                
                # Memòria per fer que 1 = 3
                memoria_compassos = {} # {num_part: objecte_compas}

                # Trobem el punt d'inici (4 compassos seguits)
                num_m_originals = len(score_ritme.parts[0].getElementsByClass(music21.stream.Measure))
                start_m = random.randint(0, max(0, num_m_originals - 4))

                for idx_p, part_original in enumerate(score_ritme.parts):
                    nova_part = music21.stream.Part()
                    
                    # Clau i Armadura
                    if idx_p == 0:
                        nova_part.insert(0, music21.clef.TrebleClef())
                    else:
                        nova_part.insert(0, music21.clef.BassClef())
                    nova_part.insert(0, armadura_fa)

                    mesures_originals = list(part_original.getElementsByClass(music21.stream.Measure))
                    seleccio = mesures_originals[start_m : start_m + 4]
                    
                    for i, m in enumerate(seleccio):
                        # LÒGICA 1=3: Si és el tercer compàs, copiem el primer
                        if i == 2 and idx_p in memoria_compassos:
                            m_nova = copy.deepcopy(memoria_compassos[idx_p])
                            # Afegim el salt de línia al compàs 3
                            m_nova.insert(0, music21.layout.SystemLayout(isNew=True))
                        else:
                            m_nova = copy.deepcopy(m)
                            
                            # Si és mà dreta, apliquem els acords de referència
                            if idx_p == 0:
                                for n in m_nova.flatten().notes:
                                    nou_set = random.choice(acords_referencia)
                                    acord_nou = music21.chord.Chord(nou_set)
                                    acord_nou.duration = n.duration
                                    m_nova.replace(n, acord_nou)
                            
                            # Guardem el primer compàs per repetir-lo al tercer
                            if i == 0:
                                memoria_compassos[idx_p] = copy.deepcopy(m_nova)

                        # Configuració de la mesura
                        m_nova.number = i + 1
                        m_nova.makeBeams(inPlace=True)
                        nova_part.append(m_nova)
                    
                    # Neteja de la part
                    nova_part = nova_part.makeNotation()
                    new_score.insert(0, nova_part)

                # 4. Exportar a MusicXML
                with tempfile.NamedTemporaryFile(delete=False, suffix=".musicxml") as tmp:
                    new_score.write('musicxml', fp=tmp.name)
                    with open(tmp.name, 'rb') as f:
                        xml_data = f.read()

                # --- RESULTATS ---
                st.subheader("🎼 Previsualització")
                render_musicxml(xml_data)
                
                st.download_button(
                    label="📥 Descarregar Fitxer XML",
                    data=xml_data,
                    file_name="funk_pro_1-3.musicxml",
                    mime="application/vnd.recordare.musicxml+xml",
                    use_container_width=True
                )
                
            except Exception as e:
                st.error(f"S'ha produït un error: {e}")

st.divider()
st.caption("Estructura harmònica basada en compàs de referència. 2 compassos per sistema.")
