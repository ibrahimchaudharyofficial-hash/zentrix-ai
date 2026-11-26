# ZENTRIX AI 3.3.0 — Test Report

## Automated validation
- `python -m pytest -q`: **64 passed**. This includes the complete 3.2.0 regression suite and four new 3.3.0 checks for API version, usage tracker markup, plain-language navigation and theme preservation.
- `python -m compileall -q backend`: passed.
- Inline JavaScript extracted from the served HTML and checked with `node --check`: passed.

## Release changes
- Reorganised navigation into understandable groups and renamed tools with plain-language labels.
- Added active-use tracking with daily, rolling seven-day and lifetime totals.
- The tracker pauses when the tab is hidden and after 75 seconds without user activity.
- Usage is stored in browser local storage; it does not require a server database or cloud account.
- Added a blush-pink and lavender light palette while preserving the dark theme.
- Updated the backend API version to 3.3.0.

## Boundaries
The usage timer is browser-based and estimates active time from tab visibility and recent interaction. It is not operating-system-level foreground tracking. Concurrent tabs may count independently. No physical performance benchmark or browser automation benchmark was performed in this environment.
