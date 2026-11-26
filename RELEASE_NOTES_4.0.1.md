# ZENTRIX AI v4.0.1 — AI Photo Reading Fix

- Fixed AI math reading: the frontend previously called a missing `photoForGemini()` image-preparation helper, which caused the generic “AI math reading could not complete” message.
- Added browser-side image orientation handling, resizing and JPEG compression before an image is sent to the user-selected provider.
- Enforces a safe compressed image size below the backend's 975 KB image limit.
- Improved error feedback so the photo panel and notification show the actual failure reason.
- Images are still sent only after the user's confirmation and are not stored by ZENTRIX.
- Preserves Matrix Lab, Definitions, Exam Centre, school-level solver and existing provider integrations.
