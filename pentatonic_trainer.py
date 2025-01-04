import pygame
import sounddevice as sd
import numpy as np
import json
import time
import os
from dataclasses import dataclass
from typing import List, Dict, Optional
import scipy.signal

@dataclass
class Note:
    fret: int
    string: int
    frequency: float
    name: str

@dataclass
class ScalePosition:
    name: str
    notes: List[Note]
    description: str
    tab: str

class PentatonicTrainer:
    def __init__(self):
        pygame.init()
        pygame.mixer.init()
        
        self.SAMPLE_RATE = 44100
        self.CHUNK_SIZE = 1024
        self.starting_bpm = 120
        self.current_bpm = self.starting_bpm
        self.target_bpm = 240  # Default target BPM
        self.FREQUENCY_TOLERANCE = 0.5
        
        self.string_frequencies = {
            6: 82.41,  # E2
            5: 110.00, # A2
            4: 146.83, # D3
            3: 196.00, # G3
            2: 246.94, # B3
            1: 329.63  # E4
        }

        self.note_names = {
            6: ["E", "F", "F#", "G", "G#", "A", "A#", "B", "C", "C#", "D", "D#"],
            5: ["A", "A#", "B", "C", "C#", "D", "D#", "E", "F", "F#", "G", "G#"],
            4: ["D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B", "C", "C#"],
            3: ["G", "G#", "A", "A#", "B", "C", "C#", "D", "D#", "E", "F", "F#"],
            2: ["B", "C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#"],
            1: ["E", "F", "F#", "G", "G#", "A", "A#", "B", "C", "C#", "D", "D#"]
        }
        
        self.scale_positions = {
            "position1": self.create_scale_position1(),
            "position2": self.create_scale_position2(),
            "position3": self.create_scale_position3(),
            "position4": self.create_scale_position4(),
            "position5": self.create_scale_position5()
        }
        
        self.progress = {
            "total_score": 0,
            "games_won": [],
            "target_bpm": self.target_bpm,
            "level_accuracies": {},  # Store accuracies for each level/bpm combination
            "highest_bpm": self.starting_bpm,
            "positions_unlocked": ["position1"]
        }

        
        self.load_progress()

    def calculate_note_frequency(self, string: int, fret: int) -> float:
        base_freq = self.string_frequencies[string]
        return base_freq * (2 ** (fret/12))

    def get_note_name(self, string: int, fret: int) -> str:
        return self.note_names[string][fret % 12]

    def create_scale_position1(self) -> ScalePosition:
        notes = [
            Note(5, 6, self.calculate_note_frequency(6, 5), self.get_note_name(6, 5)),   # A
            Note(8, 6, self.calculate_note_frequency(6, 8), self.get_note_name(6, 8)),   # C
            Note(5, 5, self.calculate_note_frequency(5, 5), self.get_note_name(5, 5)),   # D
            Note(7, 5, self.calculate_note_frequency(5, 7), self.get_note_name(5, 7)),   # E
            Note(5, 4, self.calculate_note_frequency(4, 5), self.get_note_name(4, 5)),   # G
            Note(7, 4, self.calculate_note_frequency(4, 7), self.get_note_name(4, 7)),   # A
            Note(5, 3, self.calculate_note_frequency(3, 5), self.get_note_name(3, 5)),   # C
            Note(7, 3, self.calculate_note_frequency(3, 7), self.get_note_name(3, 7)),   # D
            Note(5, 2, self.calculate_note_frequency(2, 5), self.get_note_name(2, 5)),   # E
            Note(8, 2, self.calculate_note_frequency(2, 8), self.get_note_name(2, 8)),   # G
            Note(5, 1, self.calculate_note_frequency(1, 5), self.get_note_name(1, 5)),   # A
            Note(8, 1, self.calculate_note_frequency(1, 8), self.get_note_name(1, 8))    # C
        ]
        
        tab = """
e|---5--8-------------------------
b|---5--8-------------------------
G|---5--7-------------------------
D|---5--7-------------------------
A|---5--7-------------------------
E|---5--8-------------------------"""
        
        return ScalePosition(
            "Position 1 - A Minor Pentatonic",
            notes,
            "The foundation position starting on the root note A",
            tab
        )

    def create_scale_position2(self) -> ScalePosition:
        notes = [
            Note(8, 6, self.calculate_note_frequency(6, 8), self.get_note_name(6, 8)),   # C
            Note(10, 6, self.calculate_note_frequency(6, 10), self.get_note_name(6, 10)), # D
            Note(7, 5, self.calculate_note_frequency(5, 7), self.get_note_name(5, 7)),   # E
            Note(10, 5, self.calculate_note_frequency(5, 10), self.get_note_name(5, 10)), # G
            Note(7, 4, self.calculate_note_frequency(4, 7), self.get_note_name(4, 7)),   # A
            Note(10, 4, self.calculate_note_frequency(4, 10), self.get_note_name(4, 10)), # C
            Note(7, 3, self.calculate_note_frequency(3, 7), self.get_note_name(3, 7)),   # D
            Note(9, 3, self.calculate_note_frequency(3, 9), self.get_note_name(3, 9)),   # E
            Note(8, 2, self.calculate_note_frequency(2, 8), self.get_note_name(2, 8)),   # G
            Note(10, 2, self.calculate_note_frequency(2, 10), self.get_note_name(2, 10)), # A
            Note(8, 1, self.calculate_note_frequency(1, 8), self.get_note_name(1, 8)),   # C
            Note(10, 1, self.calculate_note_frequency(1, 10), self.get_note_name(1, 10))  # D
        ]
        
        tab = """
e|---8--10------------------------
b|---8--10------------------------
G|---7--9-------------------------
D|---7--10------------------------
A|---7--10------------------------
E|---8--10------------------------"""
        
        return ScalePosition(
            "Position 2 - A Minor Pentatonic",
            notes,
            "The second position, starting on C",
            tab
        )

    def create_scale_position3(self) -> ScalePosition:
        notes = [
            Note(10, 6, self.calculate_note_frequency(6, 10), self.get_note_name(6, 10)), # D
            Note(12, 6, self.calculate_note_frequency(6, 12), self.get_note_name(6, 12)), # E
            Note(10, 5, self.calculate_note_frequency(5, 10), self.get_note_name(5, 10)), # G
            Note(12, 5, self.calculate_note_frequency(5, 12), self.get_note_name(5, 12)), # A
            Note(10, 4, self.calculate_note_frequency(4, 10), self.get_note_name(4, 10)), # C
            Note(12, 4, self.calculate_note_frequency(4, 12), self.get_note_name(4, 12)), # D
            Note(9, 3, self.calculate_note_frequency(3, 9), self.get_note_name(3, 9)),   # E
            Note(12, 3, self.calculate_note_frequency(3, 12), self.get_note_name(3, 12)), # G
            Note(10, 2, self.calculate_note_frequency(2, 10), self.get_note_name(2, 10)), # A
            Note(12, 2, self.calculate_note_frequency(2, 12), self.get_note_name(2, 12)), # C
            Note(10, 1, self.calculate_note_frequency(1, 10), self.get_note_name(1, 10)), # D
            Note(12, 1, self.calculate_note_frequency(1, 12), self.get_note_name(1, 12))  # E
        ]
        
        tab = """
e|---10-12------------------------
b|---10-12------------------------
G|---9--12------------------------
D|---10-12------------------------
A|---10-12------------------------
E|---10-12------------------------"""
        
        return ScalePosition(
            "Position 3 - A Minor Pentatonic",
            notes,
            "The third position, starting on D",
            tab
        )

    def create_scale_position4(self) -> ScalePosition:
        notes = [
            Note(12, 6, self.calculate_note_frequency(6, 12), self.get_note_name(6, 12)), # E
            Note(15, 6, self.calculate_note_frequency(6, 15), self.get_note_name(6, 15)), # G
            Note(12, 5, self.calculate_note_frequency(5, 12), self.get_note_name(5, 12)), # A
            Note(15, 5, self.calculate_note_frequency(5, 15), self.get_note_name(5, 15)), # C
            Note(12, 4, self.calculate_note_frequency(4, 12), self.get_note_name(4, 12)), # D
            Note(14, 4, self.calculate_note_frequency(4, 14), self.get_note_name(4, 14)), # E
            Note(12, 3, self.calculate_note_frequency(3, 12), self.get_note_name(3, 12)), # G
            Note(14, 3, self.calculate_note_frequency(3, 14), self.get_note_name(3, 14)), # A
            Note(12, 2, self.calculate_note_frequency(2, 12), self.get_note_name(2, 12)), # C
            Note(15, 2, self.calculate_note_frequency(2, 15), self.get_note_name(2, 15)), # D
            Note(12, 1, self.calculate_note_frequency(1, 12), self.get_note_name(1, 12)), # E
            Note(15, 1, self.calculate_note_frequency(1, 15), self.get_note_name(1, 15))  # G
        ]
        
        tab = """
e|---12-15------------------------
b|---12-15------------------------
G|---12-14------------------------
D|---12-14------------------------
A|---12-15------------------------
E|---12-15------------------------"""
        
        return ScalePosition(
            "Position 4 - A Minor Pentatonic",
            notes,
            "The fourth position, starting on E",
            tab
        )

    def create_scale_position5(self) -> ScalePosition:
        notes = [
            Note(15, 6, self.calculate_note_frequency(6, 15), self.get_note_name(6, 15)), # G
            Note(17, 6, self.calculate_note_frequency(6, 17), self.get_note_name(6, 17)), # A
            Note(15, 5, self.calculate_note_frequency(5, 15), self.get_note_name(5, 15)), # C
            Note(17, 5, self.calculate_note_frequency(5, 17), self.get_note_name(5, 17)), # D
            Note(14, 4, self.calculate_note_frequency(4, 14), self.get_note_name(4, 14)), # E
            Note(17, 4, self.calculate_note_frequency(4, 17), self.get_note_name(4, 17)), # G
            Note(14, 3, self.calculate_note_frequency(3, 14), self.get_note_name(3, 14)), # A
            Note(17, 3, self.calculate_note_frequency(3, 17), self.get_note_name(3, 17)), # C
            Note(15, 2, self.calculate_note_frequency(2, 15), self.get_note_name(2, 15)), # D
            Note(17, 2, self.calculate_note_frequency(2, 17), self.get_note_name(2, 17)), # E
            Note(15, 1, self.calculate_note_frequency(1, 15), self.get_note_name(1, 15)), # G
            Note(17, 1, self.calculate_note_frequency(1, 17), self.get_note_name(1, 17))  # A
        ]
        
        tab = """
e|---15-17------------------------
b|---15-17------------------------
G|---14-17------------------------
D|---14-17------------------------
A|---15-17------------------------
E|---15-17------------------------"""
        
        return ScalePosition(
            "Position 5 - A Minor Pentatonic",
            notes,
            "The fifth position, starting on G",
            tab
        )

    def generate_note(self, frequency: float, duration: float) -> np.ndarray:
        """Generate a synthesized guitar-like note."""
        t = np.linspace(0, duration, int(self.SAMPLE_RATE * duration))
        
        # Fundamental frequency
        note = np.sin(2 * np.pi * frequency * t)
        
        # Add harmonics for a more guitar-like sound
        harmonics = [1.0, 0.5, 0.3, 0.2]
        for i, amplitude in enumerate(harmonics[1:], 2):
            note += amplitude * np.sin(2 * np.pi * frequency * i * t)
        
        # Apply envelope
        attack = 0.02
        decay = 0.1
        sustain_level = 0.7
        release = 0.3
        
        envelope = np.ones_like(t)
        attack_samples = int(attack * self.SAMPLE_RATE)
        decay_samples = int(decay * self.SAMPLE_RATE)
        release_samples = int(release * self.SAMPLE_RATE)
        
        envelope[:attack_samples] = np.linspace(0, 1, attack_samples)
        envelope[attack_samples:attack_samples + decay_samples] = np.linspace(1, sustain_level, decay_samples)
        envelope[-release_samples:] = np.linspace(sustain_level, 0, release_samples)
        
        return note * envelope * 0.3

    def play_demonstration(self, scale: ScalePosition, bpm: int) -> None:
        """Play the scale notes as a demonstration."""
        print("\nPlaying demonstration...")
        seconds_per_beat = 60.0 / bpm
        
        # Generate metronome click
        t = np.linspace(0, 0.05, int(0.05 * self.SAMPLE_RATE))
        click = np.sin(2 * np.pi * 1000 * t) * np.exp(-10 * t) * 0.3
        
        # First play the metronome for 4 beats
        for i in range(4):
            print(f"Count: {i+1}")
            sd.play(click, self.SAMPLE_RATE)
            time.sleep(seconds_per_beat)
        
        # Play the scale up
        print("\nPlaying scale up:")
        for note in scale.notes:
            print(f"Playing {note.name} ({note.frequency:.1f}Hz)")
            audio = self.generate_note(note.frequency, seconds_per_beat)
            audio[:len(click)] += click
            sd.play(audio, self.SAMPLE_RATE)
            sd.wait()
        
        # Play the scale down
        print("\nPlaying scale down:")
        for note in reversed(scale.notes):
            print(f"Playing {note.name} ({note.frequency:.1f}Hz)")
            audio = self.generate_note(note.frequency, seconds_per_beat)
            audio[:len(click)] += click
            sd.play(audio, self.SAMPLE_RATE)
            sd.wait()
            
        print("\nDemonstration complete!")

    def detect_fundamental_frequency(self, audio_data: np.ndarray) -> Optional[float]:
        """Detect fundamental frequency using zero-crossing rate and autocorrelation."""
        if len(audio_data) < self.CHUNK_SIZE:
            return None
            
        # Normalize audio
        audio_data = audio_data / np.max(np.abs(audio_data))
        
        # Apply window function
        window = np.hanning(len(audio_data))
        audio_data = audio_data * window
        
        # Compute autocorrelation
        correlation = np.correlate(audio_data, audio_data, mode='full')
        correlation = correlation[len(correlation)//2:]
        
        # Find peaks in autocorrelation
        peaks = scipy.signal.find_peaks(correlation, height=0.1)[0]
        
        if len(peaks) > 0:
            first_peak = peaks[0]
            frequency = self.SAMPLE_RATE / first_peak
            return frequency
        return None

    def find_closest_note(self, frequency: float) -> str:
        """Find the closest note name for a given frequency."""
        # A4 = 440 Hz
        # Calculate number of semitones from A4
        semitones = 12 * np.log2(frequency / 440.0)
        # Round to nearest semitone
        semitones = round(semitones)
        
        # Note names starting from A
        notes = ['A', 'A#', 'B', 'C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#']
        # Calculate octave and note index
        octave = 4 + (semitones + 9) // 12  # +9 because we start from A
        note_idx = (semitones + 9) % 12
        
        return f"{notes[note_idx]}{octave}"

    def generate_metronome(self, bpm: int, num_beats: int) -> np.ndarray:
        """Generate metronome clicks at specified BPM."""
        samples_per_beat = int(60.0 / bpm * self.SAMPLE_RATE)
        total_samples = int(num_beats * samples_per_beat)
        
        t = np.linspace(0, 0.05, int(0.05 * self.SAMPLE_RATE))
        click = np.sin(2 * np.pi * 1000 * t) * np.exp(-10 * t)
        click = np.pad(click, (0, samples_per_beat - len(click)))
        
        metronome = np.zeros(total_samples)
        for i in range(num_beats):
            start = i * samples_per_beat
            end = start + len(click)
            metronome[start:end] += click
            
        return metronome

    def play_game(self, position: str) -> None:
        scale = self.scale_positions[position]
        
        print("\n" + "="*50)
        print(f"Playing {scale.name}")
        print("="*50)
        
        print("\nNotes to play:")
        for note in scale.notes:
            print(f"String {note.string}, Fret {note.fret} ({note.name}): {note.frequency:.1f}Hz")
        
        print("\nTab:")
        print(scale.tab)
        
        while True:
            print("\nOptions:")
            print("1. Listen to demonstration")
            print("2. Start playing")
            print("3. Return to main menu")
            
            choice = input("\nEnter your choice (1-3): ")
            
            if choice == "1":
                self.play_demonstration(scale, self.current_bpm)
            elif choice == "2":
                break
            elif choice == "3":
                return
        
        print("\nInstructions:")
        print("1. You will hear four count-in clicks")
        print("2. Start playing on the fifth click")
        print("3. Play each note with the metronome")
        print(f"4. Current tempo: {self.current_bpm} BPM")
        
        input("\nPress Enter when ready...")
        
        # Generate metronome
        notes_per_direction = len(scale.notes)
        total_beats = 4 + (notes_per_direction * 2)  # 4 count-in beats + notes up and down
        metronome = self.generate_metronome(self.current_bpm, total_beats)
        
        # Count in
        for i in range(3, 0, -1):
            print(f"{i}...")
            time.sleep(1)
        print("Start playing on the fifth click!")
        
        # Record and play
        recording = []
        with sd.InputStream(channels=1, samplerate=self.SAMPLE_RATE, 
                          blocksize=self.CHUNK_SIZE) as stream:
            sd.play(metronome, self.SAMPLE_RATE)
            
            total_samples = len(metronome)
            samples_recorded = 0
            
            print("\nRecording...")
            while samples_recorded < total_samples:
                audio_chunk, _ = stream.read(self.CHUNK_SIZE)
                recording.extend(audio_chunk.flatten())
                samples_recorded += len(audio_chunk.flatten())
                
                if samples_recorded % (self.SAMPLE_RATE // 2) == 0:
                    print(".", end="", flush=True)
        
        print("\n\nAnalyzing your playing...")
        recording = np.array(recording)
        
        # Skip the count-in portion
        start_sample = int(4 * (60.0 / self.current_bpm) * self.SAMPLE_RATE)
        playing_audio = recording[start_sample:]
        
        # Analyze in chunks corresponding to expected note timing
        samples_per_beat = int(60.0 / self.current_bpm * self.SAMPLE_RATE)
        notes_detected = []
        
        for i in range(0, len(playing_audio), samples_per_beat):
            chunk = playing_audio[i:i + samples_per_beat]
            if len(chunk) >= self.CHUNK_SIZE:
                freq = self.detect_fundamental_frequency(chunk)
                if freq is not None:
                    notes_detected.append(freq)
                    print(f"Detected frequency: {freq:.1f}Hz")
        
        # Compare with expected notes
        expected_notes = scale.notes + list(reversed(scale.notes))
        correct_notes = 0
        
        for detected, expected in zip(notes_detected, expected_notes):
            if detected is not None:
                ratio = detected / expected.frequency
                semitone_distance = abs(12 * np.log2(ratio))
                
                if semitone_distance <= self.FREQUENCY_TOLERANCE:
                    correct_notes += 1
                    print(f"✓ Correct note: {expected.name}")
                else:
                    detected_note = self.find_closest_note(detected)
                    print(f"✗ Expected {expected.name}, got {detected_note}")
        
        expected_note_count = len(expected_notes)
        if expected_note_count > 0:
            accuracy = (correct_notes / expected_note_count) * 100
        else:
            accuracy = 0
        
        print(f"\nAccuracy: {accuracy:.1f}%")
        print(f"Correct notes: {correct_notes} out of {expected_note_count}")
        
        # Store accuracy for this attempt
        level_key = f"{scale.name}_{self.current_bpm}"
        if level_key not in self.progress["level_accuracies"]:
            self.progress["level_accuracies"][level_key] = []
        self.progress["level_accuracies"][level_key].append(accuracy)
        
        if accuracy == 100:
            print("Excellent! You've mastered this tempo!")
            self.progress["games_won"].append(f"{scale.name} at {self.current_bpm} BPM")
            self.current_bpm = min(self.current_bpm + 10, self.progress["target_bpm"])
            self.progress["highest_bpm"] = max(self.progress["highest_bpm"], self.current_bpm)
            # Unlock next position if available
            current_pos = int(position[-1])  # Get the number from position1, position2, etc.
            next_pos = f"position{current_pos + 1}"
            if current_pos < 5 and next_pos not in self.progress["positions_unlocked"]:
                self.progress["positions_unlocked"].append(next_pos)
                print(f"\nCongratulations! You've unlocked {self.scale_positions[next_pos].name}!")            
        else:
            print("\nYou need 100% accuracy to progress to the next tempo.")
            print("Keep practicing! Try to hit each note clearly on the beat.")
            print(f"\nYour accuracy history for {scale.name} at {self.current_bpm} BPM:")
            accuracies = self.progress["level_accuracies"][level_key]
            print(f"Best: {max(accuracies):.1f}%")
            print(f"Average: {sum(accuracies)/len(accuracies):.1f}%")
            
        self.save_progress()

    def save_progress(self) -> None:
        with open("pentatonic_progress.json", "w") as f:
            json.dump(self.progress, f)
            
    def load_progress(self) -> None:
        if os.path.exists("pentatonic_progress.json"):
            try:
                with open("pentatonic_progress.json", "r") as f:
                    self.progress = {
                        "total_score": saved_progress.get("total_score", 0),
                        "games_won": saved_progress.get("games_won", []),
                        "target_bpm": saved_progress.get("target_bpm", self.target_bpm),
                        "level_accuracies": saved_progress.get("level_accuracies", {}),
                        "highest_bpm": saved_progress.get("highest_bpm", self.starting_bpm),
                        "positions_unlocked": saved_progress.get("positions_unlocked", ["position1"])
                   }
                self.current_bpm = self.progress["highest_bpm"]
            except:
                    print("Error loading progress, starting fresh.")

    def show_stats(self) -> None:
        print("\n=== Current Stats ===")
        print(f"Total Score: {self.progress['total_score']}")
        print(f"Highest BPM: {self.progress['highest_bpm']}")
        print(f"Target BPM: {self.progress['target_bpm']}")
        print("\nRecent Achievements:")
        for game in self.progress["games_won"][-5:]:
            print(f"- {game}")

        print("\nAccuracy History:")
        for level, accuracies in self.progress["level_accuracies"].items():
            position, bpm = level.rsplit('_', 1)
            print(f"\n{position} at {bpm} BPM:")
            print(f"  Attempts: {len(accuracies)}")
            print(f"  Best Accuracy: {max(accuracies):.1f}%")
            print(f"  Average Accuracy: {sum(accuracies)/len(accuracies):.1f}%")
            
    def set_target_bpm(self) -> None:
        print(f"\nCurrent target BPM: {self.progress['target_bpm']}")
        while True:
            try:
                new_target = input("Enter new target BPM (60-300, or press Enter to keep current): ")
                if not new_target:
                    return
                new_target = int(new_target)
                if 60 <= new_target <= 300:
                    self.progress['target_bpm'] = new_target
                    print(f"Target BPM set to {new_target}")
                    self.save_progress()
                    break
                else:
                    print("Please enter a value between 60 and 300")
            except ValueError:
                print("Please enter a valid number")
            
    def run(self) -> None:
        while True:
            print("\n=== Pentatonic Scale Trainer ===")
            print("1. Play Available Positions")
            print("2. View Stats")
            print("3. Set Target BPM")
            print("4. Reset Progress")
            print("5. Quit")
            
            choice = input("\nEnter your choice (1-5): ")
            
            if choice == "1":
                for position in self.progress["positions_unlocked"]:
                    self.play_game(position)
                    again = input("\nWould you like to try this position again? (y/n): ")
                    if again.lower() != 'y':
                        break
            elif choice == "2":
                self.show_stats()
            elif choice == "3":
                self.set_target_bpm()
            elif choice == "4":
                confirm = input("Are you sure you want to reset progress? (y/n): ")
                if confirm.lower() == 'y':
                    self.progress = {
                        "total_score": 0,
                        "games_won": [],
                        "target_bpm": self.target_bpm,
                        "level_accuracies": {},
                        "highest_bpm": self.starting_bpm,
                        "positions_unlocked": ["position1"]
                    }
                    self.current_bpm = self.starting_bpm
                    self.save_progress()
            elif choice == "5":
                break

if __name__ == "__main__":
    trainer = PentatonicTrainer()
    trainer.run()
