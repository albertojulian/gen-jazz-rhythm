from enum import Enum

import numpy as np
import music21 as m21  # instrument, metadata, note, stream, clef, tie

CHORD_SPLIT = ":"
MEASURE_DURATION = 4

melody_m21instruments = [
    m21.instrument.AltoSaxophone,
    m21.instrument.TenorSaxophone,
    m21.instrument.SopranoSaxophone,
    m21.instrument.Flute,
]

melody_instruments_d = {instr().instrumentName: instr for instr in melody_m21instruments}


class PitchedInstruments(Enum):
    # MELODY = 0
    CHORD = 0
    BASS = 1


class DrumInstruments(Enum):
    RIDE = 2  # Cymbal
    FOOT_HIHAT = 3
    HIHAT = 4
    SNARE = 5
    KICK = 6  # bass drum
    CRASH = 7  # Cymbal


class States(Enum):
    OFF = 0
    FILL_1 = 1  # fill whole beat
    FILL_2_1 = 2  # swing
    FILL_0_1 = 3  # swing syncopation
    FILL_1_T = 4  # fill whole beat and tie with next


class PatternMusic21Converter:
    """
    Converts background patterns into music21 scores.

    This class takes a background pattern state array and converts it into a score
    using the music21 library.
    """

    # Mapping of drum instrument indices to music21 classes and MIDI pitches
    drumInstruments = {
        DrumInstruments.RIDE: (m21.instrument.HiHatCymbal, 51, "Ride Cymbal"),
        DrumInstruments.FOOT_HIHAT: (m21.instrument.HiHatCymbal, 44, "Foot HiHat"),
        DrumInstruments.CRASH: (m21.instrument.HiHatCymbal, 49, "Crash Cymbal"),
        DrumInstruments.HIHAT: (m21.instrument.HiHatCymbal, 42),
        DrumInstruments.SNARE: (m21.instrument.SnareDrum, 38),
        DrumInstruments.KICK: (m21.instrument.BassDrum, 36),
    }

    BEAT_DURATION = 1.0
    VOLUME_INCREASE = 1.5

    def __init__(self, is_m21melody=False, key=None, tempo=None):
        self.is_m21melody = is_m21melody
        self.key = key
        self.tempo = tempo

    def to_music21_score(self, state, melody, m21_chord_progression, m21_bass_line,
                         score_title="Jazz Music generated by Bill Aivans",
                         melody_instrument=melody_m21instruments[0](),
                         octave_up_down=0,
                         ):
        """
        TODO: update
        Converts a drum pattern state to a music21 stream for musical
        representation.

        Parameters:
            state (np.ndarray): The state array of the drum pattern.

            melody

            m21_chord_progression

            m21_bass_line

            score_title

            melody_instrument

        Returns:
            music21.stream.Score: The music21 score representation of the drum
                pattern.
        """
        score = m21.stream.Score()
        score.metadata = m21.metadata.Metadata(
            title=score_title
        )

        pattern_length = len(state[0])

        if not self.is_m21melody:
            melody_part = self._melody_instrument_to_music21_part(
                melody, state, melody_instrument, octave_up_down,
            )
        else:
            melody_part = self._m21melody_instrument_to_music21_part(
                melody, melody_instrument, octave_up_down,
            )
        score.append(melody_part)

        chord_part = self._chord_instrument_to_music21_part(
                m21_chord_progression, state
        )
        score.append(chord_part)

        bass_part = self._bass_instrument_to_music21_part(
                m21_bass_line, state
        )
        score.append(bass_part)

        for drum_instrument in DrumInstruments:
            part = self._drum_instrument_to_music21_part(
                drum_instrument, state, pattern_length
            )
            score.append(part)

        max_measures = max([len(part.getElementsByClass(m21.stream.Measure)) for part in score.parts])
        for part in score.parts:
            # all parts should have the same number of measures; otherwise, add an empty one
            if len(part.getElementsByClass(m21.stream.Measure)) == max_measures - 1:
                last_measure = m21.stream.Measure()
                part.append(last_measure)

        return score

    def _melody_instrument_to_music21_part(
            self, melody, state, melody_instrument, octave_up_down,
    ):
        # Create the melody part and add notes to it
        melody_part = m21.stream.Part()

        transp_interv = melody_instrument.transposition
        if transp_interv != None:
            print(f"Instrument transposed {transp_interv.semitones} semitones")

        melody_part.append(melody_instrument)

        current_measure = m21.stream.Measure() # measure 0

        for (fig_name, fig_duration) in melody:

            if fig_name == "R":
                melody_fig = m21.note.Rest(fig_duration)
            else:
                melody_fig = m21.note.Note(fig_name, quarterLength=fig_duration)
                melody_fig.volume.velocityScalar = self.VOLUME_INCREASE

                if transp_interv != None:
                    # melody_fig.transpose(m21.interval.Interval(-transp_interv.semitones - 12), inPlace=True)
                    melody_fig.transpose(m21.interval.Interval(-transp_interv.semitones), inPlace=True)

                # due to change of random melodies initialization replaced
                if octave_up_down != 0:
                    melody_fig.transpose(m21.interval.Interval(12 * octave_up_down), inPlace=True)

            if current_measure.duration.quarterLength + melody_fig.duration.quarterLength > MEASURE_DURATION:
                # Verificar si parte de la figura cabe en el compás actual
                if current_measure.duration.quarterLength < MEASURE_DURATION:
                    remaining_bar_duration = MEASURE_DURATION - current_measure.duration.quarterLength
                    print("remaining_bar_duration", remaining_bar_duration)
                    split_note, remaining_note = melody_fig.splitAtQuarterLength(remaining_bar_duration)
                    current_measure.append(split_note)
                    melody_part.append(current_measure)
                    current_measure = m21.stream.Measure()
                    melody_fig = remaining_note

                elif current_measure.duration.quarterLength == MEASURE_DURATION:
                    # current_measure.append(melody_fig)
                    melody_part.append(current_measure)
                    current_measure = m21.stream.Measure()

            current_measure.append(melody_fig)

        melody_part.append(current_measure)

        if current_measure.duration.quarterLength < MEASURE_DURATION:
            print("last_measure.duration.quarterLength", current_measure.duration.quarterLength)
            end_rest = m21.note.Rest(MEASURE_DURATION - current_measure.duration.quarterLength)
            print("Adding ending rest of duration ", end_rest.quarterLength)
            current_measure.append(end_rest)

        return melody_part

    def _m21melody_instrument_to_music21_part(
            self, melody, melody_instrument, octave_up_down,
    ):

        # Create the melody part and add notes to it
        melody_part = m21.stream.Part()

        melody_key_sign = None
        transp_interv = melody_instrument.transposition
        if transp_interv != None:
            print(f"Instrument transposed {transp_interv.semitones} semitones")

            # transpose melody key
            if self.key is not None:
                melody_key_sign = m21.key.KeySignature(self.key.sharps).transpose(-transp_interv.semitones)
        else:
            if self.key is not None:
                melody_key_sign = m21.key.KeySignature(self.key.sharps)

        melody_part.append(melody_instrument)

        current_measure = m21.stream.Measure()

        if melody_key_sign is not None:
            current_measure.append(melody_key_sign)

        if self.tempo is not None:
            current_measure.append(self.tempo)

        for melody_fig in melody:

            if isinstance(melody_fig, m21.note.Note):
                melody_fig.volume.velocityScalar = self.VOLUME_INCREASE

                if transp_interv != None:
                    # melody_fig.transpose(m21.interval.Interval(-transp_interv.semitones - 12), inPlace=True)
                    melody_fig.transpose(m21.interval.Interval(-transp_interv.semitones), inPlace=True)

                # due to change of random melodies initialization replaced
                if octave_up_down != 0:
                    melody_fig.transpose(m21.interval.Interval(12 * octave_up_down), inPlace=True)

            if current_measure.duration.quarterLength + melody_fig.duration.quarterLength > MEASURE_DURATION:
                # Verificar si parte de la figura cabe en el compás actual
                if current_measure.duration.quarterLength < MEASURE_DURATION:
                    remaining_bar_duration = MEASURE_DURATION - current_measure.duration.quarterLength
                    print("remaining_bar_duration", remaining_bar_duration)
                    split_note, remaining_note = melody_fig.splitAtQuarterLength(remaining_bar_duration)
                    current_measure.append(split_note)
                    melody_part.append(current_measure)
                    current_measure = m21.stream.Measure()
                    melody_fig = remaining_note

                elif current_measure.duration.quarterLength == MEASURE_DURATION:
                    # current_measure.append(melody_fig)
                    melody_part.append(current_measure)
                    current_measure = m21.stream.Measure()

            current_measure.append(melody_fig)

        melody_part.append(current_measure)

        if current_measure.duration.quarterLength < MEASURE_DURATION:
            print("last_measure.duration.quarterLength", current_measure.duration.quarterLength)
            end_rest = m21.note.Rest(MEASURE_DURATION - current_measure.duration.quarterLength)
            print("Adding ending rest of duration ", end_rest.quarterLength)
            current_measure.append(end_rest)

        return melody_part


    def _chord_instrument_to_music21_part(
            self, chord_progression, state
    ):
        chord_part = m21.stream.Part()
        chord_instrument = m21.instrument.Piano()
        chord_part.insert(0, chord_instrument)

        current_measure = m21.stream.Measure()

        if self.key is not None:
            current_measure.append(m21.key.KeySignature(self.key.sharps))

        for chord_pos, chord in enumerate(chord_progression):

            new_chord = m21.chord.Chord(chord.pitches, quarterlength=chord.quarterLength)
            new_chord.insertLyric(chord.lyric)

            if current_measure.quarterLength + new_chord.quarterLength > 4.0:
                chord_part.append(current_measure)
                current_measure = m21.stream.Measure()

            if (
                    state[PitchedInstruments.CHORD.value][chord_pos] == States.FILL_0_1.value
            ):
                rest = m21.note.Rest(self.BEAT_DURATION * 1/2)
                current_measure.append(rest)

                new_chord.quarterLength = self.BEAT_DURATION * 1 / 2
                # new_chord.volume.velocityScalar = self.VOLUME_INCREASE

                next_chord_pos = chord_pos + 1
                if next_chord_pos < len(chord_progression):
                    #    next_bass_note = bass_line[next_bass_pos]
                    new_chord.tie = m21.tie.Tie('start')
            elif (
                    state[PitchedInstruments.CHORD.value][chord_pos] == States.FILL_1_T.value
            ):
                # sometimes chords other than 7ths are tied
                next_chord_pos = chord_pos + 1
                if next_chord_pos < len(chord_progression):
                    #    next_bass_note = bass_line[next_bass_pos]
                    new_chord.tie = m21.tie.Tie('start')

            current_measure.append(new_chord)

        chord_part.append(current_measure)

        return chord_part

    def _bass_instrument_to_music21_part(
            self, bass_line, state
    ):
        bass_part = m21.stream.Part()
        bass_part.insert(m21.clef.FClef())

        bass = m21.instrument.Contrabass()
        bass_part.insert(0, bass)

        current_measure = m21.stream.Measure()

        if self.key is not None:
            current_measure.append(m21.key.KeySignature(self.key.sharps))

        for bass_pos, bass_note in enumerate(bass_line):

            new_bass_note = m21.note.Note(bass_note.pitch)
            if current_measure.quarterLength + bass_note.quarterLength > 4.0:
                bass_part.append(current_measure)
                current_measure = m21.stream.Measure()

            new_bass_note.volume.velocityScalar = self.VOLUME_INCREASE

            if (
                    state[PitchedInstruments.BASS.value][bass_pos] == States.FILL_0_1.value
            ):
                rest = m21.note.Rest(self.BEAT_DURATION * 1/2)
                current_measure.append(rest)

                new_bass_note.quarterLength = self.BEAT_DURATION * 1/2
                next_bass_pos = bass_pos + 1
                if next_bass_pos < len(bass_line):
                    #    next_bass_note = bass_line[next_bass_pos]
                    new_bass_note.tie = m21.tie.Tie('start')
            else:
                new_bass_note.quarterLength = bass_note.quarterLength

            current_measure.append(new_bass_note)

        bass_part.append(current_measure)

        return bass_part

    def _drum_instrument_to_music21_part(
        self, drum_instrument, state, pattern_length
    ):
        """
        Converts a specific instrument's pattern to a music21 part.

        Parameters:
            drum_instrument (DrumInstruments): The drum instrument (HIHAT, SNARE,
            KICK,).
            state (np.ndarray): The state array of the drum pattern.
            pattern_length (int): The length of the drum pattern.

        Returns:
            music21.stream.Part: A music21 part representation of the
                instrument's pattern.
        """
        drum_part = m21.stream.Part()
        drum_part.insert(m21.clef.PercussionClef())
        perc_instr = self.drumInstruments.get(drum_instrument)[0]()
        # Several percussion instruments (not all!) share the same HiHat music21 class.
        # In this case, the name of the instrument in the score can/must be changed
        if len(self.drumInstruments.get(drum_instrument)) > 2:
            perc_instr.instrumentName = self.drumInstruments.get(drum_instrument)[2]
            perc_instr.instrumentAbbreviation = self.drumInstruments.get(drum_instrument)[2]

        drum_part.insert(0, perc_instr)

        current_measure = m21.stream.Measure()

        for position in range(pattern_length):

            if current_measure.quarterLength + self.BEAT_DURATION > 4.0:
                drum_part.append(current_measure)
                current_measure = m21.stream.Measure()

            if (
                state[drum_instrument.value][position] == States.FILL_1.value
            ):  # If the instrument is ON at this position
                note_pitch = self._get_midi_pitch_for_instrument(
                    drum_instrument
                )
                drum_note = m21.note.Note()
                drum_note.pitch.midi = note_pitch
                drum_note.volume.velocityScalar = self.VOLUME_INCREASE
                drum_note.quarterLength = self.BEAT_DURATION

                current_measure.append(drum_note)

            elif (
                state[drum_instrument.value][position] == States.FILL_2_1.value
            ):
                note_pitch = self._get_midi_pitch_for_instrument(
                    drum_instrument
                )
                drum_note1 = m21.note.Note()
                drum_note1.pitch.midi = note_pitch
                drum_note1.volume.velocityScalar = self.VOLUME_INCREASE
                drum_note1.quarterLength = self.BEAT_DURATION * 1/2

                current_measure.append(drum_note1)

                drum_note2 = m21.note.Note()
                drum_note2.pitch.midi = note_pitch
                drum_note2.volume.velocityScalar = self.VOLUME_INCREASE
                drum_note2.duration.quarterLength = self.BEAT_DURATION * 1/2

                current_measure.append(drum_note2)

            elif (
                state[drum_instrument.value][position] == States.FILL_0_1.value
            ):
                drum_rest1 = m21.note.Rest(self.BEAT_DURATION * 1/2)

                current_measure.append(drum_rest1)

                note_pitch = self._get_midi_pitch_for_instrument(
                    drum_instrument
                )
                drum_note2 = m21.note.Note()
                drum_note2.pitch.midi = note_pitch
                drum_note2.volume.velocityScalar = self.VOLUME_INCREASE
                drum_note2.duration.quarterLength = self.BEAT_DURATION * 1/2

                current_measure.append(drum_note2)

            elif (
                state[drum_instrument.value][position] == States.OFF.value
            ):

                current_measure.append(m21.note.Rest(self.BEAT_DURATION))

            else:

                print("Unknown state", state[drum_instrument.value][position])

        drum_part.append(current_measure)

        return drum_part

    def _get_midi_pitch_for_instrument(self, drum_instrument):
        """
        Retrieves the MIDI pitch corresponding to a drum instrument.

        Parameters:
            drum_instrument (DrumInstruments): The drum instrument (KICK, SNARE,
                HIHAT).

        Returns:
            int: The MIDI pitch number corresponding to the instrument.
        """
        return self.drumInstruments.get(
            drum_instrument, 0
        )[1]  # Default to 0 if not found

