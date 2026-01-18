# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Fakti is a Django-based SaaS invoice management application for Haitian businesses with bilingual support (Haitian Creole default, English). It enables users to create invoices, manage clients, generate PDFs, and send invoices via email.

## Common Commands

```bash
# Development server
python3 manage.py runserver

# Database
python3 manage.py makemigrations
python3 manage.py migrate

# Run all tests
python3 manage.py test

# Run tests for a specific app
python3 manage.py test invoices
python3 manage.py test users
python3 manage.py test core

# Run a specific test class or method
python3 manage.py test invoices.tests.InvoiceActionsTests
python3 manage.py test invoices.tests.InvoiceActionsTests.test_generate_invoice_pdf

# Translations (i18n)
python3 manage.py makemessages -l ht
python3 manage.py compilemessages
# Alternative if gettext not installed:
python3 compile_messages.py

# Static files (production)
python3 manage.py collectstatic --noinput
```

## Architecture

**Three Django apps:**
- `core/` - Landing page and dashboard views
- `users/` - Custom User model (extends AbstractUser) with business profile fields (business_name, logo, tax_id, language preference)
- `invoices/` - Main application: Client, Invoice, InvoiceItem, Item models

**Project configuration:** `config/` (settings.py, urls.py, wsgi.py)

**Key model relationships:**
- User → Client (one-to-many)
- User → Invoice (one-to-many), Client → Invoice (one-to-many)
- Invoice → InvoiceItem (one-to-many)
- InvoiceItem optionally links to Item (reusable catalog)
- Unique constraint: (user, invoice_number) - each user has unique invoice numbers

## Key Patterns

**Authentication:** All views use `LoginRequiredMixin` (class-based) or `@login_required` (function-based). All model queries filter by `request.user`.

**PDF Generation:** Uses WeasyPrint with conditional import (`WEASYPRINT_INSTALLED` flag). Gracefully degrades if WeasyPrint unavailable. Template: `invoices/templates/invoices/invoice_pdf.html`.

**Forms:** User-aware forms accept `user` in `__init__` to filter querysets. `InvoiceItemFormSet` manages multiple line items per invoice.

**i18n:** Default language is Haitian Creole (`ht`). All user-facing strings use `gettext_lazy`. Translation files in `locale/ht/`.

**Currency:** Supports HTG (Haitian Gourdes) and USD. Decimal fields use `max_digits=10, decimal_places=2`.

## URL Structure

- `/` - Home (unauthenticated) or Dashboard (authenticated)
- `/users/` - Authentication routes (register, login, profile, password reset)
- `/invoicing/` - Invoice app (clients/, invoices/, items/, PDF generation, email)
- `/admin/` - Django admin
- `/i18n/` - Language switching

## Environment

Configuration via `.env` file using python-decouple:
- `DEBUG`, `SECRET_KEY`, `ALLOWED_HOSTS`
- `EMAIL_BACKEND` (console in dev, SMTP in production)
- Database: SQLite for development, PostgreSQL for production
