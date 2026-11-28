"""Zentrix AI API. Run: uvicorn main:app --reload"""
import asyncio
import base64
import functools
import math
import os
import re
import tempfile
import urllib.request
import urllib.error
import json
import random
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import sympy as sp
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from starlette.middleware.gzip import GZipMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load the project-root .env before importing the math engine.
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

import engine as E
from research_engine import analyze_scalar_field, analyze_vector_field
from billing import router as billing_router

app = FastAPI(title='Zentrix AI', version='4.1.1', description='Mathematics Without Limits — created by M.Ayaan Chaudhry')
app.add_middleware(GZipMiddleware, minimum_size=1200)


def _public_mode() -> bool:
    return os.getenv("ZENTRIX_PUBLIC_MODE", "false").strip().lower() in {"1", "true", "yes"}


@app.get("/api/public-config")
def public_config():
    """Expose only browser-safe Supabase and Paddle client configuration; never server secrets."""
    return {
        "public_mode": _public_mode(),
        "supabase_url": os.getenv("SUPABASE_URL", "").rstrip("/"),
        "supabase_anon_key": os.getenv("SUPABASE_ANON_KEY", ""),
        "auth_enabled": bool(os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_ANON_KEY")),
        "paddle_client_token": os.getenv("PADDLE_CLIENT_TOKEN", ""),
        "paddle_environment": "sandbox" if os.getenv("PADDLE_ENVIRONMENT", "sandbox").strip().lower() == "sandbox" else "production",
    }


@app.middleware('http')
async def harden_local_responses(request: Request, call_next):
    # Bound API payloads before JSON parsing; the app is designed for local use.
    length = request.headers.get('content-length')
    if request.url.path.startswith('/api/') and length:
        try:
            if int(length) > 1_500_000:
                return __import__('starlette.responses', fromlist=['JSONResponse']).JSONResponse(
                    {'detail': 'Request is too large. Keep API requests below 1.5 MB.'}, status_code=413)
        except ValueError:
            return __import__('starlette.responses', fromlist=['JSONResponse']).JSONResponse(
                {'detail': 'Invalid request size.'}, status_code=400)
    response = await call_next(request)
    response.headers.setdefault('X-Content-Type-Options', 'nosniff')
    response.headers.setdefault('Referrer-Policy', 'same-origin')
    response.headers.setdefault('X-Frame-Options', 'SAMEORIGIN')
    response.headers.setdefault('Permissions-Policy', 'camera=(), microphone=(), geolocation=()')
    if request.url.path.startswith('/api/'):
        response.headers['Cache-Control'] = 'no-store'
    return response


@functools.lru_cache(maxsize=384)
def cached(question: str):
    return E.solve(question)


# SymPy workloads are CPU-bound. A small queue prevents repeated expensive inputs
# from overwhelming an 8 GB laptop when several browser requests arrive together.
_solver_slots = asyncio.Semaphore(2)
_solver_pool = ThreadPoolExecutor(max_workers=2, thread_name_prefix='zentrix-math')


async def _run_solver(question: str):
    async with _solver_slots:
        loop = asyncio.get_running_loop()
        work = loop.run_in_executor(_solver_pool, cached, question)
        return await asyncio.wait_for(work, 25)






class TutorRequest(BaseModel):
    topic: str = Field(min_length=1, max_length=50)
    question: str = Field(default='', max_length=700)


TUTOR_LESSONS = {
    'algebra': 'Algebra uses symbols to represent unknown values. Start by keeping both sides of an equation balanced: whatever operation you apply to one side, apply to the other. To solve ax+b=c, subtract b, then divide by a (provided a is not zero). Check your result by substitution.',
    'calculus': 'Calculus studies change and accumulation. Differentiation finds an instantaneous rate of change; integration accumulates quantities and can reverse differentiation. For powers, the power rule is d(x^n)/dx = n·x^(n−1). Always apply domain and constant rules carefully.',
    'geometry': 'Geometry studies shapes, sizes and spatial relationships. Sketch the figure, label known lengths and angles, identify the relevant theorem or formula, then substitute values with consistent units. For a triangle, area = one half × base × perpendicular height.',
    'trigonometry': 'Trigonometry connects angles and side lengths. In a right triangle, sin θ = opposite/hypotenuse, cos θ = adjacent/hypotenuse and tan θ = opposite/adjacent. Check whether your calculator is in degrees or radians before evaluating.',
    'statistics': 'Statistics describes and interprets data. The mean is the sum divided by the number of observations; the median is the middle value after sorting; the mode is the most frequent value. Keep repeated observations when calculating these measures.',
    'probability': 'Probability measures how likely an event is, from 0 to 1. For equally likely outcomes, P(event) = favourable outcomes / total outcomes. For complements, P(not A) = 1 − P(A). Make sure outcomes are equally likely before using the simple ratio.',
    'matrices': 'A matrix is a rectangular array of values. Matrix addition requires equal dimensions. For a 2×2 matrix [[a,b],[c,d]], the determinant is ad−bc. A matrix is invertible only when its determinant is nonzero.',
    'arithmetic': 'Arithmetic works with numbers and operations. Follow order of operations: brackets, powers, multiplication/division, then addition/subtraction. Keep track of negative signs and use estimation to check whether an answer is reasonable.',
    'physics': 'Physics uses mathematical models to describe the physical world. Identify the known quantities, choose a formula with consistent SI units, rearrange it before substituting, and state the final unit. For constant mass, Newton’s second law is F = ma.'
}


TUTOR_EXAMPLES = {
    'algebra': 'Solve 2x + 3 = 11: subtract 3 to get 2x = 8, then divide by 2 to get x = 4. Substitute 4 back into the original equation: 2(4) + 3 = 11.',
    'calculus': 'For f(x) = x^3, the power rule gives f\u2032(x) = 3x^2. At x = 2, the slope is 12.',
    'geometry': 'A triangle with base 8 cm and perpendicular height 5 cm has area (1/2)(8)(5) = 20 cm^2.',
    'trigonometry': 'In a right triangle, if the opposite side is 3 and the hypotenuse is 5, then sin(theta) = 3/5. Check whether the angle is being measured in degrees or radians.',
    'statistics': 'For data 2, 4, 4, 8, the mean is 18/4 = 4.5, the median is 4, and the mode is 4.',
    'probability': 'A fair six-sided die has one favourable outcome for rolling a 4, so P(4) = 1/6.',
    'matrices': 'For A = [[1,2],[3,4]], det(A) = 1*4 - 2*3 = -2, so A is invertible.',
    'arithmetic': 'Evaluate 8 + 4*3 by multiplying first: 8 + 12 = 20.',
    'physics': 'For a 2 kg object accelerating at 3 m/s^2, Newton\u2019s second law gives F = ma = 6 N.'
}
TUTOR_MISTAKES = {
    'algebra': 'Changing only one side of an equation. Apply the same operation to both sides and check by substitution.',
    'calculus': 'Forgetting the chain rule or the constant of integration. State the variable and include +C for indefinite integrals.',
    'geometry': 'Using a slanted side instead of the perpendicular height in a triangle-area calculation. Keep units consistent.',
    'trigonometry': 'Mixing up opposite, adjacent and hypotenuse, or confusing degree mode with radians.',
    'statistics': 'Dropping repeated values when finding the mean, median or mode. Sort the complete data set first.',
    'probability': 'Assuming outcomes are equally likely when they are not. Check the sample space before using a simple ratio.',
    'matrices': 'Multiplying matrices in the wrong order or assuming AB = BA. Check dimensions before multiplying.',
    'arithmetic': 'Performing addition before multiplication when there are no grouping brackets. Follow order of operations.',
    'physics': 'Substituting values before checking units. Convert to consistent SI units and state the final unit.'
}
TUTOR_PRACTICE = {
    'algebra': 'Try solving 3x - 4 = 11.',
    'calculus': 'Differentiate f(x) = 5x^4.',
    'geometry': 'Find the area of a triangle with base 10 cm and height 6 cm.',
    'trigonometry': 'In a right triangle, the opposite side is 5 and hypotenuse is 13. Find sin(theta).',
    'statistics': 'Find the mean and median of 3, 5, 5, 7, 10.',
    'probability': 'A fair coin is tossed twice. What is the probability of two heads?',
    'matrices': 'Find the determinant of [[2,1],[5,3]].',
    'arithmetic': 'Evaluate 18 - 2*(3 + 4).',
    'physics': 'Find the force on a 4 kg object accelerating at 2 m/s^2.'
}


def _tutor_ai_answer(provider: str, prompt: str) -> str:
    """Call one already-connected provider; never stores prompts or responses."""
    cfg = AI_PROVIDER_CONFIG[provider]
    key = os.getenv(cfg['key_env'])
    if not key:
        raise RuntimeError('provider is not connected')
    model = os.getenv(cfg['model_env'], cfg['default_model']).strip()
    if not re.fullmatch(r'[A-Za-z0-9._:/-]{2,120}', model):
        raise RuntimeError('configured model identifier is invalid')
    if provider == 'gemini':
        url = f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent'
        body = {'contents':[{'role':'user','parts':[{'text':prompt}]}],
                'generationConfig':{'temperature':0.2,'maxOutputTokens':1200}}
        headers = {'x-goog-api-key':key,'content-type':'application/json'}
    elif provider == 'anthropic':
        url = 'https://api.anthropic.com/v1/messages'
        body = {'model':model,'max_tokens':1200,'temperature':0.2,
                'messages':[{'role':'user','content':prompt}]}
        headers = {'x-api-key':key,'anthropic-version':'2023-06-01','content-type':'application/json'}
    else:
        url = 'https://api.openai.com/v1/chat/completions' if provider == 'openai' else 'https://openrouter.ai/api/v1/chat/completions'
        body = {'model':model,'messages':[{'role':'user','content':prompt}],
                'max_tokens':1200,'temperature':0.2}
        headers = {'Authorization':'Bearer '+key,'content-type':'application/json'}
        if provider == 'openrouter':
            headers['X-Title'] = 'ZENTRIX AI'
    request = urllib.request.Request(url,data=json.dumps(body).encode('utf-8'),headers=headers,method='POST')
    try:
        with urllib.request.urlopen(request,timeout=16) as response:
            data = json.load(response)
    except urllib.error.HTTPError as exc:
        if exc.code in (401,403):
            raise RuntimeError('provider rejected the saved API key') from None
        if exc.code == 429:
            raise RuntimeError('provider quota or rate limit reached') from None
        if exc.code == 404:
            raise RuntimeError('configured model was not found') from None
        raise RuntimeError(f'provider request failed (HTTP {exc.code})') from None
    except Exception as exc:
        raise RuntimeError(f'provider connection failed ({type(exc).__name__})') from None
    if provider == 'gemini':
        parts = (data.get('candidates') or [{}])[0].get('content',{}).get('parts',[])
        answer = '\n'.join(part.get('text','') for part in parts if isinstance(part,dict))
    elif provider == 'anthropic':
        answer = '\n'.join(part.get('text','') for part in data.get('content',[]) if isinstance(part,dict))
    else:
        choices = data.get('choices') or []
        content = choices[0].get('message',{}).get('content','') if choices else ''
        answer = '\n'.join(part.get('text','') for part in content if isinstance(part,dict)) if isinstance(content,list) else content
    answer = (answer or '').strip()
    if not answer:
        raise RuntimeError('provider returned an empty explanation')
    return answer


def _offline_tutor(topic: str, lesson: str, question: str) -> str:
    example = TUTOR_EXAMPLES.get(topic, 'Identify the known values, select a relevant definition, and work through one operation at a time.')
    mistake = TUTOR_MISTAKES.get(topic, 'Skipping definitions and assumptions. Write down what is known and check the final result.')
    practice = TUTOR_PRACTICE.get(topic, 'Create a small example, solve it carefully, and verify the result.')
    parts = ['CONCEPT\n' + lesson, 'WORKED EXAMPLE\n' + example,
             'COMMON MISTAKE\n' + mistake, 'TRY THIS\n' + practice]
    if question:
        parts.append('YOUR QUESTION\n' + question + '\nApproach: identify the requested quantity, list the known information, choose the relevant rule, show each algebraic step, and check the result. Use Solver for exact computation and verification.')
    return '\n\n'.join(parts)


@app.post('/api/tutor/explain')
def tutor_explain(request_data: TutorRequest):
    topic = request_data.topic.strip().lower()
    lesson = TUTOR_LESSONS.get(topic, 'Break the problem into smaller steps. Identify what is known, what is unknown, and which definition or formula connects them. Work symbolically first, substitute values carefully, then check the result.')
    question = request_data.question.strip()
    prompt = (
        'You are the ZENTRIX mathematics tutor. Teach the student, do not merely give a final answer. '
        'Explain the underlying concept, show a clear sequence of mathematical steps, include one worked example, '
        'identify a common misconception, and end with one short practice question. Adapt the depth to the topic. '
        'Keep notation readable. Never invent missing information, never claim a calculation is independently verified, '
        'and clearly state assumptions or uncertainty. If the student asks a specific question, address it directly. '
        'Topic: ' + topic + '. Student question: ' + (question or 'Give me a clear lesson with an example.')
    )
    provider_errors = []
    if not _public_mode():
        for provider in ('gemini','openai','anthropic','openrouter'):
            if not os.getenv(AI_PROVIDER_CONFIG[provider]['key_env']):
                continue
            try:
                answer = _tutor_ai_answer(provider,prompt)
                return {'topic':topic,'mode':'optional AI tutor','provider':AI_PROVIDER_CONFIG[provider]['label'],
                        'explanation':answer,'verified_calculation':False,'stored':False,'provider_fallbacks':provider_errors}
            except Exception as exc:
                provider_errors.append(AI_PROVIDER_CONFIG[provider]['label'] + ': ' + str(exc))
    explanation = _offline_tutor(topic,lesson,question)
    return {'topic':topic,'mode':'offline tutor','provider':None,'explanation':explanation,
            'verified_calculation':False,'stored':False,
            'provider_fallbacks':provider_errors,
            'fallback_note':'Connected AI was unavailable; the free offline lesson is shown.' if provider_errors else None}


class ArcadeAttempt(BaseModel):
    subject: str = Field(min_length=1, max_length=40)
    difficulty: str = Field(min_length=1, max_length=20)
    game: str = Field(min_length=1, max_length=40)
    correct: bool
    seconds: int = Field(default=0, ge=0, le=86400)


@contextmanager
def _progress_db():
    db_path = Path(__file__).resolve().parent.parent / 'zentrix_progress.sqlite3'
    conn = sqlite3.connect(db_path, timeout=8)
    try:
        conn.execute('PRAGMA busy_timeout=8000')
        conn.execute('PRAGMA journal_mode=WAL')
        conn.execute('PRAGMA synchronous=NORMAL')
        conn.execute("CREATE TABLE IF NOT EXISTS arcade_attempts (id INTEGER PRIMARY KEY AUTOINCREMENT, subject TEXT NOT NULL, difficulty TEXT NOT NULL, game TEXT NOT NULL, correct INTEGER NOT NULL, seconds INTEGER NOT NULL, created_at TEXT NOT NULL)")
        conn.execute('CREATE INDEX IF NOT EXISTS idx_arcade_subject ON arcade_attempts(subject, created_at)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_arcade_created ON arcade_attempts(created_at)')
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


@app.post('/api/arcade/attempt')
def save_arcade_attempt(attempt: ArcadeAttempt):
    if _public_mode():
        return {'ok': True, 'saved': False, 'reason': 'Guest progress is stored in this browser; sign-in sync is handled by your account.'}
    with _progress_db() as conn:
        conn.execute('INSERT INTO arcade_attempts(subject,difficulty,game,correct,seconds,created_at) VALUES(?,?,?,?,?,?)', (attempt.subject, attempt.difficulty, attempt.game, int(attempt.correct), attempt.seconds, datetime.now(timezone.utc).isoformat()))
    return {'ok': True}


@app.get('/api/arcade/stats')
def arcade_stats():
    if _public_mode():
        return {'attempts': 0, 'correct': 0, 'accuracy': 0, 'subjects': []}
    with _progress_db() as conn:
        total, correct = conn.execute('SELECT COUNT(*), COALESCE(SUM(correct),0) FROM arcade_attempts').fetchone()
        rows = conn.execute('SELECT subject, COUNT(*), SUM(correct) FROM arcade_attempts GROUP BY subject ORDER BY subject').fetchall()
    return {'attempts': total, 'correct': correct, 'accuracy': round(correct * 100 / total) if total else 0, 'subjects': [{'subject': r[0], 'attempts': r[1], 'correct': r[2] or 0} for r in rows]}


@app.get('/api/learning/profile')
def learning_profile():
    if _public_mode():
        return {'total_attempts': 0, 'correct': 0, 'overall_accuracy': 0, 'subjects': [], 'recommended_focus': None, 'method_note': 'Guest progress is private to this browser. Sign in to enable account sync.'}
    with _progress_db() as conn:
        rows = conn.execute('SELECT subject, COUNT(*), COALESCE(SUM(correct),0), MAX(created_at) FROM arcade_attempts GROUP BY subject ORDER BY subject').fetchall()
        total, correct = conn.execute('SELECT COUNT(*), COALESCE(SUM(correct),0) FROM arcade_attempts').fetchone()
    subjects = []
    for name, attempts, hits, latest in rows:
        accuracy = hits / attempts if attempts else 0
        # A conservative evidence score: low sample counts never imply mastery.
        confidence = min(1.0, attempts / 20)
        mastery = round(100 * (accuracy * confidence + 0.5 * (1 - confidence)))
        subjects.append({'subject': name, 'attempts': attempts, 'accuracy': round(accuracy * 100), 'mastery_estimate': mastery, 'confidence': round(confidence * 100), 'last_attempt': latest})
    weak = sorted((x for x in subjects if x['attempts'] >= 3), key=lambda x: x['mastery_estimate'])
    return {'total_attempts': total, 'correct': correct, 'overall_accuracy': round(correct * 100 / total) if total else 0, 'subjects': subjects, 'recommended_focus': weak[0]['subject'] if weak else None, 'method_note': 'Estimates are based on Math Arcade attempts only; they are not a complete curriculum mastery or spaced-repetition model.'}


class Q(BaseModel):
    question: str = Field(min_length=1, max_length=2000)


class Plot(BaseModel):
    expr: str = Field(min_length=1, max_length=500)
    xmin: float = -10
    xmax: float = 10


class GeminiSettings(BaseModel):
    api_key: str = Field(min_length=20, max_length=300)


class PhotoVisionOcrRequest(BaseModel):
    mime_type: str = Field(pattern=r'^image/(jpeg|png|webp)$')
    image_base64: str = Field(min_length=16, max_length=1_300_000)
    provider: str = Field(default='gemini', pattern=r'^(gemini|openai|anthropic|openrouter)$')


class AIProviderSettings(BaseModel):
    provider: str = Field(pattern=r'^(gemini|openai|anthropic|openrouter)$')
    api_key: str = Field(min_length=20, max_length=500)
    model: str = Field(min_length=2, max_length=120)


class VerifyAnswer(BaseModel):
    expected: str = Field(min_length=1, max_length=1000)
    submitted: str = Field(min_length=1, max_length=1000)


class AuditSteps(BaseModel):
    steps: list[str] = Field(min_length=2, max_length=12)


class DiagnoseSteps(BaseModel):
    problem: str = Field(default='', max_length=500)
    steps: list[str] = Field(min_length=2, max_length=12)



def _validate_gemini_key(key: str):
    # Do not assume Google's key alphabet: accept printable ASCII tokens and
    # let Google's API perform the authoritative credential check.
    if not (20 <= len(key) <= 300) or not key.isascii() or any(
        ch.isspace() or ord(ch) < 33 or ord(ch) > 126 for ch in key
    ):
        raise HTTPException(400, 'The API key must be 20–300 printable characters with no spaces. Copy it directly from Google AI Studio.')
    return key


def _local_request_only(request: Request):
    host = (request.url.hostname or '').lower()
    if host not in {'127.0.0.1', 'localhost', '::1'}:
        raise HTTPException(403, 'Settings can only be changed from this computer.')
    origin = request.headers.get('origin')
    if origin:
        from urllib.parse import urlparse
        origin_host = (urlparse(origin).hostname or '').lower()
        if origin_host not in {'127.0.0.1', 'localhost', '::1'}:
            raise HTTPException(403, 'Cross-origin settings requests are not allowed.')


def _save_gemini_key(key: str):
    _validate_gemini_key(key)
    project_root = Path(__file__).resolve().parent.parent
    env_path = project_root / '.env'
    existing = env_path.read_text(encoding='utf-8') if env_path.exists() else ''
    lines = [line for line in existing.splitlines() if not line.strip().startswith('GEMINI_API_KEY=')]
    lines.append('GEMINI_API_KEY=' + key)
    content = '\n'.join(lines).strip() + '\n'
    fd, temp_name = tempfile.mkstemp(prefix='.zentrix-env-', dir=str(project_root), text=True)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as handle:
            handle.write(content)
        try:
            os.chmod(temp_name, 0o600)
        except OSError:
            pass
        os.replace(temp_name, env_path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)
    os.environ['GEMINI_API_KEY'] = key
    cached.cache_clear()


def _check_gemini_connection(key: str):
    model = os.getenv('GEMINI_MODEL', 'gemini-3.5-flash-lite').strip()
    if not re.fullmatch(r'[A-Za-z0-9._-]{1,100}', model):
        raise HTTPException(500, 'The configured Gemini model name is invalid.')
    payload = json.dumps({'contents': [{'role': 'user', 'parts': [{'text': 'Reply with exactly: OK'}]}], 'generationConfig': {'temperature': 0, 'maxOutputTokens': 5}}).encode('utf-8')
    req = urllib.request.Request(
        f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent',
        data=payload, headers={'x-goog-api-key': key, 'content-type': 'application/json'}, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=12) as response:
            data = json.load(response)
        if not data.get('candidates'):
            raise ValueError('empty response')
    except Exception as exc:
        # Do not return the provider body or the API key to the browser.
        kind = type(exc).__name__
        if isinstance(exc, urllib.error.HTTPError):
            if exc.code in (401, 403):
                raise HTTPException(400, 'Google rejected this API key. Check that it is active and has Gemini API access.') from None
            if exc.code == 404:
                raise HTTPException(400, 'The configured Gemini model was not found. Check GEMINI_MODEL in your project settings.') from None
            if exc.code == 429:
                raise HTTPException(429, 'Gemini rate limit reached. Try again later or check your free-tier quota.') from None
        raise HTTPException(502, f'Could not verify the Gemini connection ({kind}). Check your internet connection and try again.') from None
    return {'connected': True, 'provider': 'Google Gemini', 'model': model}


@app.post('/api/ocr/vision')
def read_photo_with_gemini(photo: PhotoVisionOcrRequest, request: Request):
    """Optional, user-initiated math-aware transcription. Images are never persisted."""
    if _public_mode():
        raise HTTPException(404, 'Server-wide AI key settings are disabled on the public website. Personal AI connections will be added separately.')
    _local_request_only(request)
    if photo.provider != 'gemini':
        return _read_photo_with_provider(photo, photo.provider)
    key = os.getenv('GEMINI_API_KEY')
    if not key:
        raise HTTPException(400, 'Connect Gemini in Settings before using AI math reading.')
    model = os.getenv('GEMINI_MODEL', 'gemini-3.5-flash-lite').strip()
    if not re.fullmatch(r'[A-Za-z0-9._-]{1,100}', model):
        raise HTTPException(500, 'The configured Gemini model name is invalid.')
    try:
        image_bytes = base64.b64decode(photo.image_base64, validate=True)
    except (ValueError, base64.binascii.Error):
        raise HTTPException(400, 'The selected image data is invalid.') from None
    if not image_bytes or len(image_bytes) > 975_000:
        raise HTTPException(413, 'The compressed image is too large. Choose a smaller crop and try again.')
    signatures = {
        'image/jpeg': image_bytes.startswith(b'\xff\xd8\xff'),
        'image/png': image_bytes.startswith(b'\x89PNG\r\n\x1a\n'),
        'image/webp': len(image_bytes) >= 12 and image_bytes[:4] == b'RIFF' and image_bytes[8:12] == b'WEBP',
    }
    if not signatures.get(photo.mime_type, False):
        raise HTTPException(400, 'The compressed image format does not match its declared type.')
    prompt = (
        'Transcribe the visible mathematics question exactly. Do NOT solve it, explain it, '
        'or invent missing information. Preserve the question wording and line order. '
        'Write powers with ^ (for example x^2), square roots as sqrt(...), fractions as '
        '(numerator)/(denominator), multiplication as *, and comparisons as <=, >= or !=. '
        'Keep variable names and all signs. For a symbol or number that cannot be read, write '
        '[unclear] rather than guessing. If a diagram is essential, add a short [Diagram: ...] '
        'description using only visible labels and relationships. Return only the transcription.'
    )
    payload = json.dumps({
        'contents': [{'role': 'user', 'parts': [
            {'text': prompt},
            {'inlineData': {'mimeType': photo.mime_type, 'data': photo.image_base64}},
        ]}],
        'generationConfig': {'maxOutputTokens': 1200},
    }).encode('utf-8')
    req = urllib.request.Request(
        f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent',
        data=payload,
        headers={'x-goog-api-key': key, 'content-type': 'application/json'},
        method='POST',
    )
    try:
        with urllib.request.urlopen(req, timeout=25) as response:
            data = json.load(response)
    except urllib.error.HTTPError as exc:
        if exc.code in (401, 403):
            raise HTTPException(400, 'Google rejected the Gemini key. Reconnect it in Settings.') from None
        if exc.code == 404:
            raise HTTPException(400, 'The configured Gemini model was not found. Check the model setting.') from None
        if exc.code == 429:
            raise HTTPException(429, 'Gemini free-tier or account quota is currently unavailable. Try later.') from None
        raise HTTPException(502, f'Gemini image transcription failed (HTTP {exc.code}).') from None
    except Exception as exc:
        raise HTTPException(502, f'Could not reach Gemini for image transcription ({type(exc).__name__}).') from None
    candidates = data.get('candidates') or []
    if not candidates:
        raise HTTPException(502, 'Gemini returned no transcription candidate. Try a clearer crop.')
    parts = candidates[0].get('content', {}).get('parts', [])
    transcription = '\n'.join(part.get('text', '') for part in parts if isinstance(part, dict)).strip()
    if not transcription:
        raise HTTPException(502, 'Gemini did not return a readable transcription. Try a clearer crop.')
    return {'transcription': transcription, 'model': model, 'sent_to_provider': True, 'stored': False}


@app.post('/api/settings/gemini')
def save_gemini_settings(settings: GeminiSettings, request: Request):
    if _public_mode():
        raise HTTPException(404, 'Server-wide AI key settings are disabled on the public website. Personal AI connections will be added separately.')
    _local_request_only(request)
    key = _validate_gemini_key(settings.api_key.strip())
    # Verify first; never persist a typo, revoked key, or key without API access.
    result = _check_gemini_connection(key)
    _save_gemini_key(key)
    return {'ok': True, **result, 'message': 'Gemini is connected. Your key is saved locally on this computer.'}


@app.delete('/api/settings/gemini')
def remove_gemini_settings(request: Request):
    if _public_mode():
        raise HTTPException(404, 'Server-wide AI key settings are disabled on the public website. Personal AI connections will be added separately.')
    _local_request_only(request)
    project_root = Path(__file__).resolve().parent.parent
    env_path = project_root / '.env'
    existing = env_path.read_text(encoding='utf-8') if env_path.exists() else ''
    lines = [line for line in existing.splitlines() if not line.strip().startswith('GEMINI_API_KEY=')]
    if lines:
        env_path.write_text('\n'.join(lines).rstrip() + '\n', encoding='utf-8')
    elif env_path.exists():
        env_path.unlink()
    os.environ.pop('GEMINI_API_KEY', None)
    cached.cache_clear()
    return {'ok': True, 'message': 'Gemini key removed from this computer.'}



AI_PROVIDER_CONFIG = {
    'gemini': {'key_env': 'GEMINI_API_KEY', 'model_env': 'GEMINI_MODEL', 'default_model': 'gemini-3.5-flash-lite', 'label': 'Google Gemini'},
    'openai': {'key_env': 'OPENAI_API_KEY', 'model_env': 'OPENAI_MODEL', 'default_model': 'gpt-4o-mini', 'label': 'OpenAI'},
    'anthropic': {'key_env': 'ANTHROPIC_API_KEY', 'model_env': 'ANTHROPIC_MODEL', 'default_model': 'claude-3-5-haiku-latest', 'label': 'Anthropic Claude'},
    'openrouter': {'key_env': 'OPENROUTER_API_KEY', 'model_env': 'OPENROUTER_MODEL', 'default_model': 'openai/gpt-4o-mini', 'label': 'OpenRouter'},
}


def _write_env_values(values: dict[str, str | None]):
    root = Path(__file__).resolve().parent.parent
    path = root / '.env'
    existing = path.read_text(encoding='utf-8') if path.exists() else ''
    lines = [line for line in existing.splitlines() if not any(line.strip().startswith(k + '=') for k in values)]
    for key, value in values.items():
        if value is not None:
            lines.append(key + '=' + value)
    content = '\n'.join(lines).strip() + ('\n' if lines else '')
    fd, temp_name = tempfile.mkstemp(prefix='.zentrix-env-', dir=str(root), text=True)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as handle:
            handle.write(content)
        try:
            os.chmod(temp_name, 0o600)
        except OSError:
            pass
        if content:
            os.replace(temp_name, path)
        elif path.exists():
            path.unlink()
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)
    for key, value in values.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value
    cached.cache_clear()


