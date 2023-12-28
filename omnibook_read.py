import os

import music21 as m21
from m21_musescore import M21_and_show

CHORD_SPLIT = ":"
admitted_durations = [1/6, 0.25, 1/3, 0.5, 0.75, 2/3, 1, 1.5, 2, 3, 4]
non_admitted_durations = [1/5, 0.125, 4/5, 1/12]

chord_type_map_dict = {
    "min7b5": "ø7",
    "min9": "-7",
    "min7": "-7",
    "13": "7",
    "maj7": "M7",
    "7#9": "7(#9)",
    "dim": "o7",
    "": "M7",
    "m": "-7"
}


def chords_and_m21melody(omni_file):
    score = m21.converter.parse(omni_file)
    key = score.analyze("key")

    part = score.parts[0]
    m0 = part.getElementsByClass(m21.stream.Measure)[0] # measure 0

    tempo = None
    for element in m0:
        if isinstance(element, m21.tempo.MetronomeMark):
            tempo = element

    chord_dict = M21_and_show.chord_dict

    chords_omni = []
    melody = []

    elements = part.flatten().notesAndRests
    for element in elements:
        if 'Note' in element.classes or 'Rest' in element.classes:

            melody.append(element)
            # print(element.nameWithOctave, element.duration.quarterLength, element.offset, element.tie)

        elif 'Chord' in element.classes: # m21.harmony.ChordType
            # print("CHORD", element.figure, element.root(), element.offset)
            chord_type_omni = element.figure.strip(element.root().name)
            chord_name = element.root().name + CHORD_SPLIT + chord_type_omni
            chords_omni.append((chord_name, int(element.offset)))
            # print("CHORD", chord_name, element.offset)

    chord_types = []
    chord_progression = []
    for chord_pos, (chord_name_omni, chord_offset) in enumerate(chords_omni):
        # for last chord, no duration can be assumed
        if chord_pos == len(chords_omni) - 1:
            duration = 4
        else:
            _, next_chord_offset = chords_omni[chord_pos + 1]
            duration = next_chord_offset - chord_offset

        chord_type_omni = chord_name_omni.split(CHORD_SPLIT)[1]
        chord_type = chord_type_map_dict.get(chord_type_omni, chord_type_omni)
        # if chord_type == chord_type_omni:
            # chord not in mapping dictionary, but may be on base dicionary
            # chord_type = chord_dict.get(chord_type_omni, chord_type_omni)
            # if chord_type == chord_type_omni:
            # TODO SILENCIO
        chord_types.append(chord_type)

        c_chord_name = "C" + CHORD_SPLIT + chord_type
        if c_chord_name not in chord_dict.keys():
            print(f"Unknown chord {chord_name_omni}")
            chord_name = "C" + CHORD_SPLIT + "M7"
        else:
            chord_name = chord_name_omni.split(CHORD_SPLIT)[0] + CHORD_SPLIT + chord_type

        chord_progression.append((chord_name, duration))

    return chord_progression, melody, chord_types, key, tempo


def chords_and_melody_all(files_path):

    chord_types_all = set()
    chords_all = []
    melody_all = []
    omni_files = os.listdir(files_path)
    omni_files = [os.path.join(files_path, omni_file) for omni_file in omni_files if omni_file[-4:] == ".xml"]
    for omni_file in omni_files:
        chords, melody, chord_types, _, _ = chords_and_m21melody(omni_file)
        chords_all.append(chords)
        melody_all.append(melody)
        chord_types_all = chord_types_all.union(set(chord_types))

    print(chord_types_all)

    return chords_all, melody_all


if __name__ == "__main__":


    ONE_FILE = True

    if ONE_FILE:
        # original https://www.youtube.com/watch?v=02apSoxB7B4
        omni_file = "Omnibook/Donna_Lee.xml"

        _, melody, _, _, _ = chords_and_m21melody(omni_file)

        print(melody)

    else:
        files_path = "Omnibook"
        _, melody_all = chords_and_melody_all(files_path)

        print("len(melody_all)", len(melody_all))

        melody_set = set(melody_all)
        print("len(melody_set)", len(melody_set))
