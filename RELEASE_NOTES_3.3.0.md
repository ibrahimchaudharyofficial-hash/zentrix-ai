# ZENTRIX AI 3.3.0 — Clear Workspace & Usage Insights

## Interface improvements
- Reorganised navigation into clear groups: Start here, Math tools, Learn & improve, Your work and Preferences.
- Renamed specialist tools with plain-language labels while preserving their underlying pages and functionality.
- Added a compact dashboard usage panel with today's active time, a two-hour focus progress bar, last-seven-days usage and lifetime usage.
- Updated the light theme to a soft blush-pink, lavender, powder-blue and white palette with subtle ambient pink glow. The dark theme remains separate.

## Active-time tracking
- Counts only while the workspace is visible and the user has interacted within the previous 75 seconds.
- Pauses when the browser tab is hidden or the user is idle.
- Stores usage locally in the browser; no account, cloud service or backend dependency is required.
- Usage begins after the welcome screen is dismissed.

## Compatibility and preservation
- Keeps the existing FastAPI, SymPy and frontend architecture.
- No new Python packages or frontend frameworks.
- Existing solver, verification, OCR, graph, matrix, research, learning, arcade, history and settings workflows are preserved.
- Backend release metadata updated to 3.3.0.

## Tracking note
Active time is an estimate based on browser visibility and recent user input. It is not operating-system-level foreground tracking, and concurrent tabs may contribute separately.
