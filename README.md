# gen-jazz-rhythm
Taking a lead-sheet score file (with melody and chord symbols), it generates a score with: 
- the same melody
- the chords (except the root note) for piano, with some syncopation
- the root note of each chord is assigned to a double-bass
- drums playing jazz rhythm:
  - basic ride cymbal and foot hi hat play a typical swing jazz rhythm, with some variations
  - occasionally, all-drum syncopations synchronised with the piano
  - occasionally, some crash cymbal or kick drum beat

<img src="./Donna_Lee_orig.png" alt="Descripción de la imagen" width="500" height="200" />

[Download audio of Donna Lee lead-sheet](https://github.com/albertojulian/gen-jazz-rhythm/blob/main/Donna_Lee_orig.mp3)

![](./Donna_Lee_rhythm.png)
[Download audio of Donna Lee with rhythm](https://github.com/albertojulian/gen-jazz-rhythm/blob/main/Donna_Lee_rhythm.mp3)

## Lead-sheet files
Lead-sheet scores are stored in XML files with melody and chord symbols. The files are contained in the folder Omnibook, which is a collection of 50 tunes and solos from Charlie Parker.

## Execution
Run `cellularautomaton_gradio.py`. It will show a URL which, when clicking, will open an interface in the default web browser. 
![](./gradio_ui.png)
The interface is composed of: 
- two dropdown lists to select the tune and the melody instrument
- one button to show the lead-sheet score
- one button to add rhythm by executing the Cellular Automaton and show the score
- some sliders to control several parameters

## Score management and display
The music elements are managed with the `music21` python library. When the score is complete, it is shown in MuseScore (or another xml interpreter integrated with `music21`). 

In case the score is played in MuseScore, it will

## Credits
Omnibook files, Ken Deguernel

Cellular Automaton framework: The Sound of AI

## Comments
### Chord types

### Tempo in Omnibook files
Tempo is included in the first measure of Omnibook files, and added to the score to be shown (and played)

### Swing style
In a standard swing style for slow to medium tempos (quarter=150 or less), two eighths are interpreted as a triplet of a quarter and an eighth: 
<img src="./standard_swing.png" alt="Standard jazz swing" width="100" height="50" />

Unfortunately, I have not seen a way for `music21` to report MuseScore that the score must be played in swing style. However, in MuseScore the swing style can be configured in the "Format/Style..." menu. Clicking in "Score" it provides several swing configurations. More information in MuseScore's page [Swing](https://musescore.org/en/handbook/3/swing).

### Key signature in Omnibook files
Although a Music XML file may include a proper key signature, all Omnibook files are loaded in music21 with a C major / A minor key signature: <music21.key.KeySignature of no sharps or flats>. This is the reason why none of the lead-sheets displays a key signature in MuseScore.

In order to display the Omnibook files with the proper key signature in MuseScore, the following sentences are executed:
`score = m21.converter.parse(omni_file); key = score.analyze("key")`

### Transposed instruments
Instruments such as alto sax, tenor sax, are said to be transposed: when a tenor sax in Bb plays a C, it sounds as a Bb; in other words, the transposition interval is **two semitones down**. 

Therefore, if we want to assign a tenor sax in Bb to a part in C, the part must be transposed **two semitones up** if we want to hear the part in C. This is the reason why the Omnibook files with rhythm may have different key signatures for melody and chords.