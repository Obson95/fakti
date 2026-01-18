# Known Issues and Technical Debt

This document tracks known issues, duplicate code, and technical debt in the Fakti application.

---

## ~~Duplicate Dashboards~~ (FIXED)

**Status:** RESOLVED

**What was fixed:**
- Removed duplicate `invoice_dashboard` view from `invoices/views.py`
- Removed duplicate dashboard template from `invoices/templates/invoices/dashboard.html`
- Removed duplicate URL route from `invoices/urls.py`
- Updated all references to point to main dashboard (`{% url 'dashboard' %}`)

---

## Django Deprecation Warning

**Issue:** `ClientDeleteView.delete()` method needs to be moved to `form_valid()`.

**Location:** `invoices/views.py:81-91`

**Warning Message:**
```
DeleteViewCustomDeleteWarning: DeleteView uses FormMixin to handle POST requests.
As a consequence, any custom deletion logic in ClientDeleteView.delete() handler
should be moved to form_valid().
```

**Recommendation:**
Replace the `delete()` method with `form_valid()` in `ClientDeleteView`, `ItemDeleteView`, and similar views.

---

## Status Updated

- Last reviewed: 2024
- Created during: Feature testing phase (Section 3)
