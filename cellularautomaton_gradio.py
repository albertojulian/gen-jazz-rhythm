import gradio as gr

import os

from pattern_m21_converter import PatternMusic21Converter, PitchedInstruments, DrumInstruments, States, melody_instruments_d
from m21_musescore import M21_and_show
from omnibook_read import chords_and_m21melody

CHORD_SPLIT = ":"
MEASURE_DURATION = 4

import numpy as np
import music21 as m21 # instrument, metadata, note, stream, clef, tie


class CellularAutomatonBackMusicGenerator:
    """
    Generates back patterns using a cellular automaton.

    TODO: update
    This class simulates a 2D cellular automaton where each cell represents a
    drum sound (kick, snare, or hi-hat) at a given time step. The state of
    each cell evolves based on predefined rules, resulting in a rhythmic
    drum pattern.

    Attributes:
        pattern_length (int): Length of the drum pattern in beats.
        state (np.ndarray): Current state of the drum pattern.
    """

    # HIHAT_ON_PROBABILITY = 0.7
    MUTATION_PROBABILITY = 0.1
    MELODY_SYNC_PROBABILITY = 0.7
    # CHORD_TIE_PROBABILITY = 0.5
    EVEN_BEAT_SWING_PROBABILITY = 0.2
    ODD_BEAT_SWING_PROBABILITY = 0.8

    def __init__(self, melody, chord_sequence, synco_prob=0.5, kick_crash_prob=0.2, print_states=False):
        """
        Initializes the CellularAutomatonBackMusicGenerator with a specified pattern
        length.

        TODO: update
        Parameters:
            pattern_length (int): The length of the drum pattern in beats.
        """

        self.melody = melody
        self.chord_sequence = chord_sequence

        # pattern_length (int): The length of the drum pattern in beats.
        # e.g. length==16 => 4 measures 4/4 if beat==quarter, 2 measures if beat==8th
        self.pattern_length = sum([duration for (_, duration) in self.chord_sequence])

        self.state = self._initialize_state(self.pattern_length)

        self.beat_bass_sequence, self.beat_chord_sequence = self._initialize_beat_pitch_sequences()

        self.SYNCOPATION_PROBABILITY = synco_prob
        self.KICK_OR_CRASH_PROBABILITY = kick_crash_prob  # only when syncopation occurs

        self.print_states = print_states
        if print_states==True:
            print("Initial states:\n", self.state)

        self._rules = {
            # "jazz_chord": self._apply_jazz_chord_rule,
            # "jazz_bass": self._apply_jazz_bass_rule,
            "jazz_drum": self._apply_jazz_drum_rule,
            "jazz_syncopation": self._apply_jazz_syncopation_rule,
            # "note_continuity": self._apply_note_continuity_rule,
        }

    def step(self, s):
        """
        Advances the drum pattern by one time step by applying the defined
        rules.
        """

        # print(self.beat_chord_sequence)
        # print(self.beat_bass_sequence)

        new_state = self.state.copy()
        for position in range(self.pattern_length):
            new_state = self._apply_rules(position, new_state)
        self.state = new_state

        if self.print_states==True:
            print(f"States after step {s}:\n", self.state)


    def _initialize_beat_pitch_sequences(self):

        beat_bass_sequence = []
        beat_chord_sequence = []
        position = 0
        for (chord_name, chord_duration) in self.chord_sequence:
            chord_bass, chord_type = chord_name.split(CHORD_SPLIT)
            for i in range(chord_duration):
                beat_bass_sequence.append(chord_bass)
                beat_chord_sequence.append(chord_name)

                # TODO bad behaviour with chord version changes in m21_musescore
                # if (i < chord_duration - 1) and np.random.random() < self.CHORD_TIE_PROBABILITY:
                #    chord_state = States.FILL_1_T.value
                # else:
                #    chord_state = States.FILL_1.value
                chord_state = States.FILL_1.value

                # self.state[PitchedInstruments.MELODY.value][position] = States.FILL_1.value

                self.state[PitchedInstruments.CHORD.value][position] = chord_state

                self.state[PitchedInstruments.BASS.value][position] = States.FILL_1.value

                position += 1

        return beat_bass_sequence, beat_chord_sequence

    def _initialize_state(self, pattern_length):
        """
        Randomly initializes the state of the drum pattern.

        Parameters:
            pattern_length (int): The length of the drum pattern in beats.

        Returns:
            np.ndarray: The initial state array.
        """
        number_of_instruments = len(DrumInstruments) + len(PitchedInstruments)
        init_state = np.zeros((number_of_instruments, pattern_length), dtype=int)

        return init_state

    def _apply_rules(self, position, new_state):
        """
        Applies the set of rules to the drum pattern at a given position.

        Parameters:
            position (int): The current position in the drum pattern.
            new_state (np.ndarray): The state array being modified.

        Returns:
            np.ndarray: The updated state array after applying the rules.
        """
        for rule in self._rules.values():
            new_state = rule(position, new_state)
        return new_state

    def _apply_jazz_chord_rule(self, position, new_state):

        new_state[PitchedInstruments.CHORD.value][position] = States.FILL_1.value

        return new_state

    def _apply_jazz_bass_rule(self, position, new_state):

        new_state[PitchedInstruments.BASS.value][position] = States.FILL_1.value

        return new_state

    def _apply_jazz_drum_rule(self, position, new_state):

        if (position % 2) == 0: # even beats: no hihat, one ride beat
            new_foot_hihat_state = States.OFF.value

            if np.random.random() < self.EVEN_BEAT_SWING_PROBABILITY:
                new_ride_cymbal_state = States.FILL_2_1.value
            else:
                new_ride_cymbal_state = States.FILL_1.value

        else: # odd beats: one hihat beat, swing ride beat
            new_foot_hihat_state = States.FILL_1.value

            if np.random.random() < self.ODD_BEAT_SWING_PROBABILITY:
                new_ride_cymbal_state = States.FILL_2_1.value
            else:
                new_ride_cymbal_state = States.OFF.value

        new_state[DrumInstruments.FOOT_HIHAT.value][position] = new_foot_hihat_state
        new_state[DrumInstruments.RIDE.value][position] = new_ride_cymbal_state

        return new_state

    def _apply_jazz_syncopation_rule(self, position, new_state):
        """
        If a chord type is V7 or o7, randomly replace first beat by quarter rest + 8th.
        Add snare and bass (kick) drum
        """
        if np.random.random() < self.SYNCOPATION_PROBABILITY:
            next_position = position + 1

            if next_position < self.pattern_length:
                chord_name = self.beat_chord_sequence[position]
                chord_type = chord_name.split(CHORD_SPLIT)[1]
                next_chord_name = self.beat_chord_sequence[next_position]
                if chord_name == next_chord_name:

                    if chord_type in ["7", "7(b9)", "o7"]:
                        # new_state[PitchedInstruments.MELODY.value][position] = States.FILL_0_1.value

                        new_state[PitchedInstruments.CHORD.value][position] = States.FILL_0_1.value
                        new_state[PitchedInstruments.BASS.value][position] = States.FILL_0_1.value
                        new_state[DrumInstruments.SNARE.value][position] = States.FILL_0_1.value
                        new_state[DrumInstruments.KICK.value][position] = States.FILL_0_1.value
                        new_state[DrumInstruments.HIHAT.value][position] = States.FILL_0_1.value

                    else:
                        if position > 0:
                            prev_position = position - 1

                            prev_chord_name = self.beat_chord_sequence[prev_position]
                            # Avoid syncopation if previous chord has same name and is [syncopated or tied]
                            if prev_chord_name != chord_name or \
                                    new_state[PitchedInstruments.CHORD.value][prev_position] not in \
                                [States.FILL_0_1.value, States.FILL_1_T.value]:
                                new_state[PitchedInstruments.CHORD.value][position] = States.FILL_0_1.value

            kick_or_crash = np.random.random()
            if kick_or_crash < self.KICK_OR_CRASH_PROBABILITY: # 0 < random < KICK_OR_CRASH_PROB
                new_state[DrumInstruments.KICK.value][position] = States.FILL_1.value
            elif kick_or_crash > (1 - self.KICK_OR_CRASH_PROBABILITY): # crash prob is same as kick: 1 > random > (1 - KICK_OR_CRASH_PROB)
                new_state[DrumInstruments.CRASH.value][position] = States.FILL_1.value

        return new_state

    def _apply_note_continuity_rule(self, position, new_state):

        next_position = position + 1
        if next_position < self.pattern_length:
            bass_note = self.beat_bass_sequence[position]
            melody_note = self.melody[position]
            melody_note_midi = m21.pitch.Pitch(melody_note).midi

            next_bass_note = self.beat_bass_sequence[next_position]
            next_melody_note = self.melody[next_position]
            next_melody_note_midi = m21.pitch.Pitch(next_melody_note).midi

            if melody_note_midi == next_melody_note_midi:
                if bass_note != next_bass_note:
                    # tie current note to next
                    new_state[PitchedInstruments.MELODY.value][position] = States.FILL_1_T.value
            else:
                if np.random.random() < self.MELODY_SYNC_PROBABILITY:
                    # if np.random.random() < self.MELODY_SYNC_PROBABILITY:
                    if np.random.random() < (1 - self.MELODY_SYNC_PROBABILITY):
                        new_state[PitchedInstruments.MELODY.value][position] = States.FILL_2_1.value
                    else:
                        new_state[PitchedInstruments.MELODY.value][position] = States.FILL_0_1.value
                else:
                    if np.random.random() < self.MELODY_SYNC_PROBABILITY:
                        new_state[PitchedInstruments.MELODY.value][position] = States.OFF.value

            # the rest has been initialized to FILL_1

        return new_state

