"""Thin wrapper around the Gemini API for conversation generation,
summary generation, and structured-data extraction."""
import json

import google.generativeai as genai
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings
from app.utils.logger import logger

genai.configure(api_key=settings.gemini_api_key)

MODEL_NAME = "gemini-2.0-flash"


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
async def generate_reply(
    system_prompt: str,
    conversation_history: list[dict],
    latest_user_text: str,
    knowledge_context: str,
    temperature: float = 0.4,
) -> str:
    """Generates the next agent utterance, grounded only in retrieved knowledge context.

    conversation_history: prior turns as list of {"role": "user"|"model", "text": str},
    NOT including latest_user_text.
    """
    model = genai.GenerativeModel(
        model_name=MODEL_NAME,
        system_instruction=(
            f"{system_prompt}\n\n"
            "Relevant knowledge base context (answer ONLY from this; "
            "if the answer isn't here, say you will arrange a callback):\n"
            f"{knowledge_context or '(no relevant context found)'}"
        ),
        generation_config={"temperature": temperature},
    )

    chat = model.start_chat(history=[
        {"role": turn["role"], "parts": [turn["text"]]} for turn in conversation_history
    ])

    logger.debug(f"Gemini request | temp={temperature} | history_len={len(conversation_history)}")
    response = await chat.send_message_async(latest_user_text)
    logger.debug(f"Gemini response: {response.text[:200]}")
    return response.text.strip()


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
async def generate_summary(transcript: str) -> dict:
    """Generates a structured call summary: summary, lead_score, sentiment,
    important_notes, next_action. Returns parsed JSON."""
    model = genai.GenerativeModel(model_name=MODEL_NAME)
    prompt = (
        "Summarize the following call transcript. Return ONLY valid JSON with keys: "
        "summary (string), lead_score (0-100 number), sentiment (positive/neutral/negative), "
        "important_notes (string), next_action (string).\n\nTranscript:\n" + transcript
    )
    response = await model.generate_content_async(prompt)
    return _parse_json_response(response.text)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
async def extract_structured_info(transcript: str) -> dict:
    """Extracts structured lead information from a transcript. Returns ONLY JSON,
    per the extraction schema in the spec."""
    model = genai.GenerativeModel(model_name=MODEL_NAME)
    prompt = (
        "Extract the following fields from this call transcript as JSON only, "
        "no markdown, no commentary. Use null for anything not mentioned:\n"
        "name, age, gender, phone, address, city, state, interested_product, budget, "
        "lead_score (0-100), interest_level (high/medium/low), follow_up_required (boolean), "
        "next_follow_up_date (YYYY-MM-DD or null), reason.\n\nTranscript:\n" + transcript
    )
    response = await model.generate_content_async(prompt)
    return _parse_json_response(response.text)


def _parse_json_response(raw_text: str) -> dict:
    cleaned = raw_text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        logger.error(f"Failed to parse Gemini JSON response: {cleaned[:300]}")
        return {}
