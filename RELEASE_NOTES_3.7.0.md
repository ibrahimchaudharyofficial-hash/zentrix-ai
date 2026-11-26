# ZENTRIX AI v3.7.0

## Photo OCR reliability and multi-provider AI

- Fixed the AI provider settings API so the provider list, connect, disconnect and status flows use one consistent interface.
- Added/retained selectable Google Gemini, OpenAI, Anthropic Claude and OpenRouter connections using the user's own API key and model ID.
- Fixed the photo-reader provider selector so newly connected providers immediately become selectable and disconnected providers are disabled.
- AI photo transcription routes to the selected provider; image transfer remains explicit and requires confirmation. Images are not persisted by ZENTRIX.
- Kept local Tesseract OCR available without an AI key. It remains an OCR aid rather than a math-aware recognizer; users can review/edit the extracted text or choose a connected vision model for difficult notation.
- Removed conflicting legacy provider routes that shadowed the newer multi-provider settings API.
- Updated regression tests for provider status, selectable connections, OCR flow and the full existing application.

## Important accuracy note

No OCR or vision model is guaranteed to read every mathematical symbol correctly. Always inspect signs, exponents, roots, fractions, decimal points and diagram labels before solving. AI provider API usage may be subject to charges and provider-specific limits.
