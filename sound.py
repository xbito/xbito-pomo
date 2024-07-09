from pydub.generators import Sine


import logging
import os
import tempfile
import winsound
from math import log10


def play_celebratory_melody():
    try:
        logging.debug("Attempting to play melody.")
        # Create a celebratory melody with a sequence of notes
        durations = [250, 250, 300, 200, 250, 300, 450]  # Durations in milliseconds
        notes = [
            Sine(523),  # C5
            Sine(587),  # D5
            Sine(659),  # E5
            Sine(784),  # G5
            Sine(880),  # A5
            Sine(988),  # B5
            Sine(1046),  # C6
        ]

        # Initial and final volumes as a percentage
        initial_volume = 0.1
        final_volume = 0.5

        # Calculate the volume increase per note
        volume_step = (final_volume - initial_volume) / (len(notes) - 1)
        segments = []

        for i, note in enumerate(notes):
            volume = initial_volume + i * volume_step
            segment = note.to_audio_segment(duration=durations[i]).apply_gain(
                20 * log10(volume)
            )
            segments.append(segment)

        melody = sum(segments)
        # Save the generated melody to a temporary WAV file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmpfile:
            melody.export(tmpfile.name, format="wav")
            # Play the WAV file
            winsound.PlaySound(tmpfile.name, winsound.SND_FILENAME)
            logging.debug("Melody finished playing.")
        # Clean up the temporary file
        os.remove(tmpfile.name)
    except Exception as e:
        logging.error("Error occurred while attempting to play melody: %s", e)