def _provider_status():
    return [{'id': pid, 'label': cfg['label'], 'connected': bool(os.getenv(cfg['key_env'])),
             'model': os.getenv(cfg['model_env'], cfg['default_model'])}
            for pid, cfg in AI_PROVIDER_CONFIG.items()]


@app.get('/api/settings/ai')
def get_ai_provider_settings(request: Request):
    if _public_mode():
        raise HTTPException(404, 'Server-wide AI key settings are disabled on the public website. Personal AI connections will be added separately.')
    _local_request_only(request)
    return {'providers': _provider_status()}


def _verify_provider_key(provider: str, key: str, model: str):
    if not (20 <= len(key) <= 500) or not key.isascii() or any(ch.isspace() or ord(ch) < 33 or ord(ch) > 126 for ch in key):
        raise HTTPException(400, 'API key must be 20–500 printable characters without spaces.')
    if not re.fullmatch(r'[A-Za-z0-9._:/-]{2,120}', model):
        raise HTTPException(400, 'Model ID contains unsupported characters.')
    if provider == 'gemini':
        old = os.environ.get('GEMINI_MODEL')
        os.environ['GEMINI_MODEL'] = model
        try:
            return _check_gemini_connection(key)
        finally:
            if old is None: os.environ.pop('GEMINI_MODEL', None)
            else: os.environ['GEMINI_MODEL'] = old
    if provider == 'openai':
        url, headers = 'https://api.openai.com/v1/models', {'Authorization': 'Bearer ' + key}
    elif provider == 'anthropic':
        url, headers = 'https://api.anthropic.com/v1/models', {'x-api-key': key, 'anthropic-version': '2023-06-01'}
    else:
        url, headers = 'https://openrouter.ai/api/v1/models', {'Authorization': 'Bearer ' + key}
    req = urllib.request.Request(url, headers=headers, method='GET')
    try:
        with urllib.request.urlopen(req, timeout=12) as response:
            data = json.load(response)
        if not isinstance(data, dict) or 'data' not in data:
            raise ValueError('unexpected provider response')
    except urllib.error.HTTPError as exc:
        if exc.code in (401, 403): raise HTTPException(400, 'The provider rejected this API key. Check that it is active and has API access.') from None
        if exc.code == 429: raise HTTPException(429, 'Provider rate limit reached. Try again later.') from None
        raise HTTPException(502, f'Provider verification failed (HTTP {exc.code}).') from None
    except Exception as exc:
        raise HTTPException(502, f'Could not verify provider connection ({type(exc).__name__}). Check your internet connection.') from None
    return {'connected': True, 'provider': AI_PROVIDER_CONFIG[provider]['label'], 'model': model}


