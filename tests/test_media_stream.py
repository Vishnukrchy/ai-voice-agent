"""Synthetic tests for media stream VAD/buffering logic without real Twilio traffic."""
import audioop
import struct
import pytest

from app.websocket.media_stream import AudioBuffer, pcm_to_wav_bytes, TWILIO_FRAME_SIZE


def generate_silent_frame() -> bytes:
    """Generate a silent mu-law frame (160 bytes of silence)."""
    # Mu-law silence is 0xFF repeated
    return b'\xFF' * TWILIO_FRAME_SIZE


def generate_loud_frame() -> bytes:
    """Generate a loud mu-law frame (synthetic tone)."""
    # Generate PCM16 sine wave then convert to mu-law
    import math
    pcm_samples = []
    for i in range(TWILIO_FRAME_SIZE):
        # 1kHz sine wave at moderate amplitude
        sample = int(10000 * math.sin(2 * math.pi * 1000 * i / 8000))
        pcm_samples.append(struct.pack('<h', sample))
    pcm_bytes = b''.join(pcm_samples)
    return audioop.lin2ulaw(pcm_bytes, 2)


def test_audio_buffer_silence_only():
    """Test that silence-only input doesn't trigger end-of-utterance."""
    buffer = AudioBuffer(silence_threshold=500, silence_frames=3)
    
    # Add 10 silent frames
    for _ in range(10):
        result = buffer.add_frame(generate_silent_frame())
        assert result is False, "Silence should not trigger end-of-utterance without prior speech"
    
    # Buffer should be empty or minimal
    pcm = buffer.get_pcm()
    assert len(pcm) < 1000, "Silence should not accumulate significant audio"


def test_audio_buffer_speech_then_silence():
    """Test that speech followed by silence triggers end-of-utterance."""
    buffer = AudioBuffer(silence_threshold=500, silence_frames=3)
    
    # Add 5 loud frames (speech)
    for _ in range(5):
        result = buffer.add_frame(generate_loud_frame())
        assert result is False, "Speech should not trigger end-of-utterance"
    
    # Add 4 silent frames (should trigger at frame 3)
    for i in range(4):
        result = buffer.add_frame(generate_silent_frame())
        if i >= 2:  # Third silence frame
            assert result is True, f"Silence after speech should trigger end-of-utterance at frame {i}"
        else:
            assert result is False, f"Should not trigger before silence threshold at frame {i}"


def test_audio_buffer_mixed_speech():
    """Test that intermittent speech doesn't trigger end-of-utterance."""
    buffer = AudioBuffer(silence_threshold=500, silence_frames=5)
    
    # Pattern: speech, silence, speech, silence (not enough consecutive silence)
    for _ in range(3):
        buffer.add_frame(generate_loud_frame())
    for _ in range(2):
        buffer.add_frame(generate_silent_frame())
    for _ in range(3):
        buffer.add_frame(generate_loud_frame())
    for _ in range(2):
        result = buffer.add_frame(generate_silent_frame())
        assert result is False, "Intermittent silence should not trigger end-of-utterance"
    
    # Now add enough consecutive silence
    for _ in range(5):
        result = buffer.add_frame(generate_silent_frame())
        if result:
            break
    assert result is True, "Sufficient consecutive silence should trigger end-of-utterance"


def test_audio_buffer_reset():
    """Test that buffer reset clears state properly."""
    buffer = AudioBuffer(silence_threshold=500, silence_frames=3)
    
    # Add speech
    for _ in range(5):
        buffer.add_frame(generate_loud_frame())
    
    # Reset
    buffer.reset()
    
    # Should not have speech state
    assert buffer.has_speech is False
    assert buffer.silence_count == 0
    assert len(buffer.buffer) == 0
    
    # Adding silence should not trigger
    for _ in range(5):
        result = buffer.add_frame(generate_silent_frame())
        assert result is False


def test_pcm_to_wav_conversion():
    """Test PCM to WAV byte conversion."""
    # Generate some PCM16 audio
    import struct
    pcm_samples = []
    for i in range(100):
        sample = int(5000 * (i % 10) / 10)  # Simple ramp
        pcm_samples.append(struct.pack('<h', sample))
    pcm_bytes = b''.join(pcm_samples)
    
    # Convert to WAV
    wav_bytes = pcm_to_wav_bytes(pcm_bytes, sample_rate=8000)
    
    # Verify WAV header
    assert wav_bytes[:4] == b'RIFF', "WAV should start with RIFF header"
    assert wav_bytes[8:12] == b'WAVE', "WAV should have WAVE format"
    
    # Verify data is larger than PCM (header overhead)
    assert len(wav_bytes) > len(pcm_bytes), "WAV should be larger due to header"


def test_twilio_frame_size():
    """Verify Twilio frame size is correct for 20ms at 8kHz mu-law."""
    # 8kHz = 8000 samples per second
    # 20ms = 0.02 seconds
    # 8000 * 0.02 = 160 samples
    # mu-law = 1 byte per sample
    # So 160 bytes per frame
    assert TWILIO_FRAME_SIZE == 160, "Frame size should be 160 bytes for 20ms at 8kHz mu-law"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
