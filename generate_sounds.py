#!/usr/bin/env python3
"""
Generate Wizard of Wor sound effects and voice lines.
Creates 8-bit style, crunchy, Votrax-inspired audio assets.
"""

import os
import shutil
import struct
import subprocess
import wave

import numpy as np

SAMPLE_RATE = 22050  # Lower sample rate for retro feel
ASSETS_DIR = "assets/sounds"


def ensure_dir():
    os.makedirs(ASSETS_DIR, exist_ok=True)


def save_wav(filename, samples, sample_rate=SAMPLE_RATE):
    """Save samples as WAV file."""
    filepath = os.path.join(ASSETS_DIR, filename)

    # Normalize and convert to 16-bit
    samples = np.clip(samples, -1, 1)
    samples = (samples * 32767).astype(np.int16)

    with wave.open(filepath, "w") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(samples.tobytes())

    print(f"Created: {filepath}")


def bitcrush(samples, bits=6):
    """Reduce bit depth for crunchy retro sound."""
    levels = 2**bits
    return np.round(samples * levels) / levels


def add_noise(samples, amount=0.05):
    """Add subtle noise for texture."""
    noise = np.random.uniform(-amount, amount, len(samples))
    return samples + noise


# ============ SOUND EFFECTS ============


def generate_player_shot():
    """High-pitched laser 'pew' sound."""
    duration = 0.15
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration))

    # Frequency sweep from high to low
    freq_start = 1800
    freq_end = 400
    freq = np.linspace(freq_start, freq_end, len(t))

    # Generate tone with frequency sweep
    phase = np.cumsum(freq) / SAMPLE_RATE * 2 * np.pi
    wave = np.sin(phase)

    # Add harmonics for bite
    wave += 0.3 * np.sin(phase * 2)
    wave += 0.1 * np.sin(phase * 3)

    # Sharp attack, quick decay envelope
    envelope = np.exp(-t * 25)

    samples = wave * envelope * 0.7
    samples = bitcrush(samples, 5)

    save_wav("player_shot.wav", samples)


def generate_enemy_shot():
    """Heavier electrical crackle shot."""
    duration = 0.2
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration))

    # Lower frequency sweep
    freq_start = 800
    freq_end = 200
    freq = np.linspace(freq_start, freq_end, len(t))

    phase = np.cumsum(freq) / SAMPLE_RATE * 2 * np.pi
    wave = np.sin(phase)

    # Add square wave component for harshness
    wave += 0.4 * np.sign(np.sin(phase * 0.5))

    # Add crackle noise
    noise = np.random.uniform(-0.3, 0.3, len(t))
    noise_envelope = np.exp(-t * 15)
    wave += noise * noise_envelope

    envelope = np.exp(-t * 18)

    samples = wave * envelope * 0.6
    samples = bitcrush(samples, 4)

    save_wav("enemy_shot.wav", samples)


def generate_enemy_death():
    """Satisfying crunchy explosion."""
    duration = 0.4
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration))

    # White noise base
    noise = np.random.uniform(-1, 1, len(t))

    # Filter the noise with descending frequency
    # Simple lowpass simulation using cumsum
    filtered = np.zeros_like(noise)
    cutoff = np.linspace(0.3, 0.05, len(t))
    for i in range(1, len(noise)):
        filtered[i] = filtered[i - 1] * (1 - cutoff[i]) + noise[i] * cutoff[i]

    # Add tonal component (descending)
    freq = np.linspace(300, 50, len(t))
    phase = np.cumsum(freq) / SAMPLE_RATE * 2 * np.pi
    tone = np.sin(phase) * 0.5

    wave = filtered + tone

    # Punchy envelope
    envelope = np.exp(-t * 8) * (1 - np.exp(-t * 100))

    samples = wave * envelope * 0.8
    samples = bitcrush(samples, 4)

    save_wav("enemy_death.wav", samples)


