import streamlit as st
import music21
import os
import random
import copy
import tempfile
import streamlit.components.v1 as components

# --- CONFIGURACIÓ DE PÀGINA ---
st.set_page_config(page_title="Funk Generator Pro", page_icon="🎸", layout="wide")

st.title("🎸 Funk Generator: C7 Mixolydian Mode")
st.markdown("Estructura: **1=C7**, **2=Vincle (Db7/F7)**, **3=C7**, **4=Vincle**.")

# --- RUTES ---
base_path = os.path.dirname(__file__) if "__file__" in locals() else os.getcwd()
nom_ritme = "buidat_ritmic_funk.musicxml"
nom_acords = "font acords funk.musicxml"
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
            spacingFactor: 1.6,
            newSystemsFromMusicXml: true,
            pageFormat: "Endless"
        }});

        osmd.load(`{xml_str}`).then(() => {{
            // Forcem que cada compàs sigui molt ample per obligar el salt cada 2
            osmd.Sheet.Rules.MinMeasureWidth = 55; 
            osmd.render();
        }});
    </script>
    """
    components.html(html_code, height=700, width=1100)

# --- FUNCIÓ DE TRANSPOSICIÓ ---
def transposar_posicio(acord_font, nota_desti):
    # Calculem l'interval des de C (assumim que la teva font està en C)
    itvl = music21.interval.Interval(music21.pitch.Pitch('C'), music21.pitch.Pitch(nota_desti))
    # Transposem l'objecte sencer (manté l'estructura de veus exacta)
    return acord_font.transpose(itvl)

@st.cache_data
def carregar_pool_acords(ruta):
    try:
        score = music21.converter.parse(ruta)
        # Agafem només acords o notes soles de la part superior
        pool = [el for el in score.parts[0].flatten().notes if el.isChord or el.isNote]
        return pool
    except: return None

# --- LÒGICA DE GENERACIÓ ---
if not os.path.exists(path_ritme) or not os.path.exists(path_acords):
    st.error("⚠️ No es troben els fitxers .musicxml.")
else:
    if st.button("🔥 GENERAR EXERCICI HARMONITZAT", use_container_width=True):
        with st.spinner("Transposant posicions..."):
            try:
                pool_posicions = carregar_pool_acords(path_acords)
                score_ritme = music21.converter.parse(path_ritme)
                
                # Triem quin acord "vincle" usarem als compassos 2 i 4
                acord_vincle = random.choice(['Db', 'F']) # bII7 o IV
                toniques = ['C', acord_vincle, 'C', acord_vincle]
                
                new_score = music21.stream.Score()
                armadura_fa = music21.key.KeySignature(-1) # Fa Major
                
                # Memòria per a la coherència rítmica (1=3 i 2=4 si vols, o lliure)
                # Aquí ho farem amb el ritme original del fitxer, però transposat
                
                for idx_p, part_original in enumerate(score_ritme.parts):
                    nova_part = music21.stream.Part()
                    nova_part.insert(0, music21.clef.TrebleClef() if idx_p == 0 else music21.clef.BassClef())
                    nova_part.insert(0, armadura_fa)

                    mesures_originals = list(part_original.getElementsByClass(music21.stream.Measure))
                    start_m = random.randint(0, max(0, len(mesures_originals) - 4))
                    seleccio = mesures_originals[start_m : start_m + 4]
                    
                    for i in range(4):
                        m_nova = copy.deepcopy(seleccio[i])
                        m_nova.number = i + 1
                        
                        if idx_p == 0: # Mà dreta: Transposició de la teva font
                            # Triem una posició aleatòria de la teva font
                            posicio_original = random.choice(pool_posicions)
                            # Si és nota sola, la convertim a acord per seguretat
                            if posicio_original.isNote:
                                posicio_original = music21.chord.Chord([posicio_original.pitch])
                            
                            acord_final = transposar_posicio(posicio_original, toniques[i])
                            
                            # Apliquem aquesta posició a tot el ritme del compàs
                            for n in m_nova.flatten().notes:
                                n_nova = copy.deepcopy(acord_final)
                                n_nova.duration = n.duration
                                m_nova.replace(n, n_nova)
                        
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

                st.subheader(f"🎼 Estructura: C7 i {acord_vincle}7")
                render_musicxml(xml_data)
                
                st.download_button(label="📥 Descarregar XML", data=xml_data, 
                                 file_name="funk_mixolidi_pro.musicxml", 
                                 mime="application/vnd.recordare.musicxml+xml",
                                 use_container_width=True)
                
            except Exception as e:
                st.error(f"Error: {e}")
