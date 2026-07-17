"""
Twilio Media Streams WebSocket handler.

This is the real-time backbone of a live call: Twilio streams the caller's
audio (mu-law, 8kHz, base64-encoded frames) to this endpoint, and expects
audio frames streamed back to play to the caller.

STATUS: This module wires up the connection lifecycle and message routing
correctly, but the audio buffering/VAD (voice-activity detection to know
when the caller stopped talking), mu-law <-> PCM transcoding, and streaming
playback of TTS output back to Twilio are intentionally left as the next
implementation milestone — that inner loop is the highest-complexity,
highest-risk part of this system and deserves its own focused pass with
real call testing rather than being guessed at here.

Next steps (in order):
  1. Buffer inbound 'media' frames per call, run VAD to detect end-of-utterance
  2. Decode mu-law -> PCM16, write to a temp wav, call speech.stt.transcribe_audio
  3. Feed transcript into ConversationOrchestrator.handle_user_utterance
  4. Synthesize reply via speech.tts.synthesize_speech, transcode to mu-law 8k
  5. Stream 'media' frames back to Twilio in ~20ms chunks (base64 mu-law)
"""
import json

from fastapi import WebSocket, WebSocketDisconnect

from app.database.session import AsyncSessionLocal
from app.models.agent import Agent
from app.models.call import Call, CallStatus
from app.utils.logger import logger


async def handle_media_stream(websocket: WebSocket, call_id: str) -> None:
    await websocket.accept()
    logger.info(f"Media stream connected for call {call_id}")

    async with AsyncSessionLocal() as db:
        call = await db.get(Call, call_id)
        if call is None:
            logger.error(f"Media stream: call {call_id} not found, closing")
            await websocket.close()
            return

        agent = await db.get(Agent, call.agent_id)  # noqa: F841 - reserved for orchestrator wiring (see module docstring)
        call.status = CallStatus.in_progress
        await db.commit()

        try:
            while True:
                raw = await websocket.receive_text()
                event = json.loads(raw)
                event_type = event.get("event")

                if event_type == "start":
                    logger.info(f"Call {call_id}: Twilio stream started")
                    # TODO: send greeting via TTS -> stream back as first 'media' frames

                elif event_type == "media":
                    # TODO: buffer event["media"]["payload"] (base64 mu-law audio)
                    # and run VAD/STT pipeline per the module docstring above
                    pass

                elif event_type == "stop":
                    logger.info(f"Call {call_id}: Twilio stream stopped")
                    break

        except WebSocketDisconnect:
            logger.info(f"Media stream disconnected for call {call_id}")
        finally:
            call.status = CallStatus.completed
            await db.commit()
