import streamlit as st
import music21
import os
import random
import copy
import tempfile

# Configuració de la pàgina
st.set_page_config(page_title="Funk Generator", page_icon="🎸")
st.title("🎸 Generador de Funk Aleatori")
st.markdown("""
Aquesta app combina un **esquelet rítmic** amb una **font d'acords** per crear exercicis de lectura a vista.
""")

# --- CONFIGURACIÓ DE RUTES RELATIVES ---
# Això permet que l'app funcioni tant al teu ordinador com a GitHub/Streamlit Cloud
base_path = os.path.dirname(__file__) if "__file__" in locals() else os.getcwd()

# REVISA QUE AQUESTS NOMS COINCIDEIXIN EXACTAMENT AMB ELS DE GITHUB (Majúscules i minúscules!)
nom_ritme = "buidat_ritmic_funk.musicxml"
nom_acords = "font acords funk.musicxml"

path_ritme = os.path.join(base_path, nom_ritme)
path_acords = os.path.join(base_path, nom_acords)

# --- FUNCIONS ---

@st.cache_data
def carregar_pool_acords(ruta):
    """Llegeix el fitxer d'acords i en crea una llista per triar a l'atzar."""
    try:
        score = music21.converter.parse(ruta)
        pool = []
        # Agafem la primera part (mà dreta normalment)
        part = score.parts[0]
        for el in part.flatten().notes:
            if el.isChord:
                pool.append([p.nameWithOctave for p in el.pitches])
            elif el.isNote:
                pool.append([el.pitch.nameWithOctave])
        return pool
    except Exception as e:
        st.error(f"Error analitzant el pool d'acords: {e}")
        return None

# --- LÒGICA PRINCIPAL ---

# Comprovació de fitxers abans de començar
if not os.path.exists(path_ritme) or not os.path.exists(path_acords):
    st.error("⚠️ No s'han trobat els fitxers de música al repositori.")
    with st.expander("🔍 Detalls de depuració per a l'usuari"):
        st.write(f"Ruta base: `{base_path}`")
        st.write(f"Buscant fitxer ritme: `{nom_ritme}` -> {'✅ Trobat' if os.path.exists(path_ritme) else '❌ No trobat'}")
        st.write(f"Buscant fitxer acords: `{nom_acords}` -> {'✅ Trobat' if os.path.exists(path_acords) else '❌ No trobat'}")
        st.write("Fitxers detectats actualment:", os.listdir(base_path))
else:
    if st.button("🔥 Generar nou patró de Funk", use_container_width=True):
        with st.spinner("Cocinant el groove... 🕺"):
            try:
                # 1. Carregar dades
                pool_acords = carregar_pool_acords(path_acords)
                score_ritme = music21.converter.parse(path_ritme)
                
                if not pool_acords:
                    st.error("El pool d'acords està buit!")
                    st.stop()

                # 2. Seleccionar 4 compassos aleatoris
                part_original = score_ritme.parts[0]
                mesures_totals = list(part_original.getElementsByClass(music21.stream.Measure))
                num_mesures = len(mesures_totals)

                if num_mesures < 4:
                    start_m = 0
                    st.warning(f"El fitxer rítmic només té {num_mesures} compassos.")
                else:
                    start_m = random.randint(0, num_mesures - 4)

                # 3. Crear la nova partitura
                new_score = music21.stream.Score()
                nova_part = music21.stream.Part()
                
                # Copiar el tempo si existeix
                metronome = score_ritme.flatten().getElementsByClass(music21.tempo.MetronomeMark)
                if metronome:
                    nova_part.append(copy.deepcopy(metronome[0]))

                # Processar els 4 compassos seleccionats
                seleccio = mesures_totals[start_m : start_m + 4]
                
                for m in seleccio:
                    m_nova = copy.deepcopy(m)
                    # Substituir cada nota rítmica per un acord aleatori del pool
                    for n in m_nova.flatten().notes:
                        nou_set = random.choice(pool_acords)
                        new_chord = music21.chord.Chord(nou_set)
                        new_chord.duration = n.duration
                        m_nova.replace(n, new_chord)
                    nova_part.append(m_nova)
                
                new_score.insert(0, nova_part)

                # 4. Exportar a fitxer temporal
                with tempfile.NamedTemporaryFile(delete=False, suffix=".musicxml") as tmp:
                    new_score.write('musicxml', fp=tmp.name)
                    with open(tmp.name, 'rb') as f:
                        xml_data = f.read()

                # 5. Resultat
                st.success(f"✅ Patró generat amb èxit! (Compassos {start_m + 1} al {start_m + 4} del model)")
                
                st.download_button(
                    label="📥 Descarregar XML (MuseScore / Sibelius)",
                    data=xml_data,
                    file_name="exercici_funk.musicxml",
                    mime="application/vnd.recordare.musicxml+xml",
                    use_container_width=True
                )
                
            except Exception as e:
                st.error(f"S'ha produït un error durant la generació: {e}")

# Peu de pàgina
st.divider()
st.caption("Creat per a Lectura a Vista de Funk - Fes servir MuseScore per obrir el fitxer generat.")