@app.post('/api/settings/ai')
def connect_ai_provider(settings: AIProviderSettings, request: Request):
    if _public_mode():
        raise HTTPException(404, 'Server-wide AI key settings are disabled on the public website. Personal AI connections will be added separately.')
    _local_request_only(request)
    provider = settings.provider
    cfg = AI_PROVIDER_CONFIG[provider]
    key = settings.api_key.strip()
    model = settings.model.strip()
    result = _verify_provider_key(provider, key, model)
    _write_env_values({cfg['key_env']: key, cfg['model_env']: model})
    return {'ok': True, 'label': cfg['label'], 'message': cfg['label'] + ' connected. The key is stored locally on this computer.', **result}


@app.delete('/api/settings/ai/{provider}')
def disconnect_ai_provider(provider: str, request: Request):
    if _public_mode():
        raise HTTPException(404, 'Server-wide AI key settings are disabled on the public website. Personal AI connections will be added separately.')
    _local_request_only(request)
    if provider not in AI_PROVIDER_CONFIG:
        raise HTTPException(404, 'Unknown AI provider.')
    cfg = AI_PROVIDER_CONFIG[provider]
    _write_env_values({cfg['key_env']: None, cfg['model_env']: None})
    return {'ok': True, 'message': cfg['label'] + ' disconnected from this computer.'}


