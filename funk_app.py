import streamlit as st
import music21
import random
import copy
import os

# CONFIGURACIÓ PER A SERVIDOR (Github/Streamlit)
# Això evita que music21 busqui el MuseScore al servidor
music21.environment.set('musicxmlDirectives', 'nopreview')

st.title("🎸 Funk Generator Cloud")

# Rutes relatives (busquen al repositori de GitHub)
path_ritme = "buidat_ritmic_funk.xml"
path_acords = "font_acords_funk.xml"

def carregar_pool_acords(ruta):
    # Verifiquem que el fitxer existeix al repo
    if not os.path.exists(ruta):
        st.error(f"Falta el fitxer {ruta} al repositori!")
        return []
    
    score = music21.converter.parse(ruta)
    pool = []
    # Suposem que la font d'acords és la Part 0
    for el in score.parts[0].flatten().notes:
        if el.isChord:
            pool.append([p.nameWithOctave for p in el.pitches])
        elif el.isNote:
            pool.append([el.pitch.nameWithOctave])
    return pool

# --- INTERFÍCIE STREAMLIT ---

if st.button("Generar Groove de 4 compassos"):
    with st.spinner("Cocinant el ritme..."):
        pool = carregar_pool_acords(path_acords)
        
        if pool:
            score_ritme = music21.converter.parse(path_ritme)
            parts_originals = score_ritme.parts
            
            # Triem 4 compassos aleatoris
            total_m = len(parts_originals[0].getElementsByClass(music21.stream.Measure))
            start_m = random.randint(0, max(0, total_m - 4))
            
            new_score = music21.stream.Score()
            
            for idx_p, part_vella in enumerate(parts_originals):
                nova_part = music21.stream.Part()
                mesures = list(part_vella.getElementsByClass(music21.stream.Measure))[start_m : start_m + 4]
                
                for m in mesures:
                    m_nova = copy.deepcopy(m)
                    # Mà Dreta (Part 0): Canviem notes per acords aleatoris
                    if idx_p == 0:
                        for n in m_nova.flatten().notes:
                            nou_set = random.choice(pool)
                            acord_nou = music21.chord.Chord(nou_set)
                            acord_nou.duration = n.duration
                            m_nova.replace(n, acord_nou)
                    nova_part.append(m_nova)
                new_score.insert(0, nova_part)
            
            # Generem el fitxer XML en memòria
            fp = new_score.write('musicxml')
            
            with open(fp, 'rb') as f:
                st.download_button(
                    label="⬇️ Descarregar XML generat",
                    data=f,
                    file_name="funk_generat.musicxml",
                    mime="application/vnd.recordare.musicxml+xml"
                )
            st.success(f"Fet! He fet servir els compassos {start_m+1} al {start_m+4} del teu buidat.")
