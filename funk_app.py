import streamlit as st
import music21
import random
import copy
import os

# --- CONFIGURACIÓ INICIAL PER A SERVIDOR ---
try:
    us = music21.environment.UserSettings()
    us.create()
except:
    pass

st.set_page_config(page_title="Funk Generator", page_icon="🎸")

st.title("🎸 Funk Generator Cloud")
st.write("Generador de seqüències de 4 compassos combinant ritmes i acords.")

# --- RUTES ACTUALITZADES A .MUSICXML ---
path_ritme = "buidat_ritmic_funk.musicxml"
path_acords = "font acords funk.musicxml"

def carregar_pool_acords(ruta):
    """Llegeix el fitxer d'acords (.musicxml) i crea un pool de notes."""
    if not os.path.exists(ruta):
        st.error(f"⚠️ No s'ha trobat el fitxer: {ruta}")
        return []
    
    try:
        # Forcem el format musicxml explicitament
        score = music21.converter.parse(ruta, format='musicxml')
        pool = []
        # Agafem les notes de la primera part
        for el in score.parts[0].flatten().notes:
            if el.isChord:
                pool.append([p.nameWithOctave for p in el.pitches])
            elif el.isNote:
                pool.append([el.pitch.nameWithOctave])
        return pool
    except Exception as e:
        st.error(f"Error al carregar acords: {e}")
        return []

# --- INTERFÍCIE ---

if st.button("🚀 Generar nou patró (4 compassos)"):
    if not os.path.exists(path_ritme):
        st.error(f"⚠️ No s'ha trobat el fitxer de ritmes: {path_ritme}")
    else:
        with st.spinner("Sincopant els ritmes..."):
            pool = carregar_pool_acords(path_acords)
            
            if pool:
                try:
                    # Carreguem el document de ritmes forçant format musicxml
                    score_ritme = music21.converter.parse(path_ritme, format='musicxml')
                    parts_originals = score_ritme.parts
                    
                    total_m = len(parts_originals[0].getElementsByClass(music21.stream.Measure))
                    
                    if total_m < 4:
                        start_m = 0
                    else:
                        start_m = random.randint(0, total_m - 4)
                    
                    new_score = music21.stream.Score()
                    
                    for idx_p, part_vella in enumerate(parts_originals):
                        nova_part = music21.stream.Part()
                        nova_part.partName = part_vella.partName
                        
                        mesures = list(part_vella.getElementsByClass(music21.stream.Measure))[start_m : start_m + 4]
                        
                        for i, m in enumerate(mesures):
                            m_nova = copy.deepcopy(m)
                            m_nova.number = i + 1 
                            
                            if idx_p == 0: # Mà Dreta
                                for n in m_nova.flatten().notes:
                                    nou_set = random.choice(pool)
                                    acord_nou = music21.chord.Chord(nou_set)
                                    acord_nou.duration = n.duration
                                    acord_nou.articulations = n.articulations
                                    m_nova.replace(n, acord_nou)
                            
                            nova_part.append(m_nova)
                        
                        new_score.insert(0, nova_part)
                    
                    # Generació del fitxer de sortida
                    tmp_fp = new_score.write('musicxml')
                    
                    with open(tmp_fp, 'rb') as f:
                        xml_data = f.read()
                        
                    st.success(f"Generat correctament a partir dels compassos {start_m + 1} a {start_m + 4}.")
                    
                    st.download_button(
                        label="⬇️ Descarregar MusicXML",
                        data=xml_data,
                        file_name="funk_generat.musicxml",
                        mime="application/vnd.recordare.musicxml+xml"
                    )
                    
                    if os.path.exists(tmp_fp):
                        os.remove(tmp_fp)
                        
                except Exception as e:
                    st.error(f"Error durant la generació: {e}")

st.divider()
st.caption("Recorda pujar els fitxers .musicxml amb el mateix nom al teu repositori de GitHub.")