def _read_photo_with_provider(photo: PhotoVisionOcrRequest, provider: str):
    cfg = AI_PROVIDER_CONFIG[provider]
    key = os.getenv(cfg['key_env'])
    if not key:
        raise HTTPException(400, 'Connect ' + cfg['label'] + ' in Settings before using AI math reading.')
    model = os.getenv(cfg['model_env'], cfg['default_model'])
    try:
        image_bytes = base64.b64decode(photo.image_base64, validate=True)
    except (ValueError, base64.binascii.Error):
        raise HTTPException(400, 'The selected image data is invalid.') from None
    if not image_bytes or len(image_bytes) > 975_000:
        raise HTTPException(413, 'The compressed image is too large. Choose a smaller crop and try again.')
    signatures = {'image/jpeg': image_bytes.startswith(b'\xff\xd8\xff'), 'image/png': image_bytes.startswith(b'\x89PNG\r\n\x1a\n'), 'image/webp': len(image_bytes) >= 12 and image_bytes[:4] == b'RIFF' and image_bytes[8:12] == b'WEBP'}
    if not signatures.get(photo.mime_type, False):
        raise HTTPException(400, 'The compressed image format does not match its declared type.')
    prompt = ('Transcribe the visible mathematics question exactly. Do NOT solve or explain it. Preserve wording and line order. '
              'Use ^ for powers, sqrt(...) for roots, (a)/(b) for fractions, * for multiplication and <=, >=, != for comparisons. '
              'Keep every variable, sign and number. If unclear, write [unclear] rather than guessing. Return only the transcription.')
    b64 = photo.image_base64
    if provider in ('openai', 'openrouter'):
        url = 'https://api.openai.com/v1/chat/completions' if provider == 'openai' else 'https://openrouter.ai/api/v1/chat/completions'
        body = {'model': model, 'messages': [{'role': 'user', 'content': [{'type': 'text', 'text': prompt}, {'type': 'image_url', 'image_url': {'url': f'data:{photo.mime_type};base64,{b64}'}}]}], 'max_tokens': 1200, 'temperature': 0}
        headers = {'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json'}
        if provider == 'openrouter': headers['X-Title'] = 'ZENTRIX AI'
    else:
        url = 'https://api.anthropic.com/v1/messages'
        media_type = photo.mime_type
        body = {'model': model, 'max_tokens': 1200, 'temperature': 0, 'messages': [{'role': 'user', 'content': [{'type': 'text', 'text': prompt}, {'type': 'image', 'source': {'type': 'base64', 'media_type': media_type, 'data': b64}}]}]}
        headers = {'x-api-key': key, 'anthropic-version': '2023-06-01', 'Content-Type': 'application/json'}
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers=headers, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=35) as response: data = json.load(response)
    except urllib.error.HTTPError as exc:
        if exc.code in (401, 403): raise HTTPException(400, cfg['label'] + ' rejected the API key. Reconnect it in Settings.') from None
        if exc.code == 404: raise HTTPException(400, 'The selected model was not found. Check the model ID in Settings.') from None
        if exc.code == 429: raise HTTPException(429, cfg['label'] + ' rate limit or quota reached. Try again later.') from None
        raise HTTPException(502, cfg['label'] + ' image transcription failed (HTTP ' + str(exc.code) + ').') from None
    except Exception as exc:
        raise HTTPException(502, 'Could not reach ' + cfg['label'] + ' (' + type(exc).__name__ + '). Check your internet connection.') from None
    if provider in ('openai', 'openrouter'):
        choices = data.get('choices') or []
        content = choices[0].get('message', {}).get('content', '') if choices else ''
        if isinstance(content, list): transcription = '\n'.join(x.get('text', '') for x in content if isinstance(x, dict))
        else: transcription = content
    else:
        transcription = '\n'.join(x.get('text', '') for x in data.get('content', []) if isinstance(x, dict))
    transcription = (transcription or '').strip()
    if not transcription: raise HTTPException(502, cfg['label'] + ' returned no readable transcription. Try a clearer crop.')
    return {'transcription': transcription, 'model': model, 'provider': provider, 'sent_to_provider': True, 'stored': False}


