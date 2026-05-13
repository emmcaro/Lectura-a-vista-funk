import streamlit as st
import music21
import os
import random
import copy
import tempfile
import streamlit.components.v1 as components

# --- CONFIGURACIÓ ---
st.set_page_config(page_title="Funk Transposer", page_icon="🎸", layout="wide")
st.title("🎸 Funk Generator: Transposició de Posicions")

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
            autoResize: true, drawPartNames: false, drawingParameters: "compacttight"
        }});
        osmd.setOptions({{
            zoom: 1.3, spacingFactor: 1.4, newSystemsFromMusicXml: true
        }});
        osmd.load(`{xml_str}`).then(() => {{
            osmd.Sheet.Rules.MinMeasureWidth = 55; 
            osmd.render();
        }});
    </script>
    """
    components.html(html_code, height=750, width=1100)

# --- FUNCIÓ PER TRANSPOSAR ---
def transposar_acord(acord_original, nota_desti_nom):
    """Transposa un objecte acord a la nova fonamental mantenint l'estructura exacta."""
    # Suposem que la "referència" de la teva font és Do (C)
    # Si la teva font d'acords està en una altra tonalitat, canvia 'C' per la tònica d'aquella font.
    interval = music21.interval.Interval(music21.pitch.Pitch('C'), music21.pitch.Pitch(nota_desti_nom))
    nou_acord = acord_original.transpose(interval)
    return nou_acord

@st.cache_data
def carregar_pool_acords_originals(ruta):
    try:
        score = music21.converter.parse(ruta)
        pool = [el for el in score.parts[0].flatten().notes if el.isChord or el.isNote]
        return pool
    except: return None

# --- LÒGICA ---
if not os.path.exists(path_ritme) or not os.path.exists(path_acords):
    st.error("⚠️ Falten fitxers XML al repositori.")
else:
    if st.button("🔥 GENERAR AMB POSICIONS REALS", use_container_width=True):
        with st.spinner("Transposant les teves posicions... 🎹"):
            try:
                pool_originals = carregar_pool_acords_originals(path_acords)
                score_ritme = music21.converter.parse(path_ritme)
                
                # Triem l'acord per als compassos 2 i 4
                desti_parell = random.choice(['Db', 'F'])
                
                new_score = music21.stream.Score()
                armadura_fa = music21.key.KeySignature(-1)

                for idx_p, part_original in enumerate(score_ritme.parts):
                    nova_part = music21.stream.Part()
                    nova_part.insert(0, music21.clef.TrebleClef() if idx_p == 0 else music21.clef.BassClef())
                    nova_part.insert(0, armadura_fa)

                    mesures_originals = list(part_original.getElementsByClass(music21.stream.Measure))
                    seleccio = mesures_originals[random.randint(0, max(0, len(mesures_originals)-4)) : ]
                    
                    for i in range(4):
                        m = mesures_originals[i] # Agafem els 4 primers del ritme o aleatoris
                        m_nova = copy.deepcopy(m)
                        m_nova.number = i + 1
                        
                        # Definir tònica segons el compàs
                        tonica = 'C' if (i == 0 or i == 2) else desti_parell

                        if idx_p == 0: # Mà Dreta: Transposició
                            for n in m_nova.flatten().notes:
                                # Triem una posició a l'atzar de la teva font
                                posicio_font = random.choice(pool_originals)
                                
                                # Si a la font hi ha una nota sola, la convertim en acord per seguretat
                                if posicio_font.isNote:
                                    posicio_font = music21.chord.Chord([posicio_font.pitch])
                                
                                # Transposem la teva posició a la tònica del compàs (C, Db o F)
                                acord_transposat = transposar_acord(posicio_font, tonica)
                                acord_transposat.duration = n.duration
                                m_nova.replace(n, acord_transposat)

                        if i == 2: m_nova.insert(0, music21.layout.SystemLayout(isNew=True))
                        m_nova.makeBeams(inPlace=True)
                        nova_part.append(m_nova)
                    
                    nova_part = nova_part.makeNotation()
                    new_score.insert(0, nova_part)

                with tempfile.NamedTemporaryFile(delete=False, suffix=".musicxml") as tmp:
                    new_score.write('musicxml', fp=tmp.name)
                    with open(tmp.name, 'rb') as f:
                        xml_data = f.read()

                st.subheader(f"🎼 Estructura: C (1,3) i {desti_parell} (2,4)")
                render_musicxml(xml_data)
                
                st.download_button(label="📥 Descarregar XML", data=xml_data, 
                                 file_name="funk_posicions.musicxml", 
                                 mime="application/vnd.recordare.musicxml+xml",
                                 use_container_width=True)
                
            except Exception as e:
                st.error(f"Error: {e}")
