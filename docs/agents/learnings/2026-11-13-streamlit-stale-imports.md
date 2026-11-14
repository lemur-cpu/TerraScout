# Streamlit reruns app.py without reloading imported dashboard modules

**Area:** `src/terra_scout/dashboard/app.py`
**Symptom:** `ImportError: cannot import name 'SKEPTIC_EMPTY' from 'terra_scout.dashboard.copy'` (same pattern earlier for `evidence_packet`) while the name exists in the file on disk.
**Cause:** Streamlit keeps `sys.modules`. A rerun of `app.py` after a hot save does `from copy import NEW_NAME` against the previously imported module.
**Do this:** `importlib.reload` `dashboard.copy` and `dashboard.review` before reading names. Restart the Streamlit process if the error is already on screen.
**Evidence:** `test_stale_copy_module_needs_reload_to_export_new_names`, `test_dashboard_app_reloads_copy_before_named_imports`
**Ticket:** candidate-finder