def generate_player_death():
    """Long descending explosion tone."""
    duration = 1.2
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration))

    # Long descending frequency sweep
    freq = np.linspace(600, 30, len(t))
    phase = np.cumsum(freq) / SAMPLE_RATE * 2 * np.pi

    wave = np.sin(phase)
    wave += 0.5 * np.sin(phase * 2)  # Harmonics
    wave += 0.3 * np.sign(np.sin(phase * 0.5))  # Square wave grit

    # Add noise that fades in
    noise = np.random.uniform(-0.4, 0.4, len(t))
    noise_env = np.linspace(0, 1, len(t)) ** 2
    wave += noise * noise_env

    # Slow decay envelope with initial punch
    envelope = (1 - np.exp(-t * 50)) * np.exp(-t * 2.5)

    samples = wave * envelope * 0.7
    samples = bitcrush(samples, 4)

    save_wav("player_death.wav", samples)


def generate_walking_beat(bpm=120):
    """Background thrumming beat - creates a short loop."""
    beat_duration = 60.0 / bpm  # Duration of one beat
    duration = beat_duration * 4  # 4 beats per loop
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration))

    samples = np.zeros_like(t)

    # Create 4 beats
    for i in range(4):
        beat_start = int(i * beat_duration * SAMPLE_RATE)
        beat_len = int(0.1 * SAMPLE_RATE)  # Short thump

        if beat_start + beat_len > len(samples):
            break

        beat_t = np.linspace(0, 0.1, beat_len)

        # Low frequency thump
        freq = 60 if i % 2 == 0 else 50  # Alternate slightly
        beat = np.sin(2 * np.pi * freq * beat_t)
        beat += 0.3 * np.sin(2 * np.pi * freq * 2 * beat_t)

        # Quick decay
        beat_env = np.exp(-beat_t * 40)
        beat = beat * beat_env * 0.5

        samples[beat_start : beat_start + beat_len] += beat

    samples = bitcrush(samples, 5)
    save_wav("walking_beat.wav", samples)

    # Also create a faster version
    generate_walking_beat_fast()


def generate_walking_beat_fast():
    """Faster beat for tension."""
    bpm = 180
    beat_duration = 60.0 / bpm
    duration = beat_duration * 4
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration))

    samples = np.zeros_like(t)

    for i in range(4):
        beat_start = int(i * beat_duration * SAMPLE_RATE)
        beat_len = int(0.08 * SAMPLE_RATE)

        if beat_start + beat_len > len(samples):
            break

        beat_t = np.linspace(0, 0.08, beat_len)
        freq = 70 if i % 2 == 0 else 55
        beat = np.sin(2 * np.pi * freq * beat_t)
        beat_env = np.exp(-beat_t * 50)
        beat = beat * beat_env * 0.5

        samples[beat_start : beat_start + beat_len] += beat

    samples = bitcrush(samples, 5)
    save_wav("walking_beat_fast.wav", samples)


def generate_radar_blip():
    """High frequency radar ping."""
    duration = 0.05
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration))

    freq = 2400
    wave = np.sin(2 * np.pi * freq * t)
    wave += 0.3 * np.sin(2 * np.pi * freq * 1.5 * t)

    # Sharp envelope
    envelope = np.exp(-t * 80)

    samples = wave * envelope * 0.4
    samples = bitcrush(samples, 6)

    save_wav("radar_blip.wav", samples)


def generate_worluk_escape():
    """Sound when Worluk escapes through tunnel."""
    duration = 0.6
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration))

    # Ascending then descending whoosh
    freq = 200 + 800 * np.sin(np.pi * t / duration)
    phase = np.cumsum(freq) / SAMPLE_RATE * 2 * np.pi

    wave = np.sin(phase)
    wave += 0.2 * np.random.uniform(-1, 1, len(t))  # Noise

    # Fade in and out
    envelope = np.sin(np.pi * t / duration) ** 2

    samples = wave * envelope * 0.5
    samples = bitcrush(samples, 5)

    save_wav("worluk_escape.wav", samples)


def generate_wizard_teleport():
    """Magical teleport zap sound."""
    duration = 0.3
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration))

    # Multiple frequency sweeps
    freq1 = np.linspace(100, 2000, len(t))
    freq2 = np.linspace(2000, 100, len(t))

    phase1 = np.cumsum(freq1) / SAMPLE_RATE * 2 * np.pi
    phase2 = np.cumsum(freq2) / SAMPLE_RATE * 2 * np.pi

    wave = 0.5 * np.sin(phase1) + 0.5 * np.sin(phase2)
    wave += 0.2 * np.random.uniform(-1, 1, len(t))

    envelope = np.exp(-t * 8) * (1 - np.exp(-t * 100))

    samples = wave * envelope * 0.6
    samples = bitcrush(samples, 4)

    save_wav("wizard_teleport.wav", samples)


