# ZENTRIX AI 3.4.0 — Photo reading reliability

## Local OCR improvements
- Tesseract.js library loading retries through jsDelivr and unpkg. A failed initialisation can be retried rather than leaving a rejected worker promise cached.
- Worker, WebAssembly core and English language-data paths are explicit; the worker setup has a second CDN configuration.
- Image preprocessing is bounded to a 2,400-pixel maximum edge and approximately 4 megapixels, reducing the chance of high memory use on modest laptops.
- Four candidate readings compare the original image, contrast-enhanced grayscale, black-and-white and sparse-layout segmentation.
- The status message distinguishes good, moderate and low Tesseract confidence.

## Optional AI math reading
- When Gemini is connected, a separate AI math reading button transcribes math notation using the configured Gemini model.
- The button is hidden unless Gemini is connected. A confirmation is shown before image data is sent to Google.
- The browser compresses the image before sending it to the local backend. The backend validates the request, forwards the image to Gemini in memory, returns transcription text and does not save the image.
- The output remains unverified text. Users must inspect it before solving.

## Known limits
Tesseract remains general-purpose printed-text OCR; it is not a dedicated mathematical OCR model. Handwriting, stacked fractions, superscripts, radicals, dense layouts and diagrams may still be misread. Gemini transcription can also be wrong and may consume provider quota.
