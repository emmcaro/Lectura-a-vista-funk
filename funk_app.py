import music21
import os
import random
import copy

# RUTES
folder = "/Users/caro/Desktop/app lectura semis"
path_ritme = os.path.join(folder, "buidat_ritmic_funk.musicxml")
path_acords = os.path.join(folder, "font acords funk.musicxml")
path_sortida = os.path.join(folder, "generacio_funk_4_compassos.xml")

def carregar_pool_acords(ruta):
    """Llegeix el Doc 2 i guarda tots els acords/notes en una llista."""
    score = music21.converter.parse(ruta)
    pool = []
    # Agafem només la mà dreta (Part 0)
    part_dreta = score.parts[0]
    for el in part_dreta.flatten().notes:
        if el.isChord:
            # Guardem només les altures (pitches) de l'acord
            pool.append([p.nameWithOctave for p in el.pitches])
        elif el.isNote:
            pool.append([el.pitch.nameWithOctave])
    return pool

def generar_funk():
    if not os.path.exists(path_ritme) or not os.path.exists(path_acords):
        print("Error: Revisa que els dos fitxers XML estiguin a la carpeta.")
        return

    print("Preparant generació...")
    pool_acords = carregar_pool_acords(path_acords)
    score_ritme = music21.converter.parse(path_ritme)
    
    # Triem un punt d'inici aleatori per agafar 4 compassos seguits del Doc 1
    total_compassos = len(score_ritme.parts[0].getElementsByClass(music21.stream.Measure))
    if total_compassos < 4:
        start_m = 0
    else:
        start_m = random.randint(0, total_compassos - 4)

    # Creem la nova partitura
    new_score = music21.stream.Score()
    
    for idx_p, part_original in enumerate(score_ritme.parts):
        nova_part = music21.stream.Part()
        nova_part.partName = part_original.partName
        
        # Agafem els 4 compassos triats
        mesures = list(part_original.getElementsByClass(music21.stream.Measure))[start_m : start_m + 4]
        
        for m in mesures:
            m_nova = copy.deepcopy(m)
            
            # SI ÉS LA MÀ DRETA (Part 0), apliquem l'aleatorietat d'acords
            if idx_p == 0:
                for n in m_nova.flatten().notes:
                    # Triem un acord aleatori de la bossa
                    nou_set_notes = random.choice(pool_acords)
                    
                    if n.isChord:
                        # Si era un acord, el substituïm conservant la durada
                        n.pitches = [music21.pitch.Pitch(p) for p in nou_set_notes]
                    elif n.isNote:
                        # Si era una nota sola, la convertim en acord o nota segons el pool
                        new_chord = music21.chord.Chord(nou_set_notes)
                        new_chord.duration = n.duration
                        m_nova.replace(n, new_chord)
            
            # SI ÉS LA MÀ ESQUERRA (Part 1), no fem res, ja hem fet el deepcopy
            nova_part.append(m_nova)
            
        new_score.insert(0, nova_part)

    # Guardar resultat
    new_score.write('musicxml', fp=path_sortida)
    print(f"Fet! S'han generat 4 compassos a: {path_sortida}")

if __name__ == "__main__":
    generar_funk()