def show_leadsheet(selected_file, folder="./Omnibook"):

    if isinstance(selected_file, list):
        return "No file has been selected!"

    file_path = os.path.join(folder, selected_file)

    score = m21.converter.parse(file_path)
    file_name = file_path.split("/")[-1]
    score_title = file_name.strip(".xml") + " (original)"
    score.metadata = m21.metadata.Metadata(
        title=score_title
    )

    score.show()

    return f"Showing leadsheet {file_name}"

def list_files(folder="./Omnibook"):

    xml_files = [xml_file for xml_file in os.listdir(folder) if xml_file.endswith(".xml")]

    if np.random.random() < 0.5:
        reverse = True
    else:
        reverse = False

    xml_files.sort(reverse=reverse)

    return xml_files

def list_melody_instruments():

    melody_instruments_list = list(melody_instruments_d.keys())

    return melody_instruments_list

def add_rhythm(selected_file, selected_instrument=None,
               synco_prob=0.5, kick_crash_prob=0.2, octave_up_down=0,
               folder="./Omnibook"):

    if isinstance(selected_file, list):
        return "No file has been selected!"

    if selected_instrument is None or isinstance(selected_instrument, list):
        selected_instrument = list(melody_instruments_d.keys())[0]

    output = f"Adding rhythm to {selected_file} with {selected_instrument}"

    file_path = os.path.join(folder, selected_file)

    m21_and_show = M21_and_show()

    score_title = selected_file.split("/")[-1].strip(".xml")

    chord_progression, generated_melody, _, key, tempo = chords_and_m21melody(file_path)

    back_generator = CellularAutomatonBackMusicGenerator(
        melody=generated_melody,
        chord_sequence=chord_progression,
        synco_prob=synco_prob,
        kick_crash_prob=kick_crash_prob,
        print_states=False
    )

    for step in range(1):
    # for step in range(16):
        back_generator.step(step)

    beat_duration = 1
    beat_chord_sequence = back_generator.beat_chord_sequence
    # print(beat_chord_sequence)
    beat_chord_progression = [(chord_name, beat_duration) for chord_name in beat_chord_sequence]

    m21_chord_progression, m21_bass_line = m21_and_show.chord_seq_to_m21_chords_and_bass(
        beat_chord_progression)

    music_converter = PatternMusic21Converter(is_m21melody=True, key=key, tempo=tempo)

    melody_instrument = melody_instruments_d[selected_instrument]()

    score = music_converter.to_music21_score(back_generator.state,
                                             generated_melody,
                                             m21_chord_progression,
                                             m21_bass_line,
                                             score_title=score_title,
                                             melody_instrument=melody_instrument,
                                             octave_up_down=octave_up_down,
                                             )

    score.show()

    return output