@app.get('/api/health')
def health():
    return {
        'ok': True,
        'version': app.version,
        'math_engine': 'local',
        'online_ai_configured': (False if _public_mode() else any([os.getenv('GEMINI_API_KEY'), os.getenv('OPENAI_API_KEY'), os.getenv('ANTHROPIC_API_KEY'), os.getenv('OPENROUTER_API_KEY')])),
        'ai_provider': 'Google Gemini' if (not _public_mode() and os.getenv('GEMINI_API_KEY')) else None,
        'ai_model': os.getenv('GEMINI_MODEL', 'gemini-3.5-flash-lite') if (not _public_mode() and os.getenv('GEMINI_API_KEY')) else None,
        'paid_api_calls_enabled': False,
        'solver_cache': {'entries': cached.cache_info().currsize, 'capacity': cached.cache_info().maxsize},
        'runtime': 'local-optimized',
    }


@app.get('/api/diagnostics')
def diagnostics():
    info = cached.cache_info()
    return {'ok': True, 'solver_cache': {'hits': info.hits, 'misses': info.misses, 'entries': info.currsize, 'capacity': info.maxsize}, 'solver_concurrency_limit': 2, 'plot_samples': 640, 'database': 'SQLite WAL'}


@app.get('/api/capabilities')
def capabilities():
    return {
        'version': app.version,
        'domains': ['arithmetic', 'algebra', 'equations', 'systems', 'inequalities',
                    'calculus', 'partial_derivatives', 'taylor_series', 'summations',
                    'limits', 'ordinary_differential_equations', 'linear_algebra', 'number_theory',
                    'class10_complex_numbers', 'class10_quadratics', 'class10_matrices',
                    'class10_functions', 'class10_algebraic_fractions', 'class10_vectors',
                    'class10_trigonometry', 'class10_circle_calculations',
                    'class10_information_handling', 'class10_probability',
                    'geometry_mensuration', 'coordinate_geometry', 'grouped_statistics',
                    'combinatorics', 'unit_conversion', 'algebraic_identity_proof', 'guided_word_problem_models', 'ladder_right_triangle_word_problems', 'rectangle_area_perimeter_word_problems', 'photo_question_ocr_client_side', 'introductory_physics_numericals', 'local_practice_generator', 'symbolic_answer_verification', 'multivariable_calculus', 'vector_calculus', 'critical_point_classification', 'jacobian_divergence_curl'],
        'features': ['optional_gemini_vision_ocr', 'research_calculus_lab', 'symbolic_identity_verification', 'high_precision_evaluation', 'multi_pass_photo_ocr', 'printable_research_reports', 'adaptive_arcade_difficulty', 'local_learning_profile', 'step_by_step', 'symbolic_verification', 'mathematical_proof_auditor', 'misconception_detection', 'numerical_checks', '2d_plotting', 'geometry_calculations', 'grouped_statistics', 'combinatorics', 'unit_conversion', 'algebraic_identity_check', 'guided_word_problem_models', 'ladder_right_triangle_word_problems', 'rectangle_area_perimeter_word_problems', 'generated_geometry_diagrams', 'browser_based_photo_ocr', 'physics_formula_calculator', 'practice_quizzes', 'exact_answer_comparison', 'multivariable_research_workbench', 'symbolic_gradient_hessian', 'local_critical_point_diagnostics', 'vector_field_jacobian_divergence_curl'],
        'online_ai_required': False,
        'offline_math': True,
    }


@app.post('/api/solve')
async def solve(b: Q):
    q = b.question.strip()
    if not q:
        raise HTTPException(400, 'Enter a mathematical problem.')
    try:
        # Normalize harmless whitespace to improve cache hits without changing math syntax.
        q = re.sub(r'\s+', ' ', q).strip()
        return await asyncio.wait_for(_run_solver(q), 27)
    except (asyncio.TimeoutError, TimeoutError):
        raise HTTPException(504, 'Timed out: this problem is too difficult for the current solver limits. Try simplifying it or splitting it into smaller steps.')
    except Exception:
        raise HTTPException(400, 'The problem could not be processed safely. Check the expression and try again.')


