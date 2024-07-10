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


def play_rest_end_melody():
    try:
        logging.debug("Attempting to play rest end melody.")
        # Create an inspiring melody with a sequence of notes
        durations = [400, 400, 400, 600, 400, 400, 400]  # Durations in milliseconds
        notes = [
            Sine(261),  # C4
            Sine(329),  # E4
            Sine(392),  # G4
            Sine(523),  # C5
            Sine(659),  # E5
            Sine(784),  # G5
            Sine(1046),  # C6
        ]

        # Initial and final volumes as a percentage
        initial_volume = 0.2
        final_volume = 0.6

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
        play_obj = sa.play_buffer(
            melody.raw_data,
            num_channels=1,
            bytes_per_sample=2,
            sample_rate=melody.frame_rate,
        )
        play_obj.wait_done()  # Wait for the melody to finish playing
        logging.debug("Rest end melody finished playing.")
    except Exception as e:
        logging.error("Error occurred while attempting to play rest end melody: %s", e)
