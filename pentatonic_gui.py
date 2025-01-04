import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk
from PIL import Image, ImageDraw, ImageTk
import pentatonic_trainer
import threading
import queue
import time
import numpy as np
import sounddevice as sd

class FretboardCanvas(tk.Canvas):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.fret_spacing = 40  # Reduced spacing to fit 24 frets
        self.string_spacing = 20
        self.left_margin = 30
        self.top_margin = 20
        self.num_frets = 24
        self.current_notes = []
        self.expected_note_marker = None
        
        # Draw initial fretboard
        self.draw_fretboard()
    
    def draw_fretboard(self):
        # Clear canvas
        self.delete("all")
        
        # Draw strings
        for i in range(6):
            y = self.top_margin + i * self.string_spacing
            self.create_line(
                self.left_margin, y,
                self.left_margin + self.fret_spacing * self.num_frets, y,
                width=2 if i == 0 else 1
            )
        
        # Draw frets
        for i in range(self.num_frets + 1):
            x = self.left_margin + i * self.fret_spacing
            self.create_line(
                x, self.top_margin,
                x, self.top_margin + 5 * self.string_spacing,
                width=2 if i == 0 else 1
            )
            
            # Draw fret numbers
            if i > 0:
                self.create_text(
                    x - self.fret_spacing/2,
                    self.top_margin + 6 * self.string_spacing,
                    text=str(i),
                    font=("Arial", 8)
                )
        
        # Draw fret markers
        markers = [3, 5, 7, 9, 12, 15, 17, 19, 21, 24]
        for fret in markers:
            x = self.left_margin + (fret - 0.5) * self.fret_spacing
            y = self.top_margin + 2.5 * self.string_spacing
            
            # Double marker at 12th and 24th fret
            if fret in [12, 24]:
                self.create_oval(
                    x-4, y-15-4,
                    x+4, y-15+4,
                    fill="gray"
                )
                self.create_oval(
                    x-4, y+15-4,
                    x+4, y+15+4,
                    fill="gray"
                )
            else:
                self.create_oval(
                    x-4, y-4,
                    x+4, y+4,
                    fill="gray"
                )

    def highlight_note(self, string, fret, color="red", tag="note"):
        x = self.left_margin + (fret - 0.5) * self.fret_spacing
        y = self.top_margin + (string - 1) * self.string_spacing
        note_id = self.create_oval(
            x-6, y-6,
            x+6, y+6,
            fill=color,
            tags=tag
        )
        if tag == "note":
            self.current_notes.append(note_id)
        return note_id

    def show_expected_note(self, string, fret):
        self.clear_expected_note()
        self.expected_note_marker = self.highlight_note(string, fret, color="yellow", tag="expected")

    def clear_expected_note(self):
        if self.expected_note_marker:
            self.delete(self.expected_note_marker)
            self.expected_note_marker = None

    def flash_note(self, string, fret, color="green", duration=200):
        note_id = self.highlight_note(string, fret, color=color, tag="flash")
        self.after(duration, lambda: self.delete(note_id))

    def clear_notes(self):
        for note_id in self.current_notes:
            self.delete(note_id)
        self.current_notes = []
        self.clear_expected_note()

class PentatonicGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Pentatonic Scale Trainer")
        self.geometry("1200x800")
        
        # Initialize the original trainer
        self.trainer = pentatonic_trainer.PentatonicTrainer()
        
        # Queue for communication between audio thread and GUI
        self.audio_queue = queue.Queue()
        
        self.create_widgets()
        self.current_position = None
        self.recording = False
        
    def create_widgets(self):
        # Main layout frames
        self.left_frame = ctk.CTkFrame(self)
        self.left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.right_frame = ctk.CTkFrame(self)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=10, pady=10)

        # Fretboard display
        self.fretboard = FretboardCanvas(
            self.left_frame,
            width=1200,
            height=200,
            bg="white"
        )
        self.fretboard.pack(pady=20)

        # Position selection
        self.position_frame = ctk.CTkFrame(self.left_frame)
        self.position_frame.pack(fill=tk.X, pady=10)

        ctk.CTkLabel(self.position_frame, text="Position:").pack(side=tk.LEFT, padx=5)

        self.position_var = tk.StringVar(value="Position 1")
        positions = [f"Position {i}" for i in range(1, 6)]
        self.position_menu = ctk.CTkOptionMenu(
            self.position_frame,
            values=positions,
            variable=self.position_var,
            command=self.change_position
        )
        self.position_menu.pack(side=tk.LEFT, padx=5)

        # BPM control
        self.bpm_frame = ctk.CTkFrame(self.left_frame)
        self.bpm_frame.pack(fill=tk.X, pady=10)

        ctk.CTkLabel(self.bpm_frame, text="BPM:").pack(side=tk.LEFT, padx=5)

        self.bpm_var = tk.StringVar(value=str(self.trainer.current_bpm))
        self.bpm_spinner = ttk.Spinbox(
            self.bpm_frame,
            from_=40,
            to=300,
            textvariable=self.bpm_var,
            width=5
        )
        self.bpm_spinner.pack(side=tk.LEFT, padx=5)

        # Target BPM control
        self.target_bpm_frame = ctk.CTkFrame(self.left_frame)
        self.target_bpm_frame.pack(fill=tk.X, pady=10)

        ctk.CTkLabel(self.target_bpm_frame, text="Target BPM:").pack(side=tk.LEFT, padx=5)

        self.target_bpm_var = tk.StringVar(value=str(self.trainer.progress["target_bpm"]))
        self.target_bpm_spinner = ttk.Spinbox(
            self.target_bpm_frame,
            from_=60,
            to=300,
            textvariable=self.target_bpm_var,
            width=5
        )
        self.target_bpm_spinner.pack(side=tk.LEFT, padx=5)

        self.set_target_button = ctk.CTkButton(
            self.target_bpm_frame,
            text="Set Target",
            command=self.set_target_bpm
        )
        self.set_target_button.pack(side=tk.LEFT, padx=5)

        # Control buttons
        self.button_frame = ctk.CTkFrame(self.left_frame)
        self.button_frame.pack(fill=tk.X, pady=10)

        self.demo_button = ctk.CTkButton(
            self.button_frame,
            text="Play Demo",
            command=self.play_demo
        )
        self.demo_button.pack(side=tk.LEFT, padx=5)

        self.practice_button = ctk.CTkButton(
            self.button_frame,
            text="Start Practice",
            command=self.toggle_practice
        )
        self.practice_button.pack(side=tk.LEFT, padx=5)

        self.show_stats_button = ctk.CTkButton(
            self.button_frame,
            text="Show Stats",
            command=self.show_detailed_stats
        )
        self.show_stats_button.pack(side=tk.LEFT, padx=5)

        # Add console output area
        ttk.Separator(self.left_frame, orient='horizontal').pack(fill='x', pady=10)

        self.console_frame = ctk.CTkFrame(self.left_frame)
        self.console_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        ctk.CTkLabel(self.console_frame, text="Console Output").pack()

        self.console = ctk.CTkTextbox(self.console_frame, height=200)
        self.console.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.console_print("Welcome to Pentatonic Scale Trainer!")
        self.console_print("Select a position and click 'Play Demo' to begin.")

    def console_print(self, text):
        self.console.insert('end', f"{text}\n")
        self.console.see('end')  # Auto-scroll to bottom
            
    def set_target_bpm(self):
        try:
            new_target = int(self.target_bpm_var.get())
            if 60 <= new_target <= 300:
                self.trainer.progress['target_bpm'] = new_target
                self.trainer.save_progress()
                self.update_status(f"Target BPM set to {new_target}")
            else:
                messagebox.showwarning("Invalid BPM", "Please enter a value between 60 and 300")
        except ValueError:
            messagebox.showwarning("Invalid Input", "Please enter a valid number")        

    def change_position(self, position):
        position_num = int(position.split()[-1])
        position_key = f"position{position_num}"

        if position_key in self.trainer.scale_positions:
            self.current_position = self.trainer.scale_positions[position_key]
            self.fretboard.clear_notes()
            
            # Highlight notes, with root notes in green
            for note in self.current_position.notes:
                # Check if it's a root note (A for A minor pentatonic)
                color = "green" if note.name == "A" else "red"
                self.fretboard.highlight_note(note.string, note.fret, color=color)
            
            # Display position info in console
            self.console.delete('1.0', tk.END)
            self.console_print(f"=== {self.current_position.name} ===")
            self.console_print(self.current_position.description)
            self.console_print("\nNotes in this position:")
            for note in self.current_position.notes:
                self.console_print(f"String {note.string}, Fret {note.fret}: {note.name}")
            self.console_print("\nTab diagram:")
            self.console_print(self.current_position.tab)
            self.console_print("\nInstructions:")
            self.console_print("1. Click 'Play Demo' to hear how it should sound")
            self.console_print("2. Practice along with the demo until you're comfortable")
            self.console_print("3. Click 'Start Practice' when ready to record and evaluate your playing")
            self.console_print("4. You'll hear 4 count-in clicks, then start playing on the 5th click")
            self.console_print("5. Play each note clearly with the metronome")
            self.console_print("6. Play the scale up and then back down")
            self.console_print(f"7. Current tempo: {self.trainer.current_bpm} BPM")


    def play_demo(self):
    
        self.update_status("Playing Demo")  
        
        if self.current_position:
            self.demo_button.configure(state="disabled")
            self.practice_button.configure(state="disabled")
            self.fretboard.clear_notes()
            
            # Display all notes with root notes in green
            for note in self.current_position.notes:
                color = "green" if note.name == "A" else "red"
                self.fretboard.highlight_note(note.string, note.fret, color=color)
            
            def run_demo():
                self.console.delete('1.0', tk.END)
                self.console_print("=== Playing Demo ===")
                self.console_print("Listen to the scale and watch the fretboard.")
                self.console_print("Each note will flash blue when it should be played.")
                
                seconds_per_beat = 60.0 / int(self.bpm_var.get())
                    
                # Generate metronome click
                t = np.linspace(0, 0.05, int(self.trainer.SAMPLE_RATE * 0.05))
                click = np.sin(2 * np.pi * 1000 * t) * np.exp(-10 * t) * 0.3
                
                # Play count-in
                for i in range(4):
                    self.after(0, lambda x=i: print(f"Count: {x+1}"))
                    sd.play(click, self.trainer.SAMPLE_RATE)
                    time.sleep(seconds_per_beat)
                
                # Play scale up
                print("\nPlaying scale up:")
                for note in self.current_position.notes:
                    self.after(0, lambda s=note.string, f=note.fret: 
                              self.fretboard.flash_note(s, f, "blue", duration=int(seconds_per_beat * 1000)))
                    audio = self.trainer.generate_note(note.frequency, seconds_per_beat)
                    audio[:len(click)] += click
                    sd.play(audio, self.trainer.SAMPLE_RATE)
                    sd.wait()
                
                # Play scale down
                print("\nPlaying scale down:")
                for note in reversed(self.current_position.notes):
                    self.after(0, lambda s=note.string, f=note.fret: 
                              self.fretboard.flash_note(s, f, "blue", duration=int(seconds_per_beat * 1000)))
                    audio = self.trainer.generate_note(note.frequency, seconds_per_beat)
                    audio[:len(click)] += click
                    sd.play(audio, self.trainer.SAMPLE_RATE)
                    sd.wait()
                
                # Re-enable buttons and restore red notes
                self.after(0, lambda: [
                    self.enable_buttons(),
                    self.fretboard.clear_notes(),
                    *[self.fretboard.highlight_note(note.string, note.fret, color="red") 
                      for note in self.current_position.notes]
                ])
            
            # Run demo in separate thread
            threading.Thread(target=run_demo, daemon=True).start()

    def toggle_practice(self):
        if not self.recording:
            self.update_status("Recording Practice")
            self.recording = True
            self.practice_button.configure(text="Stop Practice")
            self.console.delete('1.0', tk.END)
            self.console_print("=== Practice Session ===")
            self.console_print("Get ready to play!")
            self.console_print("\nReminders:")
            self.console_print("- Watch for the yellow highlight showing which note to play")
            self.console_print("- Play each note exactly on the metronome click")
            self.console_print("- Keep time even if you miss a note")
            self.console_print("- You need 100% accuracy to progress")
            self.console_print("- Start on the fifth click!")
            self.console_print(f"- Current tempo: {self.bpm_var.get()} BPM")
            self.console_print("\nStarting countdown...")
            self.recording = True
            self.practice_button.configure(text="Stop Practice")
            
            def practice_session():
                bpm = int(self.bpm_var.get())
                seconds_per_beat = 60.0 / bpm
                
                # Calculate total beats needed for entire sequence
                notes_per_direction = len(self.current_position.notes)
                total_beats = 4 + (notes_per_direction * 2)  # 4 count-in beats + notes up and down
                metronome = self.trainer.generate_metronome(bpm, total_beats)
                
                # Count in
                for i in range(3, 0, -1):
                    self.after(0, lambda x=i: print(f"{x}..."))
                    time.sleep(1)
                self.after(0, lambda: print("Start playing on the fifth click!"))
                
                # Record and play
                recording = []
                with sd.InputStream(
                    channels=1,
                    samplerate=self.trainer.SAMPLE_RATE,
                    blocksize=self.trainer.CHUNK_SIZE
                ) as stream:
                    sd.play(metronome, self.trainer.SAMPLE_RATE)
                    
                    total_samples = len(metronome)
                    samples_recorded = 0
                    beat_samples = int(seconds_per_beat * self.trainer.SAMPLE_RATE)
                    
                    self.console_print("\nRecording...")
                    while samples_recorded < total_samples:
                        audio_chunk, _ = stream.read(self.trainer.CHUNK_SIZE)
                        recording.extend(audio_chunk.flatten())
                        samples_recorded += len(audio_chunk.flatten())
                        
                        # Update expected note visual
                        beat_number = samples_recorded // beat_samples
                        notes_per_direction = len(self.current_position.notes)
                        
                        if 4 <= beat_number < total_beats:  # After count-in
                            play_index = beat_number - 4
                            if play_index < notes_per_direction:  # Ascending
                                note = self.current_position.notes[play_index]
                                print(f"Expected (up): {note.name}")
                            elif play_index < notes_per_direction * 2:  # Descending
                                reverse_index = notes_per_direction - (play_index - notes_per_direction) - 1
                                note = self.current_position.notes[reverse_index]
                                print(f"Expected (down): {note.name}")
                            else:
                                continue
                                
                            self.after(0, lambda s=note.string, f=note.fret: 
                                     self.fretboard.show_expected_note(s, f))
                
                self.console_print("\nAnalyzing recording...")
                self.analyze_recording(np.array(recording), bpm)
                self.after(0, self.after_practice)
            
            # Start practice session in separate thread
            threading.Thread(target=practice_session, daemon=True).start()
        else:
            self.update_status("Ready")
            self.recording = False
            self.practice_button.configure(text="Start Practice")
            
    def after_practice(self):
        self.practice_button.configure(text="Start Practice")
        self.recording = False
        self.update_stats()
        self.fretboard.clear_notes()
        for note in self.current_position.notes:
            color = "green" if note.name == "A" else "red"
            self.fretboard.highlight_note(note.string, note.fret, color=color)
        self.update_status("Ready")            
    
    def analyze_recording(self, recording, bpm):
        # Clear previous console output
        self.after(0, lambda: self.console.delete('1.0', tk.END))

        # Skip the count-in portion
        seconds_per_beat = 60.0 / bpm
        start_sample = int(4 * seconds_per_beat * self.trainer.SAMPLE_RATE)
        playing_audio = recording[start_sample:]

        # Analyze in chunks corresponding to expected note timing
        samples_per_beat = int(seconds_per_beat * self.trainer.SAMPLE_RATE)
        notes_detected = []

        for i in range(0, len(playing_audio), samples_per_beat):
            chunk = playing_audio[i:i + samples_per_beat]
            if len(chunk) >= self.trainer.CHUNK_SIZE:
                freq = self.trainer.detect_fundamental_frequency(chunk)
                if freq is not None:
                    notes_detected.append(freq)
                    self.console_print(f"Detected frequency: {freq:.1f}Hz")

        # Compare with expected notes
        expected_notes = self.current_position.notes + list(reversed(self.current_position.notes))
        correct_notes = 0

        for detected, expected in zip(notes_detected, expected_notes):
            if detected is not None:
                ratio = detected / expected.frequency
                semitone_distance = abs(12 * np.log2(ratio))
                
                if semitone_distance <= self.trainer.FREQUENCY_TOLERANCE:
                    correct_notes += 1
                    self.after(0, lambda s=expected.string, f=expected.fret:
                             self.fretboard.flash_note(s, f, "green"))
                    self.console_print(f"✓ Correct note: {expected.name}")
                else:
                    detected_note = self.trainer.find_closest_note(detected)
                    self.after(0, lambda s=expected.string, f=expected.fret:
                             self.fretboard.flash_note(s, f, "red"))
                    self.console_print(f"✗ Expected {expected.name}, got {detected_note}")

        # Calculate accuracy and update progress
        expected_note_count = len(expected_notes)
        if expected_note_count > 0:
            accuracy = (correct_notes / expected_note_count) * 100
            self.console_print(f"\nAccuracy: {accuracy:.1f}%")
            
            # Store accuracy and update progress
            level_key = f"{self.current_position.name}_{bpm}"
            if level_key not in self.trainer.progress["level_accuracies"]:
                self.trainer.progress["level_accuracies"][level_key] = []
            self.trainer.progress["level_accuracies"][level_key].append(accuracy)
            
            # Handle 100% accuracy achievements
            if accuracy == 100:
                self.console_print("\nExcellent! You've mastered this tempo!")
                self.trainer.progress["games_won"].append(f"{self.current_position.name} at {bpm} BPM")
                
                # Check for unlocking next position
                current_pos = int(self.current_position.name.split()[-1])  # Get position number from name
                next_pos = f"position{current_pos + 1}"
                if current_pos < 5 and next_pos not in self.trainer.progress["positions_unlocked"]:
                    self.trainer.progress["positions_unlocked"].append(next_pos)
                    self.console_print(f"\nCongratulations! You've unlocked {self.trainer.scale_positions[next_pos].name}!")
                
                # Update BPM if not at target
                if bpm < self.trainer.progress["target_bpm"]:
                    new_bpm = min(bpm + 5, self.trainer.progress["target_bpm"])
                    self.trainer.current_bpm = new_bpm
                    self.console_print(f"\nBPM increased to {new_bpm}")
            else:
                self.console_print("\nKeep practicing! You need 100% accuracy to progress.")
            
            self.trainer.save_progress()
    
    def enable_buttons(self):
        self.demo_button.configure(state="normal")
        self.practice_button.configure(state="normal")
    
    def after_practice(self):
        self.practice_button.configure(text="Start Practice")
        self.recording = False
        self.update_stats()
        self.fretboard.clear_notes()
        for note in self.current_position.notes:
            self.fretboard.highlight_note(note.string, note.fret)
            
    def update_status(self, status_text):   
         self.console_print(f"\n{status_text}")           

    def update_stats(self):

        # Display current stats
        stats = (
            f"Current BPM: {self.trainer.current_bpm}\n"
            f"Target BPM: {self.trainer.progress['target_bpm']}\n"
            f"Highest BPM: {self.trainer.progress['highest_bpm']}\n\n"
            f"Recent Achievements:\n"
        )
        
        for game in self.trainer.progress["games_won"][-5:]:
            stats += f"- {game}\n"
        
        stats += "\nAccuracy History:\n"
        for level, accuracies in self.trainer.progress["level_accuracies"].items():
            position, bpm = level.rsplit('_', 1)
            stats += f"\n{position} at {bpm} BPM:\n"
            stats += f"  Attempts: {len(accuracies)}\n"
            stats += f"  Best: {max(accuracies):.1f}%\n"
            stats += f"  Average: {sum(accuracies)/len(accuracies):.1f}%\n"
        
    def show_detailed_stats(self):
        self.console.delete('1.0', tk.END)
        self.console_print("=== Detailed Statistics ===\n")
        self.console_print(f"Current BPM: {self.trainer.current_bpm}")
        self.console_print(f"Target BPM: {self.trainer.progress['target_bpm']}")
        self.console_print(f"Highest BPM Achieved: {self.trainer.progress['highest_bpm']}")
        
        self.console_print("\nUnlocked Positions:")
        for pos in self.trainer.progress["positions_unlocked"]:
            self.console_print(f"- {self.trainer.scale_positions[pos].name}")
        
        self.console_print("\nRecent Achievements:")
        for game in self.trainer.progress["games_won"][-5:]:
            self.console_print(f"- {game}")
        
        self.console_print("\nAccuracy History:")
        for level, accuracies in self.trainer.progress["level_accuracies"].items():
            position, bpm = level.rsplit('_', 1)
            self.console_print(f"\n{position} at {bpm} BPM:")
            self.console_print(f"  Total Attempts: {len(accuracies)}")
            self.console_print(f"  Best Accuracy: {max(accuracies):.1f}%")
            self.console_print(f"  Average Accuracy: {sum(accuracies)/len(accuracies):.1f}%")
            self.console_print(f"  Recent Scores: {', '.join(f'{acc:.1f}%' for acc in accuracies[-5:])}")
            
if __name__ == "__main__":
    app = PentatonicGUI()
    app.mainloop()
