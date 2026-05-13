import streamlit as st
import music21
import os
import random
import copy
from io import BytesIO

st.set_page_config(page_title="Funk Generator", page_icon="🎸")
st.title("🎸 Generador de Funk Aleatori")

# Rutes dels fitxers
folder = "/Users/caro/Desktop/app lectura semis"
path_ritme = os.path.join(folder, "buidat_ritmic_funk.musicxml")
path_acords = os.path.join(folder, "font acords funk.musicxml")

def carregar_pool_acords(ruta):
    score = music21.converter.parse(ruta)
    pool = []
    part_dreta = score.parts[0]
    for el in part_dreta.flatten().notes:
        if el.isChord:
            pool.append([p.nameWithOctave for p in el.pitches])
        elif el.isNote:
            pool.append([el.pitch.nameWithOctave])
    return pool

if st.button("Generar nou patró de 4 compassos"):
    if not os.path.exists(path_ritme) or not os.path.exists(path_acords):
        st.error("No trobo els fitxers XML a la carpeta de l'escriptori.")
    else:
        with st.spinner("Cocinant el groove..."):
            pool_acords = carregar_pool_acords(path_acords)
            score_ritme = music21.converter.parse(path_ritme)
            
            total_m = len(score_ritme.parts[0].getElementsByClass(music21.stream.Measure))
            start_m = random.randint(0, max(0, total_m - 4))

            new_score = music21.stream.Score()
            
            for idx_p, part_original in enumerate(score_ritme.parts):
                nova_part = music21.stream.Part()
                mesures = list(part_original.getElementsByClass(music21.stream.Measure))[start_m : start_m + 4]
                
                for m in mesures:
                    m_nova = copy.deepcopy(m)
                    if idx_p == 0: # Mà dreta
                        for n in m_nova.flatten().notes:
                            nou_set = random.choice(pool_acords)
                            new_chord = music21.chord.Chord(nou_set)
                            new_chord.duration = n.duration
                            m_nova.replace(n, new_chord)
                    nova_part.append(m_nova)
                new_score.insert(0, nova_part)

            # En lloc de guardar a disc, ho preparem per descarregar
            out_xml = new_score.write('musicxml')
            with open(out_xml, 'rb') as f:
                xml_data = f.read()
            
            st.success(f"Patró generat correctament (compassos {start_m + 1} al {start_m + 4})!")
            
            st.download_button(
                label="Descarregar fitxer XML",
                data=xml_data,
                file_name="generacio_funk.musicxml",
                mime="application/vnd.recordare.musicxml+xml"
            )
