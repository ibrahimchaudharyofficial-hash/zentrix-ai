# Zentrix AI 1.3.0

## Photo question reader
- Added image selection and drag-and-drop to the main solver.
- Added browser-based OCR using Tesseract.js, loaded only when the user requests recognition.
- Supports common image formats accepted by the browser, with a 12 MB upload-size guard.
- Shows a preview and editable recognised text so users can correct OCR mistakes before solving.
- Recognised text is sent to the existing local math engine; the image itself is not uploaded to the Zentrix backend.
- OCR requires an internet connection the first time to load the library and English language data. The mathematical calculation remains local and does not require a Gemini API key.

## Existing functionality retained
- SymPy-based exact calculations, step-by-step output, verification, graphing, Matrix Lab, browser-local history, Gemini optional settings, and generated geometry diagrams.

## Important limitations
- OCR quality depends on image clarity, lighting, handwriting, layout, and mathematical notation. Handwritten equations and complex multi-column pages may be misread.
- Always review the extracted text before solving. OCR does not itself make unsupported question types solvable; the local engine's supported operations still apply.