def generate_level_complete():
    """Victory jingle."""
    duration = 1.0
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration))

    samples = np.zeros_like(t)

    # Simple ascending arpeggio
    notes = [262, 330, 392, 523]  # C E G C
    note_duration = 0.2

    for i, freq in enumerate(notes):
        start = int(i * note_duration * SAMPLE_RATE)
        end = int((i + 1) * note_duration * SAMPLE_RATE)
        if end > len(t):
            end = len(t)

        note_t = t[start:end] - t[start]
        note = np.sin(2 * np.pi * freq * note_t)
        note += 0.3 * np.sin(2 * np.pi * freq * 2 * note_t)

        note_env = np.exp(-note_t * 5)
        samples[start:end] += note * note_env * 0.5

    samples = bitcrush(samples, 5)
    save_wav("level_complete.wav", samples)


def generate_game_over():
    """Sad game over sound."""
    duration = 1.5
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration))

    samples = np.zeros_like(t)

    # Descending notes
    notes = [392, 330, 262, 196]  # G E C low-C
    note_duration = 0.35

    for i, freq in enumerate(notes):
        start = int(i * note_duration * SAMPLE_RATE)
        end = int((i + 1.2) * note_duration * SAMPLE_RATE)
        if end > len(t):
            end = len(t)

        note_t = t[start:end] - t[start]
        note = np.sin(2 * np.pi * freq * note_t)
        note += 0.4 * np.sin(2 * np.pi * freq * 2 * note_t)

        note_env = np.exp(-note_t * 3)
        samples[start:end] += note * note_env * 0.5

    samples = bitcrush(samples, 4)
    save_wav("game_over.wav", samples)


# ============ VOICE SYNTHESIS (Votrax-style) ============


def generate_votrax_phoneme(phoneme_type, duration=0.1, base_freq=120):
    """Generate a basic Votrax-style phoneme."""
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration))

    if phoneme_type == "vowel":
        # Voiced vowel - buzzy fundamental with formants
        wave = np.zeros_like(t)
        # Fundamental buzz (pulse wave approximation)
        for harmonic in range(1, 15):
            amp = 1.0 / harmonic
            wave += amp * np.sin(2 * np.pi * base_freq * harmonic * t)
        wave = np.tanh(wave * 2)  # Soft clip for buzz

    elif phoneme_type == "fricative":
        # Unvoiced fricative - filtered noise
        wave = np.random.uniform(-1, 1, len(t))
        # Simple highpass by subtracting lowpassed version
        lp = np.zeros_like(wave)
        for i in range(1, len(wave)):
            lp[i] = lp[i - 1] * 0.7 + wave[i] * 0.3
        wave = wave - lp

    elif phoneme_type == "stop":
        # Plosive - short burst
        wave = np.random.uniform(-1, 1, len(t))
        env = np.exp(-t * 50)
        wave = wave * env

    elif phoneme_type == "nasal":
        # Nasal - low frequency buzz
        wave = np.zeros_like(t)
        for harmonic in range(1, 8):
            amp = 1.0 / (harmonic**1.5)
            wave += amp * np.sin(2 * np.pi * base_freq * 0.8 * harmonic * t)

    else:
        wave = np.zeros_like(t)

    return wave


