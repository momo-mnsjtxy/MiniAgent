# Offline session-command regression tests

Run `python -m pytest -q tests/test_sessions.py` with pytest installed.

These tests import the complete production `handlers/sessions.py` module by file
path. Small fixtures replace NoneBot transport/control-flow, configuration,
permission checks and memory persistence. They do not initialize the full plugin
stack or contact a model, QQ, a database, or any external service. The in-memory
fixture is not an ORM or Pydantic integration test.

Coverage includes invalid/missing/out-of-range/negative/extra session indexes,
exact-position deletion of equal-valued archives, deep-copy restore,
text/multimodal/tool/empty previews, archive/clear behavior, permission and feature
guards, and save-error reporting. Session numbers remain zero-based as displayed.

The repository's full NoneBot startup/load-test pipeline, model adapter behavior,
database migrations and live-platform integration need separate validation.
