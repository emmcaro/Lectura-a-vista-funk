import streamlit as st
import music21
import os
import random
import copy
import tempfile
import streamlit.components.v1 as components

# --- CONFIGURACIÓ ---
st.set_page_config(page_title="Funk Generator", page_icon="🎸", layout="wide")
st.title("🎸 Funk Generator: Lògica C7 - Db7/F7")

# --- RUTES ---
base_path = os.path.dirname(__file__) if "__file__" in locals() else os.getcwd()
nom_ritme = "buidat_ritmic_funk.musicxml"
nom_acords = "font acords funk.musicxml"
path_ritme = os.path.join(base_path, nom_ritme)
path_acords = os.path.join(base_path, nom_acords)

# --- VISUALITZADOR JS ---
def render_musicxml(xml_data):
    xml_str = xml_data.decode('utf-8').replace('`', '\\`').replace('$', '\\$')
    html_code = f"""
    <div id="score-container" style="width: 100%;"></div>
    <script src="https://cdn.jsdelivr.net/npm/opensheetmusicdisplay@1.5.8/build/opensheetmusicdisplay.min.js"></script>
    <script>
        const osmd = new opensheetmusicdisplay.OpenSheetMusicDisplay("score-container", {{
            autoResize: true,
            drawPartNames: false,
            drawingParameters: "compacttight"
        }});
        osmd.setOptions({{
            zoom: 1.2,
            spacingFactor: 1.5,
            newSystemsFromMusicXml: true, // Respecta el SystemLayout de Music21
            pageFormat: "Endless"
        }});
        osmd.load(`{xml_str}`).then(() => {{
            // Forçat manual de 2 compassos: si l'amplada és limitada, saltarà.
            osmd.Sheet.Rules.MinMeasureWidth = 60; 
            osmd.render();
        }});
    </script>
    """
    components.html(html_code, height=700, width=1100)

# --- CARREGA DE RECURSOS ---
@st.cache_data
def carregar_recursos(p_ritme, p_acords):
    try:
        score_r = music21.converter.parse(p_ritme)
        score_a = music21.converter.parse(p_acords)
        # Agafem només els acords/notes de la font
        pool = [el for el in score_a.parts[0].flatten().notes if el.isChord or el.isNote]
        return score_r, pool
    except Exception as e:
        st.error(f"Error en carregar fitxers: {e}")
        return None, None

# --- LÒGICA ---
if not os.path.exists(path_ritme) or not os.path.exists(path_acords):
    st.error("⚠️ No es troben els fitxers XML al repositori GitHub.")
else:
    score_ritme_original, pool_acords = carregar_recursos(path_ritme, path_acords)

    if st.button("🔥 GENERAR EXERCICI", use_container_width=True):
        if score_ritme_original and pool_acords:
            try:
                # 1. Triar acord per als compassos 2 i 4
                acord_parell = random.choice(['Db', 'F'])
                toniques = ['C', acord_parell, 'C', acord_parell]
                
                new_score = music21.stream.Score()
                armadura_fa = music21.key.KeySignature(-1)
                
                # 2. Processar cada part (Mà Dreta, Mà Esquerra)
                for idx_p, part_original in enumerate(score_ritme_original.parts):
                    nova_part = music21.stream.Part()
                    nova_part.insert(0, music21.clef.TrebleClef() if idx_p == 0 else music21.clef.BassClef())
                    nova_part.insert(0, armadura_fa)

                    mesures = list(part_original.getElementsByClass(music21.stream.Measure))
                    # Punt d'inici aleatori per al ritme
                    start_idx = random.randint(0, max(0, len(mesures) - 4))
                    seleccio_ritme = mesures[start_idx : start_idx + 4]

                    for i in range(4):
                        m_original = seleccio_ritme[i]
                        m_nova = copy.deepcopy(m_original)
                        m_nova.number = i + 1
                        
                        # Transposició per a la mà dreta
                        if idx_p == 0:
                            tonica_actual = toniques[i]
                            # Triem una posició de la teva font
                            posicio_raw = random.choice(pool_acords)
                            posicio = music21.chord.Chord(posicio_raw.pitches) if posicio_raw.isNote else copy.deepcopy(posicio_raw)
                            
                            # Calculem interval des de C (suposant que la font està en C)
                            itvl = music21.interval.Interval(music21.pitch.Pitch('C'), music21.pitch.Pitch(tonica_actual))
                            acord_transp = posicio.transpose(itvl)
                            
                            # Substituir totes les notes del ritme per aquest acord transposat
                            for n in m_nova.flatten().notes:
                                n_nova = copy.deepcopy(acord_transp)
                                n_nova.duration = n.duration
                                m_nova.replace(n, n_nova)

                        # Forçar el salt de línia al compàs 3 (perquè surtin 2 i 2)
                        if i == 2:
                            m_nova.insert(0, music21.layout.SystemLayout(isNew=True))
                        
                        m_nova.makeBeams(inPlace=True)
                        nova_part.append(m_nova)
                    
                    nova_part = nova_part.makeNotation()
                    new_score.insert(0, nova_part)

                # 3. Exportar
                with tempfile.NamedTemporaryFile(delete=False, suffix=".musicxml") as tmp:
                    new_score.write('musicxml', fp=tmp.name)
                    with open(tmp.name, 'rb') as f:
                        xml_data = f.read()

                # 4. Mostrar
                st.success(f"Generat: C7 - {acord_parell}7 - C7 - {acord_parell}7")
                render_musicxml(xml_data)
                
                st.download_button("📥 Baixar MusicXML", data=xml_data, file_name="funk_pro.musicxml")

            except Exception as e:
                st.error(f"Error generant la partitura: {e}")
        else:
            st.error("No s'han pogut carregar els fitxers de GitHub.")