@app.post('/api/verify')
def verify_answer(b: VerifyAnswer):
    """Compare two mathematical expressions using exact symbolic simplification."""
    try:
        expected, submitted = E.P(b.expected), E.P(b.submitted)
        if isinstance(expected, list) or isinstance(submitted, list):
            raise ValueError('Enter one expression at a time.')
        difference = sp.simplify(sp.together(expected - submitted))
        equivalent = difference == 0
        restrictions = []
        for label, expression in (('expected', expected), ('submitted', submitted)):
            denominator = sp.factor(sp.denom(sp.together(expression)))
            if denominator != 1:
                restrictions.append({'expression': label, 'denominator': sp.sstr(denominator),
                                     'condition': sp.sstr(sp.Ne(denominator, 0)),
                                     'condition_latex': sp.latex(sp.Ne(denominator, 0))})
        feedback = ('Correct on the common domain of both expressions.' if equivalent else
                    'Not equivalent. Recheck your algebra, signs, and simplification.')
        if equivalent and restrictions:
            feedback += ' Note the domain restrictions below; cancelled factors do not restore excluded inputs.'
        return {'correct': bool(equivalent), 'method': 'exact symbolic comparison',
                'feedback': feedback, 'difference': sp.latex(difference),
                'domain_restrictions': restrictions,
                'domain_note': 'Expressions are compared only on their common domain, where both sides are defined.'}
    except Exception:
        raise HTTPException(400, 'Could not compare these expressions. Enter a supported mathematical expression.')


@app.post('/api/audit')
def audit_steps(b: AuditSteps):
    """Audit adjacent algebraic transformations and identify the first invalid step."""
    lines = [line.strip() for line in b.steps]
    if any(not line or len(line) > 300 for line in lines):
        raise HTTPException(400, 'Each proof line must contain 1–300 characters.')
    def equation_residual(line):
        if line.count('=') > 1:
            raise ValueError('Use one equality sign per line.')
        if '=' in line:
            left, right = line.split('=', 1)
            return sp.together(E.P(left) - E.P(right))
        return sp.together(E.P(line))
    results=[]
    for i in range(1, len(lines)):
        try:
            prev, curr = equation_residual(lines[i-1]), equation_residual(lines[i])
            ratio = sp.simplify(prev/curr) if curr != 0 else None
            equivalent = sp.simplify(prev-curr) == 0 or (ratio is not None and not ratio.free_symbols and ratio.is_finite and ratio != 0)
            # For polynomial equations in one variable, compare exact solution sets as a second route.
            if not equivalent:
                symbols=sorted(prev.free_symbols | curr.free_symbols, key=str)
                if len(symbols)==1 and sp.Poly(prev,symbols[0]).degree() <= 20 and sp.Poly(curr,symbols[0]).degree() <= 20:
                    a=sp.solveset(prev,symbols[0],domain=sp.S.Complexes); c=sp.solveset(curr,symbols[0],domain=sp.S.Complexes)
                    equivalent = a == c
            results.append({'from_line':i,'to_line':i+1,'valid':bool(equivalent),
                            'message':'Equivalent transformation.' if equivalent else 'This step changes the expression or solution set.',
                            'difference':sp.latex(sp.factor(prev-curr))})
        except Exception:
            results.append({'from_line':i,'to_line':i+1,'valid':None,'message':'Could not safely compare these two lines.','difference':''})
    first=next((item for item in results if item['valid'] is False or item['valid'] is None),None)
    return {'valid': first is None, 'lines_checked':len(lines), 'transitions_checked':len(results),
            'first_issue':first, 'results':results,
            'summary':'All adjacent transformations passed the available symbolic checks.' if first is None else f'First issue is between lines {first["from_line"]} and {first["to_line"]}.'}


@app.post('/api/diagnose')
def diagnose_misconception(b: DiagnoseSteps):
    """Find the first invalid algebra transition and give a cautious misconception diagnosis."""
    lines = [line.strip() for line in b.steps]
    if any(not line or len(line) > 300 for line in lines):
        raise HTTPException(400, 'Each solution line must contain 1–300 characters.')

    audit = audit_steps(AuditSteps(steps=lines))
    issue = audit.get('first_issue')
    if issue is None:
        return {'diagnosed': False, 'valid': True, 'summary': 'No invalid transition was detected in the supported symbolic checks.',
                'misconception': None, 'explanation': 'All adjacent lines appear equivalent under the available algebra checks. This is not a proof that the original problem was solved or that every mathematical condition was respected.',
                'correction': None, 'practice': None, 'confidence': 'limited'}

    before, after = lines[issue['from_line']-1], lines[issue['to_line']-1]
    a, c = before.lower().replace(' ', ''), after.lower().replace(' ', '')
    kind = 'Unrecognised algebraic transformation'
    explanation = 'These two lines do not appear to preserve the same expression or solution set. Recheck the operation applied to both sides and any domain restrictions.'
    correction = None
    practice = 'Solve 3x + 8 = 20 and show each operation on both sides.'
    confidence = 'low'

    # Common school-algebra misconceptions. Pattern matches are intentionally narrow.
    if re.search(r'\bx\s*\+\s*\d+\s*=\s*\d+', before, re.I) and re.search(r'\bx\s*=\s*\d+\s*\+\s*\d+', after, re.I):
        kind = 'Sign error when moving a term'
        explanation = 'A term does not simply cross the equals sign unchanged. Subtract the same constant from both sides; its sign changes because you perform the inverse operation.'
        practice = 'Solve x + 7 = 19. Then check your answer by substitution.'
        confidence = 'medium'
    elif re.search(r'\d+\s*\(\s*x\s*[+-]\s*\d+\s*\)', before) and re.search(r'\d+\s*x\s*[+-]\s*\d+\b', after):
        kind = 'Incomplete distribution'
        explanation = 'The coefficient outside the brackets must multiply every term inside the brackets, not just the variable term.'
        practice = 'Expand 4(x − 3) correctly.'
        confidence = 'medium'
    elif re.search(r'x\s*\^?\s*2\s*=\s*\d+', before, re.I) and re.search(r'x\s*=\s*\d+', after, re.I):
        kind = 'Lost the negative square root'
        explanation = 'For x² = k with k positive, there are generally two real solutions: x = √k and x = −√k. Keeping only the positive root loses a valid solution.'
        practice = 'Solve x² = 49 and verify both roots.'
        confidence = 'medium'
    elif re.search(r'x\s*\*\s*\([^)]*\)\s*=\s*0|x\s*\([^)]*\)\s*=\s*0', before, re.I) and 'x' not in after.split('=')[-1]:
        kind = 'Zero-product property used incompletely'
        explanation = 'If a product is zero, set each factor equal to zero. Dividing by a variable factor can discard the solution where that factor itself is zero.'
        practice = 'Solve x(x − 5) = 0 without dividing by x.'
        confidence = 'low'
    elif re.search(r'x\s*/\s*\d+\s*=\s*\d+', before, re.I):
        kind = 'Incorrect inverse operation with a fraction'
        explanation = 'To undo division by a nonzero number, multiply both sides by that number.'
        practice = 'Solve x/4 = 6 and substitute your result back into the original equation.'
        confidence = 'medium'
    elif re.search(r'\d+\s*\(\s*-[^)]*\)', before):
        kind = 'Possible negative-sign distribution error'
        explanation = 'When distributing a negative coefficient, multiply every term and preserve the resulting signs.'
        practice = 'Expand −3(2x − 5), then check by substituting x = 2.'
        confidence = 'low'

    return {'diagnosed': True, 'valid': False, 'problem': b.problem, 'first_issue': issue,
            'from_line_text': before, 'to_line_text': after,
            'misconception': kind, 'explanation': explanation, 'correction': correction,
            'practice': practice, 'confidence': confidence,
            'summary': f'Possible misconception: {kind}. The first issue is between lines {issue["from_line"]} and {issue["to_line"]}.'}


