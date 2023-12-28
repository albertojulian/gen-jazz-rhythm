import numpy as np
import music21 as m21

CHORD_JOIN = ":"

class M21_and_show:

    chord_dict = {
        "C:M7": [["C3", "B3", "D4", "E4", "G4"], ["C3", "E4", "G4", "B4", "D5"]],
        "C:6": [["C3", "A3", "D4", "E4", "G4"], ["C3", "E4", "G4", "A4", "D5"]],
        "C:7": [["C3", "Bb3", "D4", "E4", "A4"], ["C3", "E4", "A4", "Bb4", "D5"]],
        "C:11": [["C3", "Bb3", "D4", "F4", "A4"], ["C3", "F4", "A4", "Bb4", "D5"]],
        "C:7(b9)": [["C3", "Bb3", "Db4", "E4", "A4"], ["C3", "E4", "A4", "Bb4", "Db5"]],
        "C:7(#9)": [["C3", "Bb3", "D#4", "E4", "A4"], ["C3", "E4", "A4", "Bb4", "D#5"]],
        "C:o7": [["C3", "A3", "Eb4", "Gb4"], ["C3", "Eb4", "Gb4", "A4"], ["C3", "Gb4", "A4", "Eb5"]],  # diminished 7th
        "C:7#5": [["C3", "Bb3", "D#4", "E4", "Ab4"], ["C3", "E4", "Ab4", "Bb4", "D#5"]],
        "C:-7": [["C3", "Bb3", "D4", "Eb4", "G4"], ["C3", "Eb4", "G4", "Bb4", "D5"]],
        "C:-6": [["C3", "A3", "D4", "Eb4", "G4"], ["C3", "Eb4", "G4", "A4", "D5", ]],
        "C:ø7": [["C3", "Bb3", "Eb4", "Gb4"], ["C3", "Eb4", "Gb4", "Bb4"], ["C3", "Gb4", "Bb4", "Eb5"]],  # half diminished 7th
    }


    V7_SMOOTH_VOICE_LEAD_PROBABILITY = 0.9
    NON_V7_SMOOTH_VOICE_LEAD_PROBABILITY = 0.5

    def add_chord_version(self, m21_chord_version, trans_interv, chord_version_idx, mean_midis, m21_chord_versions):

        m21_chord_version.transpose(m21.interval.Interval(trans_interv), inPlace=True)
        m21_chord_version_midis = sum([pitch.midi for pitch in m21_chord_version.pitches[1:]]) \
                                                            / len(m21_chord_version.pitches[1:])
        mean_midis.append((m21_chord_version_midis, chord_version_idx))
        m21_chord_versions.append(m21_chord_version)

        return mean_midis, m21_chord_versions

    def chord_seq_to_m21_chords_and_bass(self, chord_progression):
        """
        Translate the MC generated chord sequence into a list of music21
        chords.

        Parameters:
        - chord_progression (list): The MC generated chord sequence: list of tuples (chord_name, chord_duration).

        Returns:
        - list of music21.chord.Chord: The corresponding chord progression in music21 format.
        - list of music21.note.Note: The bass line
        """

        print(chord_progression)
        # chord_progression = [('B_-7', 2), ('Bb_7', 2), ('Eb_-6', 2), ('G#_7(b9)', 2), ('C#_-7', 2), ('G#_-7', 2),
        #                     ('F#_-7', 2), ('B_-7', 2), ('A_-7', 2), ('E_-7', 2), ('B_-7', 2), ('E_-7', 2)]



        m21_bass_line = []
        m21_chord_progression = []
        for i, (chord_name, chord_duration) in enumerate(chord_progression):
            chord_bass, chord_type = chord_name.split(CHORD_JOIN)

            if chord_bass != "C":
                interv = m21.interval.Interval(m21.note.Note("C"), m21.note.Note(chord_bass))
                trans_interv = interv.semitones

                if trans_interv > 6:
                    trans_interv -= 12

                elif trans_interv < -6:
                    trans_interv += 12

            else:
                trans_interv = 0

            chord_versions = self.chord_dict["C" + CHORD_JOIN + chord_type]
            n_chord_versions = len(chord_versions)

            # music21 generates flat as "-", but we want to display flat as "b" (also admitted by music21)
            chord_bass = chord_bass.replace("-", "b")

            if i==0:
                # the chord is initially considered a C chord which is what the chord_dict contains
                chord_version_idx = np.random.randint(n_chord_versions)

                chord_notes_list = chord_versions[chord_version_idx]

                # Create a music21 chord
                m21_chord = m21.chord.Chord(chord_notes_list, quarterLength=chord_duration)
                if trans_interv != 0:
                    m21_chord.transpose(m21.interval.Interval(trans_interv), inPlace=True)

            else:
                prev_chord_name, _ = chord_progression[i-1]
                prev_chord_bass, prev_chord_type = chord_name.split(CHORD_JOIN)
                # TODO choose chord version with several criteria:

                prev_m21_chord = m21_chord_progression[i-1]
                # previous chord does not include root note, it was removed before adding the chord to the list
                prev_mean_midis = sum([pitch.midi for pitch in prev_m21_chord.pitches])/len(prev_m21_chord.pitches)
                # print(prev_m21_chord_midis)

                m21_chord_versions = []
                mean_midis = []
                for chord_version_idx in range(n_chord_versions):
                    chord_notes_list = chord_versions[chord_version_idx]

                    # Create a music21 chord
                    m21_chord_version = m21.chord.Chord(chord_notes_list, quarterLength=chord_duration)

                    if trans_interv > 0:
                        mean_midis, m21_chord_versions = self.add_chord_version(
                            m21_chord_version, trans_interv, chord_version_idx, mean_midis, m21_chord_versions)

                        if trans_interv > 3: # try descending octave
                            m21_chord_version = m21.chord.Chord(chord_notes_list, quarterLength=chord_duration)

                            mean_midis, m21_chord_versions = self.add_chord_version(
                                m21_chord_version, trans_interv - 12, chord_version_idx, mean_midis, m21_chord_versions)

                    else: # trans_interv < = 0
                        m21_chord_midis, m21_chord_versions = self.add_chord_version(
                            m21_chord_version, trans_interv, chord_version_idx, mean_midis, m21_chord_versions)

                        # try ascending octave
                        m21_chord_version = m21.chord.Chord(chord_notes_list, quarterLength=chord_duration)
                        # mean_midis, m21_chord_versions = self.add_chord_version(
                        #    m21_chord_version, trans_interv + 12, chord_version_idx, mean_midis, m21_chord_versions)

                midis_diff = [abs(prev_mean_midis - mean_midi) for (mean_midi, _) in mean_midis]

                # - if previous chord is 7th chord, choose minimum movement version with some probability
                if prev_chord_type in ["7", "7(b9)", "o7", "ø7"]:
                    if np.random.random() < self.V7_SMOOTH_VOICE_LEAD_PROBABILITY:
                        chord_version_idx = midis_diff.index(min(midis_diff))
                    else:
                        chord_version_idx = np.random.randint(len(midis_diff))
                else:
                    if np.random.random() < self.NON_V7_SMOOTH_VOICE_LEAD_PROBABILITY:
                        chord_version_idx = midis_diff.index(min(midis_diff))
                    else:
                        chord_version_idx = np.random.randint(len(midis_diff))

                # chord_version = mean_midis[chord_version_idx][1]
                # print(midis_diff, chord_version)
                m21_chord = m21_chord_versions[chord_version_idx]

            # TODO if previous chord is the same as current one (M7, -7), change version

            m21_chord.insertLyric("".join([chord_bass, chord_type]))

            # This ensures the bass note is in the right octave
            m21_bass_note = m21_chord.bass()
            m21_bass_line.append(m21.note.Note(m21_bass_note, duration=m21_chord.duration))

            # remove bass note from chord
            m21_chord.remove(m21_chord.pitches[0])
            m21_chord_progression.append(m21_chord)

        return m21_chord_progression, m21_bass_line

    def visualize_chords(self, chord_progression, bass_line):
        """
        Visualize a sequence of (pitch, duration) pairs using music21.

        Parameters:
            - melody (list): A list of (pitch, duration) pairs.
        """
        score = m21.stream.Score()
        score.metadata = m21.metadata.Metadata(title="Markov Chain Chord Progression")
        part1 = m21.stream.Part() # right hand part
        part2 = m21.stream.Part() # bass part
        f_clef = m21.clef.FClef()
        part2.append(f_clef)

        current_measure1 = m21.stream.Measure()

        for chord in chord_progression:
            if current_measure1.duration.quarterLength + chord.duration.quarterLength > 4.0:
                part1.append(current_measure1)
                current_measure1 = m21.stream.Measure()

            current_measure1.append(chord)

        part1.append(current_measure1)

        current_measure2 = m21.stream.Measure()
        for bass in bass_line:
            if current_measure2.duration.quarterLength + bass.duration.quarterLength > 4.0:
                part2.append(current_measure2)
                current_measure2 = m21.stream.Measure()

            current_measure2.append(bass)

        part2.append(current_measure2)

        score.append(part1)
        score.append(part2)

        score.show()


def mod_chord_duration(chord_sequence):

    mod_chord_sequence = []
    for chord_pos, chord_name in enumerate(chord_sequence):
        chord_bass, chord_type = chord_name.split(CHORD_JOIN)
        if chord_type == "M7":
            chord_duration = 4
        elif chord_type in ["-7", "-6", "ø7"]:
            next_chord_pos = chord_pos + 1
            if next_chord_pos < len(chord_sequence):
                next_chord_name = chord_sequence[next_chord_pos]
                next_chord_type = next_chord_name.split(CHORD_JOIN)[1]
                # minor 7th and similar (half dim 7) can be shorter
                # if they are followed by 7th chords and similar (dim 7)
                if next_chord_type in ["7", "7(b9)", "o7"]:
                    chord_duration = 2
                else:
                    chord_duration = 4
            else:
                chord_duration = 4
        else:
            chord_duration = 2

        mod_chord_sequence.append((chord_name, chord_duration))

    return mod_chord_sequence
