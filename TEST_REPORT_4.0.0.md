# ZENTRIX AI v4.0.0 test report

- Pytest: **82 passed**.
- Python backend compileall: passed.
- Inline JavaScript syntax (`node --check`): passed.
- ZIP integrity (`ZipFile.testzip`): passed; 100 archive entries.
- Release health endpoint reports version 4.0.0.
- Regression checks confirm Matrix Lab and the Definitions page remain available.
- Exam Centre checks cover navigation, subject/length/level controls, question flow, score persistence, and result actions.

Exam Centre questions are a fixed local practice bank. Test progress is stored in browser localStorage on the current device; it is not synced between devices.