@app.get('/api/practice')
def practice(topic: str = 'mixed', difficulty: str = 'easy'):
    """Generate a small, locally computed practice question with an exact answer."""
    topic = topic.lower(); difficulty = difficulty.lower()
    if topic not in {'mixed','algebra','calculus','arithmetic','physics','geometry'}:
        raise HTTPException(400, 'Choose mixed, algebra, calculus, arithmetic, physics, or geometry.')
    if difficulty not in {'easy','medium','hard'}:
        raise HTTPException(400, 'Choose easy, medium, or hard difficulty.')
    rng = random.SystemRandom()
    level = {'easy': (2, 9), 'medium': (3, 15), 'hard': (5, 25)}[difficulty]
    a, b = rng.randint(*level), rng.randint(*level)
    bank = []
    if topic in {'mixed','algebra'}:
        root = rng.randint(-level[1], level[1]); coeff = rng.randint(1, 7)
        bank.append((f'Solve for x: {coeff}x {(-coeff*root):+d} = 0', f'solve {coeff}*x{(-coeff*root):+d}=0', str(root), 'algebra'))
    if topic in {'mixed','calculus'}:
        power = rng.randint(2, 5 if difficulty != 'hard' else 8)
        bank.append((f'Differentiate f(x) = x^{power}', f'derivative of x^{power}', str(power)+f'*x^{power-1}', 'calculus'))
    if topic in {'mixed','arithmetic'}:
        bank.append((f'Calculate {a} × {b} + {a}', f'{a}*{b}+{a}', str(a*b+a), 'arithmetic'))
    if topic in {'mixed','physics'}:
        mass, acceleration = rng.randint(1, 12), rng.randint(1, 10)
        bank.append((f'A {mass} kg object accelerates at {acceleration} m/s². Find the net force.', f'physics force mass={mass} acceleration={acceleration}', str(mass*acceleration), 'physics'))
    if topic in {'mixed','geometry'}:
        base, height = rng.randint(2, 20), rng.randint(2, 20)
        ans = sp.Rational(base*height,2)
        bank.append((f'A triangle has base {base} cm and perpendicular height {height} cm. Find its area.', f'triangle area {base},{height}', str(ans), 'geometry'))
    question, command, answer, category = rng.choice(bank)
    solved = E.solve(command)
    return {'question': question, 'command': command, 'expected': answer,
            'topic': category, 'difficulty': difficulty,
            'worked_solution': solved, 'source': 'local deterministic question generator'}


@app.post('/api/plot')
def plot(p: Plot):
    if not math.isfinite(p.xmin) or not math.isfinite(p.xmax):
        raise HTTPException(400, 'Plot bounds must be finite numbers.')
    if p.xmin >= p.xmax or p.xmax - p.xmin > 100000:
        raise HTTPException(400, 'Choose an increasing plotting interval no wider than 100,000 units.')
    try:
        expression = E.P(p.expr)
        if expression.free_symbols - {E.x}:
            raise ValueError('Only x may be used as the graph variable.')
        f = sp.lambdify(E.x, expression, modules=['numpy'])
        # 640 points are sufficient for smooth laptop rendering; cap expensive expressions.
        xs = np.linspace(p.xmin, p.xmax, 640)
        with np.errstate(all='ignore'):
            ys = np.asarray(f(xs.astype(complex)) * np.ones_like(xs), dtype=complex)
        ys = np.where((np.abs(ys.imag) < 1e-9) & (np.abs(ys.real) < 1e6), ys.real, np.nan)
        return {'x': xs.tolist(), 'y': [None if not np.isfinite(v) else float(v) for v in ys]}
    except Exception:
        raise HTTPException(400, 'Cannot plot this expression. Check its syntax and supported functions.')


@app.post('/api/plot/analyze')
def analyze_plot(p: Plot):
    """Return bounded numerical roots and stationary points plus symbolic derivatives."""
    if not math.isfinite(p.xmin) or not math.isfinite(p.xmax):
        raise HTTPException(400, 'Plot bounds must be finite numbers.')
    if p.xmin >= p.xmax or p.xmax - p.xmin > 100000:
        raise HTTPException(400, 'Choose an increasing plotting interval no wider than 100,000 units.')
    try:
        expression = E.P(p.expr)
        if expression.free_symbols - {E.x}:
            raise ValueError('Only x may be used as the graph variable.')
        derivative = sp.simplify(sp.diff(expression, E.x))
        second = sp.simplify(sp.diff(derivative, E.x))
        fn = sp.lambdify(E.x, expression, modules=['numpy'])
        dfn = sp.lambdify(E.x, derivative, modules=['numpy'])
        d2fn = sp.lambdify(E.x, second, modules=['numpy'])

        def evaluate(function, point):
            try:
                value = complex(np.asarray(function(float(point))).item())
                if not (math.isfinite(value.real) and math.isfinite(value.imag)) or abs(value.imag) > 1e-8:
                    return float('nan')
                return float(value.real)
            except Exception:
                return float('nan')

        def locate_zeros(function, samples=480):
            grid = np.linspace(p.xmin, p.xmax, samples + 1)
            values = [evaluate(function, point) for point in grid]
            finite = [abs(value) for value in values if math.isfinite(value)]
            scale = max(finite, default=0.0)
            tolerance = max(1e-300, 1e-10 * scale)
            found = []
            def add(point):
                if p.xmin - 1e-9 <= point <= p.xmax + 1e-9 and not any(abs(point-old) < 1e-5 for old in found):
                    found.append(float(point))
            for i in range(samples):
                left, right = float(grid[i]), float(grid[i+1])
                fl, fr = values[i], values[i+1]
                if math.isfinite(fl) and abs(fl) <= tolerance:
                    add(left)
                if not (math.isfinite(fl) and math.isfinite(fr)) or fl == 0 or fr == 0 or (fl > 0) == (fr > 0):
                    continue
                lo, hi, flo = left, right, fl
                valid = True
                for _ in range(48):
                    mid = (lo + hi) / 2
                    fm = evaluate(function, mid)
                    if not math.isfinite(fm):
                        valid = False
                        break
                    if abs(fm) <= tolerance:
                        lo = hi = mid
                        break
                    if (flo > 0) == (fm > 0):
                        lo, flo = mid, fm
                    else:
                        hi = mid
                root = (lo + hi) / 2
                if valid and abs(evaluate(function, root)) <= max(tolerance * 100, 1e-7):
                    add(root)
            if math.isfinite(values[-1]) and abs(values[-1]) <= tolerance:
                add(float(grid[-1]))
            return sorted(found)

        identically_zero = sp.simplify(expression) == 0
        constant_function = sp.simplify(derivative) == 0
        roots = [] if identically_zero else [{'x': round(root, 8), 'y': 0.0} for root in locate_zeros(fn)]
        stationary = []
        for point in ([] if constant_function else locate_zeros(dfn)):
            curvature = evaluate(d2fn, point)
            kind = 'local minimum' if curvature > 1e-7 else 'local maximum' if curvature < -1e-7 else 'stationary / flat'
            stationary.append({'x': round(point, 8), 'y': round(evaluate(fn, point), 8), 'kind': kind})
        y_intercept = evaluate(fn, 0) if p.xmin <= 0 <= p.xmax else None
        return {
            'expression': str(expression),
            'derivative': str(derivative),
            'second_derivative': str(second),
            'roots': roots[:30],
            'critical_points': stationary[:30],
            'y_intercept': y_intercept if y_intercept is not None and math.isfinite(y_intercept) else None,
            'identically_zero': identically_zero,
            'constant_function': constant_function,
            'method': 'Numerical sign-change search over 480 intervals; approximate results, not a proof.',
            'interval': [p.xmin, p.xmax],
        }
    except Exception:
        raise HTTPException(400, 'Cannot analyse this expression. Check its syntax and supported functions.')



class Plot3D(BaseModel):
    expr: str = Field(min_length=1, max_length=300)
    xmin: float = Field(default=-5, ge=-1000, le=1000)
    xmax: float = Field(default=5, ge=-1000, le=1000)
    ymin: float = Field(default=-5, ge=-1000, le=1000)
    ymax: float = Field(default=5, ge=-1000, le=1000)


@app.post('/api/plot3d')
def plot_3d(data: Plot3D):
    """Return a bounded 25x25 sample grid for a safe two-variable surface plot."""
    if not all(math.isfinite(v) for v in (data.xmin, data.xmax, data.ymin, data.ymax)):
        raise HTTPException(400, 'Surface bounds must be finite numbers.')
    if data.xmin >= data.xmax or data.ymin >= data.ymax:
        raise HTTPException(400, 'Each minimum must be smaller than its maximum.')
    if data.xmax - data.xmin > 100 or data.ymax - data.ymin > 100:
        raise HTTPException(400, 'Choose surface intervals no wider than 100 units.')
    try:
        sx, sy = sp.Symbol('x'), sp.Symbol('y')
        expression = E.P(data.expr, {'x': sx, 'y': sy})
        if expression.free_symbols - {sx, sy}:
            raise ValueError('Only x and y may be used as surface variables.')
        fn = sp.lambdify((sx, sy), expression, modules=['numpy'])
        xs = np.linspace(data.xmin, data.xmax, 25)
        ys = np.linspace(data.ymin, data.ymax, 25)
        xx, yy = np.meshgrid(xs, ys)
        with np.errstate(all='ignore'):
            values = np.asarray(fn(xx, yy))
            if values.ndim == 0:
                values = np.full(xx.shape, values)
            values = np.broadcast_to(values, xx.shape)
        zz = np.asarray(values, dtype=complex)
        valid = (np.abs(zz.imag) < 1e-9) & np.isfinite(zz.real) & (np.abs(zz.real) <= 1e6)
        z = [[float(zz[i, j].real) if valid[i, j] else None for j in range(len(xs))] for i in range(len(ys))]
        return {'x': xs.tolist(), 'y': ys.tolist(), 'z': z, 'samples': 25,
                'expression': data.expr, 'clipped_points': int(valid.size - valid.sum())}
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(400, 'Cannot sample this surface. Check the expression and use only x and y.')


