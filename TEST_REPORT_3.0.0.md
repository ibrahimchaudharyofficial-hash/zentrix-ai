# ZENTRIX AI 3.0.0 — Build Verification

## Automated checks

- Python `compileall`: passed.
- JavaScript syntax validation with Node.js: passed.
- Pytest regression and v3.0 research tests: **52 passed**.
- Research API: derivative, point evaluation, definite integral and numerical samples tested.
- Identity API: true and false identities tested.
- Knowledge topics and learning profile endpoints tested.

## Verification boundaries

- Tests run in the build environment, not on the user's physical Dell Latitude 5520.
- OCR was validated for pipeline syntax and integration, not against a labelled image-accuracy benchmark. Handwriting and complex mathematical layouts are not guaranteed.
- Performance, memory use and OCR recognition rates have not been measured on the target laptop.
- Browser-side OCR and KaTeX assets use CDN delivery in the existing interface and therefore need internet access when those assets are not cached.

## Result

The release passes the automated checks listed above. See `README.md` and `RELEASE_NOTES_3.0.0.md` for supported features and known limitations.