def synthesize_robot_speech(text, filename):
    """
    Create robotic Votrax-style speech.
    This is a simplified phoneme-based synthesis.
    """
    # Phoneme mappings (simplified)
    phoneme_map = {
        "a": ("vowel", 0.12, 130),
        "e": ("vowel", 0.1, 140),
        "i": ("vowel", 0.1, 150),
        "o": ("vowel", 0.12, 120),
        "u": ("vowel", 0.1, 110),
        "y": ("vowel", 0.08, 145),
        "w": ("vowel", 0.08, 100),
        "s": ("fricative", 0.12, 0),
        "f": ("fricative", 0.1, 0),
        "h": ("fricative", 0.08, 0),
        "z": ("fricative", 0.1, 0),
        "p": ("stop", 0.06, 0),
        "b": ("stop", 0.06, 0),
        "t": ("stop", 0.05, 0),
        "d": ("stop", 0.05, 0),
        "k": ("stop", 0.06, 0),
        "g": ("stop", 0.06, 0),
        "m": ("nasal", 0.1, 100),
        "n": ("nasal", 0.08, 120),
        "r": ("vowel", 0.08, 110),
        "l": ("vowel", 0.08, 115),
        " ": ("silence", 0.1, 0),
        ".": ("silence", 0.2, 0),
        "!": ("silence", 0.15, 0),
    }

    samples_list = []
    text = text.lower()

    for char in text:
        if char in phoneme_map:
            ptype, dur, freq = phoneme_map[char]
            if ptype == "silence":
                samples_list.append(np.zeros(int(SAMPLE_RATE * dur)))
            else:
                phoneme = generate_votrax_phoneme(ptype, dur, freq)
                # Add envelope
                t = np.linspace(0, dur, len(phoneme))
                env = (1 - np.exp(-t * 30)) * np.exp(-t * 3)
                samples_list.append(phoneme * env)
        else:
            # Unknown character - small pause
            samples_list.append(np.zeros(int(SAMPLE_RATE * 0.02)))

    if not samples_list:
        return

    samples = np.concatenate(samples_list)

    # Apply overall robotic processing
    # Add ring modulation for robotic effect
    t = np.linspace(0, len(samples) / SAMPLE_RATE, len(samples))
    ring_mod = 0.5 + 0.5 * np.sin(2 * np.pi * 50 * t)
    samples = samples * ring_mod

    # Bitcrush for that 80s chip sound
    samples = bitcrush(samples, 4)

    # Normalize
    samples = samples / (np.max(np.abs(samples)) + 0.001) * 0.7

    save_wav(filename, samples)


def generate_robot_laugh():
    """Robotic 'ha ha ha ha' laughter."""
    duration = 1.2
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration))

    samples = np.zeros_like(t)

    # 4-5 'ha' sounds
    ha_times = [0, 0.22, 0.44, 0.66, 0.88]

    for start_time in ha_times:
        start = int(start_time * SAMPLE_RATE)
        ha_dur = 0.15
        ha_len = int(ha_dur * SAMPLE_RATE)

        if start + ha_len > len(samples):
            break

        ha_t = np.linspace(0, ha_dur, ha_len)

        # Buzzy 'ah' sound with pitch variation
        base_freq = 150 - start_time * 30  # Descending pitch
        ha = np.zeros(ha_len)
        for h in range(1, 12):
            ha += (1.0 / h) * np.sin(2 * np.pi * base_freq * h * ha_t)

        # Sharp attack, quick decay
        ha_env = (1 - np.exp(-ha_t * 80)) * np.exp(-ha_t * 15)
        ha = np.tanh(ha * 2) * ha_env

        samples[start : start + ha_len] += ha * 0.6

    # Ring modulation for robotic effect
    ring = 0.5 + 0.5 * np.sin(2 * np.pi * 45 * t)
    samples = samples * ring

    samples = bitcrush(samples, 4)
    save_wav("laugh.wav", samples)


# ============ MAIN ============


def main():
    print("Generating Wizard of Wor sound assets...")
    print("=" * 50)

    ensure_dir()

    # Sound Effects
    print("\n[Sound Effects]")
    generate_player_shot()
    generate_enemy_shot()
    generate_enemy_death()
    generate_player_death()
    generate_walking_beat()
    generate_radar_blip()
    generate_worluk_escape()
    generate_wizard_teleport()
    generate_level_complete()
    generate_game_over()

    # Voice Lines
    print("\n[Voice Lines - Votrax Style]")
    synthesize_robot_speech("i am the wizard of wor", "voice_wizard.wav")
    synthesize_robot_speech("welcome to my dungeon", "voice_welcome.wav")
    synthesize_robot_speech("prepare to die", "voice_prepare.wav")
    synthesize_robot_speech("insert coin", "voice_insert_coin.wav")
    synthesize_robot_speech("game over", "voice_game_over.wav")
    generate_robot_laugh()

    print("\n" + "=" * 50)
    print(f"All sounds generated in {ASSETS_DIR}/")
    print("\nTo use in game, add pygame.mixer.init() and load sounds.")


if __name__ == "__main__":
    main()
    main()
    main()
    main()