with gr.Blocks() as demo:

    with gr.Row():

        with gr.Column(scale=1):

            xml_files = list_files()
            selected_file = gr.Dropdown(value=xml_files[0], choices=xml_files,
                                        label="Select an Omnibook tune")

            show_leadsheet_btn = gr.Button("Show leadsheet")

            show_output = gr.Textbox(label="Result")

        show_leadsheet_btn.click(show_leadsheet, inputs=selected_file, outputs=[show_output])

        with gr.Column(scale=1):
            melody_instruments_list = list_melody_instruments()
            selected_instrument = gr.Dropdown(value=melody_instruments_list[0], choices=melody_instruments_list,
                                              label="Select an instrument for the melody")

            add_rhythm_btn = gr.Button("Add Rhythm!!")

            add_rhythm_output = gr.Textbox(label="Result")

        with gr.Column(scale=1):

            octave_up_down = gr.Slider(minimum=-1, maximum=1, value=0, step=1,
                                       label="Transpose octave up (1) or down (-1)")
            synco_prob = gr.Slider(minimum=0, maximum=1, value=0.5,
                                   label="Syncopation probability")
            kick_crash_prob = gr.Slider(minimum=0, maximum=1, value=0.2,
                                        label="Kick/crash prob (linked to synco)")

        add_rhythm_btn.click(add_rhythm,
                             inputs=[selected_file, selected_instrument,
                                     synco_prob, kick_crash_prob, octave_up_down],
                             outputs=[add_rhythm_output])

demo.launch()