class ResearchRequest(BaseModel):
    expression: str = Field(min_length=1, max_length=500)
    variable: str = Field(default='x', min_length=1, max_length=8)
    point: float = Field(default=0.0, ge=-1e6, le=1e6)
    interval_start: float = Field(default=-5.0, ge=-1e5, le=1e5)
    interval_end: float = Field(default=5.0, ge=-1e5, le=1e5)
    precision: int = Field(default=30, ge=15, le=100)


@app.post('/api/research/analyze')
def research_analyze(data: ResearchRequest):
    """Symbolic calculus and numerical diagnostics for a single-variable expression."""
    if data.interval_start >= data.interval_end:
        raise HTTPException(400, 'The interval start must be smaller than the interval end.')
    try:
        if not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]{0,7}', data.variable):
            raise ValueError('Use a simple variable name such as x or theta.')
        variable = sp.Symbol(data.variable)
        expr = E.P(data.expression, {data.variable: variable})
        if expr.free_symbols - {variable}:
            raise ValueError('Use only the selected variable in this research analysis.')
        derivative = sp.diff(expr, variable)
        second = sp.diff(expr, variable, 2)
        antiderivative = sp.integrate(expr, variable)
        at_point = sp.N(expr.subs(variable, data.point), data.precision)
        derivative_at_point = sp.N(derivative.subs(variable, data.point), data.precision)
        try:
            limit_zero = sp.limit(expr, variable, data.point)
            limit_text = sp.sstr(limit_zero)
        except Exception:
            limit_text = 'Could not determine symbolically'
        try:
            roots = sp.solve(sp.Eq(expr, 0), variable)
            roots_text = [sp.sstr(r) for r in roots[:20]]
        except Exception:
            roots_text = []
        try:
            series = sp.series(expr, variable, data.point, 6).removeO()
            series_text = sp.sstr(series)
        except Exception:
            series_text = 'Series unavailable for this expression.'
        try:
            integral_value = sp.N(sp.integrate(expr, (variable, data.interval_start, data.interval_end)), data.precision)
            integral_text = sp.sstr(integral_value)
        except Exception:
            integral_text = 'Definite integral could not be evaluated exactly.'
        numeric = []
        fn = sp.lambdify(variable, expr, modules=['numpy'])
        for val in np.linspace(data.interval_start, data.interval_end, 41):
            try:
                result = complex(fn(float(val)))
                numeric.append({'x': float(val), 'y': float(result.real) if abs(result.imag) < 1e-9 and math.isfinite(result.real) else None})
            except Exception:
                numeric.append({'x': float(val), 'y': None})
        return {
            'expression': sp.sstr(expr), 'variable': data.variable, 'point': data.point,
            'value': sp.sstr(at_point), 'derivative': sp.sstr(derivative),
            'derivative_latex': sp.latex(derivative), 'second_derivative': sp.sstr(second),
            'antiderivative': sp.sstr(antiderivative), 'antiderivative_latex': sp.latex(antiderivative),
            'limit_at_point': limit_text, 'roots': roots_text, 'taylor_polynomial': series_text,
            'definite_integral': integral_text, 'derivative_at_point': sp.sstr(derivative_at_point),
            'samples': numeric, 'precision_digits': data.precision,
            'notes': ['Symbolic results are generated by SymPy.', 'Numerical samples are approximate and may be undefined at singularities.', 'A symbolic antiderivative may contain an arbitrary constant.']
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(400, 'Unable to analyse this expression: ' + str(exc)[:180])




class MultivariableResearchRequest(BaseModel):
    expression: str = Field(min_length=1, max_length=1200)
    variables: list[str] = Field(min_length=1, max_length=5)
    point: dict[str, float]
    precision: int = Field(default=30, ge=15, le=80)


class VectorFieldResearchRequest(BaseModel):
    components: list[str] = Field(min_length=1, max_length=5)
    variables: list[str] = Field(min_length=1, max_length=5)
    point: dict[str, float]
    precision: int = Field(default=30, ge=15, le=80)


@app.post('/api/research/multivariable')
def research_multivariable(data: MultivariableResearchRequest):
    """Exact gradient/Hessian analysis with a numerical local critical-point test."""
    try:
        return analyze_scalar_field(data.expression, data.variables, data.point, data.precision)
    except Exception as exc:
        raise HTTPException(400, 'Multivariable analysis failed: ' + str(exc)[:180])


@app.post('/api/research/vector-field')
def research_vector_field(data: VectorFieldResearchRequest):
    """Symbolic Jacobian, divergence and 3D curl for a real vector field."""
    try:
        return analyze_vector_field(data.components, data.variables, data.point, data.precision)
    except Exception as exc:
        raise HTTPException(400, 'Vector-field analysis failed: ' + str(exc)[:180])


class IdentityProofRequest(BaseModel):
    left: str = Field(min_length=1, max_length=500)
    right: str = Field(min_length=1, max_length=500)
    variable: str = Field(default='x', min_length=1, max_length=8)


@app.post('/api/proof/identity')
def prove_identity(data: IdentityProofRequest):
    """Check an identity by exact symbolic simplification and independent samples."""
    try:
        if not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]{0,7}', data.variable):
            raise ValueError('Use a simple variable name such as x or theta.')
        variable = sp.Symbol(data.variable)
        loc = {data.variable: variable}
        left, right = E.P(data.left, loc), E.P(data.right, loc)
        difference = sp.simplify(sp.together(left - right))
        exact = difference == 0
        domain_restrictions = []
        for label, expression in (('left', left), ('right', right)):
            denominator = sp.factor(sp.denom(sp.together(expression)))
            if denominator != 1:
                domain_restrictions.append({'side': label, 'denominator': sp.sstr(denominator),
                                            'condition': sp.sstr(sp.Ne(denominator, 0)),
                                            'condition_latex': sp.latex(sp.Ne(denominator, 0))})
        samples = []
        for value in [sp.Rational(1, 3), sp.Rational(2, 1), sp.Rational(-1, 2), sp.Rational(5, 2)]:
            try:
                lv, rv = sp.N(left.subs(variable, value), 30), sp.N(right.subs(variable, value), 30)
                ok = bool(lv.is_finite and rv.is_finite and abs(complex(lv-rv)) < 1e-20)
                samples.append({'at': sp.sstr(value), 'passed': ok})
            except Exception:
                samples.append({'at': sp.sstr(value), 'passed': None})
        return {'valid': bool(exact), 'status': 'Identity verified symbolically' if exact else 'Identity not established',
                'left': sp.sstr(left), 'right': sp.sstr(right), 'difference': sp.sstr(difference),
                'difference_latex': sp.latex(difference), 'symbolic_check': bool(exact), 'numerical_samples': samples,
                'domain_restrictions': domain_restrictions,
                'caution': 'Numerical agreement at sample points alone does not prove an identity. The identity holds only on the common domain; cancelled factors do not restore excluded inputs.'}
    except Exception as exc:
        raise HTTPException(400, 'Could not parse both sides: ' + str(exc)[:180])


@app.get('/api/knowledge/topics')
def knowledge_topics():
    return {'topics': [
        {'name':'Algebra','items':['Linear and quadratic equations','Polynomial factorisation','Rational expressions','Inequalities']},
        {'name':'Calculus','items':['Limits and continuity','Differentiation rules','Definite and indefinite integration','Taylor series']},
        {'name':'Linear algebra','items':['Matrix operations','Determinants and inverses','Eigenvalues and eigenvectors','Linear systems']},
        {'name':'Statistics and probability','items':['Descriptive statistics','Probability rules','Distributions','Hypothesis testing']},
        {'name':'Differential equations','items':['Separable equations','First-order linear equations','Second-order linear equations','Initial value problems']},
        {'name':'Numerical mathematics','items':['Root finding','Numerical integration','Floating-point precision','Error and convergence']},
    ]}


app.include_router(billing_router)

app.mount('/', StaticFiles(directory=os.path.join(os.path.dirname(__file__), 'static'), html=True))
