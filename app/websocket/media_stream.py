"""
Twilio Media Streams WebSocket handler.

This is the real-time backbone of a live call: Twilio streams the caller's
audio (mu-law, 8kHz, base64-encoded frames) to this endpoint, and expects
audio frames streamed back to play to the caller.

IMPLEMENTATION NOTES:
- audioop is used for mu-law <-> PCM transcoding (stdlib in Python 3.12, removed in 3.13)
- VAD uses simple RMS-based silence detection on PCM audio
- Buffer-then-transcribe approach (not streaming STT) for reliability
- No barge-in/interruption handling yet - caller audio is dropped while agent speaks
"""
import base64
import io
import json
import struct
import wave
from collections import deque

import audioop
from fastapi import WebSocket

from app.agents.conversation_orchestrator import ConversationOrchestrator
from app.database.session import AsyncSessionLocal
from app.models.agent import Agent
from app.models.call import Call, CallStatus
from app.speech.stt import transcribe_audio
from app.speech.tts import synthesize_speech_mulaw_stream
from app.utils.logger import logger

# Configuration
SILENCE_RMS_THRESHOLD = 500  # RMS threshold for silence detection (tune based on real calls)
SILENCE_FRAMES_THRESHOLD = 20  # Number of ~20ms frames of silence before considering speech ended
TWILIO_FRAME_SIZE = 160  # 20ms at 8kHz mu-law (160 bytes)


class AudioBuffer:
    """Buffers incoming audio frames with VAD to detect end-of-utterance."""
    
    def __init__(self, silence_threshold: int = SILENCE_RMS_THRESHOLD, 
                 silence_frames: int = SILENCE_FRAMES_THRESHOLD):
        self.silence_threshold = silence_threshold
        self.silence_frames = silence_frames
        self.buffer = bytearray()
        self.silence_count = 0
        self.has_speech = False
    
    def add_frame(self, mulaw_bytes: bytes) -> bool:
        """Add a mu-law frame. Returns True if end-of-utterance is detected."""
        # Transcode mu-law to PCM16 for VAD
        pcm_bytes = audioop.ulaw2lin(mulaw_bytes, 2)
        self.buffer.extend(pcm_bytes)
        
        # Calculate RMS of this frame
        rms = audioop.rms(pcm_bytes, 2)
        
        if rms < self.silence_threshold:
            self.silence_count += 1
        else:
            self.silence_count = 0
            self.has_speech = True
        
        # Detect end of utterance
        if (self.has_speech and 
            self.silence_count >= self.silence_frames and 
            len(self.buffer) > 0):
            return True
        
        return False
    
    def get_pcm(self) -> bytes:
        """Get buffered PCM16 audio and reset buffer."""
        result = bytes(self.buffer)
        self.buffer = bytearray()
        self.silence_count = 0
        self.has_speech = False
        return result
    
    def reset(self) -> None:
        """Clear buffer and reset state."""
        self.buffer = bytearray()
        self.silence_count = 0
        self.has_speech = False


async def stream_audio_to_twilio(websocket, mulaw_bytes: bytes) -> None:
    """Stream mu-law audio to Twilio in properly framed chunks."""
    # Split into 160-byte chunks (20ms at 8kHz)
    for i in range(0, len(mulaw_bytes), TWILIO_FRAME_SIZE):
        chunk = mulaw_bytes[i:i + TWILIO_FRAME_SIZE]
        if len(chunk) < TWILIO_FRAME_SIZE:
            # Pad last chunk if needed
            chunk = chunk + b'\x00' * (TWILIO_FRAME_SIZE - len(chunk))
        
        payload = base64.b64encode(chunk).decode('utf-8')
        message = {
            "event": "media",
            "streamSid": "dummy",  # Twilio provides this in start event
            "media": {"payload": payload}
        }
        await websocket.send_json(message)


def pcm_to_wav_bytes(pcm_bytes: bytes, sample_rate: int = 8000) -> bytes:
    """Convert raw PCM16 bytes to WAV format in memory."""
    wav_buffer = io.BytesIO()
    with wave.open(wav_buffer, 'wb') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit PCM
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(pcm_bytes)
    wav_buffer.seek(0)
    return wav_buffer.read()


async def handle_media_stream(websocket: WebSocket, call_id: str) -> None:
    await websocket.accept()
    logger.info(f"Media stream connected for call {call_id}")

    async with AsyncSessionLocal() as db:
        call = await db.get(Call, call_id)
        if call is None:
            logger.error(f"Media stream: call {call_id} not found, closing")
            await websocket.close()
            return

        agent = await db.get(Agent, call.agent_id)
        call.status = CallStatus.in_progress
        await db.commit()

        orchestrator = ConversationOrchestrator(db, agent, call_id)
        audio_buffer = AudioBuffer()
        is_agent_speaking = False

        try:
            while True:
                raw = await websocket.receive_text()
                event = json.loads(raw)
                event_type = event.get("event")

                if event_type == "start":
                    logger.info(f"Call {call_id}: Twilio stream started")
                    # Send greeting
                    greeting = await orchestrator.send_greeting()
                    logger.info(f"Call {call_id}: Sending greeting: {greeting[:50]}...")
                    mulaw_audio = synthesize_speech_mulaw_stream(greeting, agent.voice_id)
                    is_agent_speaking = True
                    await stream_audio_to_twilio(websocket, mulaw_audio)
                    is_agent_speaking = False

                elif event_type == "media":
                    # Drop caller audio while agent is speaking (no barge-in yet)
                    if is_agent_speaking:
                        continue
                    
                    payload = event.get("media", {}).get("payload")
                    if not payload:
                        continue
                    
                    # Decode base64 mu-law
                    mulaw_bytes = base64.b64decode(payload)
                    
                    # Add to buffer and check for end-of-utterance
                    if audio_buffer.add_frame(mulaw_bytes):
                        # End of utterance detected
                        pcm_audio = audio_buffer.get_pcm()
                        
                        if len(pcm_audio) > 1000:  # Minimum meaningful audio
                            # Convert to WAV for STT
                            wav_bytes = pcm_to_wav_bytes(pcm_audio)
                            
                            # Write to temp file for faster-whisper
                            import tempfile
                            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                                temp_file.write(wav_bytes)
                                temp_path = temp_file.name
                            
                            try:
                                # Transcribe
                                user_text = transcribe_audio(temp_path, language="en")
                                logger.info(f"Call {call_id}: Transcribed: {user_text[:100]}")
                                
                                if user_text.strip():
                                    # Get agent reply
                                    reply = await orchestrator.handle_user_utterance(user_text)
                                    logger.info(f"Call {call_id}: Agent reply: {reply[:100]}...")
                                    
                                    # Synthesize and stream reply
                                    mulaw_audio = synthesize_speech_mulaw_stream(reply, agent.voice_id)
                                    is_agent_speaking = True
                                    await stream_audio_to_twilio(websocket, mulaw_audio)
                                    is_agent_speaking = False
                            finally:
                                import os
                                if os.path.exists(temp_path):
                                    os.unlink(temp_path)
                        
                        audio_buffer.reset()

                elif event_type == "stop":
                    logger.info(f"Call {call_id}: Twilio stream stopped")
                    break

        except Exception as e:
            logger.error(f"Media stream error for call {call_id}: {e}", exc_info=True)
        finally:
            call.status = CallStatus.completed
            await db.commit()
            logger.info(f"Media stream ended for call {call_id}")
