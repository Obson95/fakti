# Fakti Deployment Checklist

Use this checklist to prepare and deploy Fakti to production.

## 1) Environment and Secrets
- Set `DEBUG=False`
- Set `ALLOWED_HOSTS` to your domain(s) and/or IP(s)
- Create a strong `SECRET_KEY` and set via environment variable
- Configure database (PostgreSQL recommended) and set `DATABASE_URL` or Django DB settings

## 2) Static and Media Files
- Run `python manage.py collectstatic` during your build step
- Ensure `STATIC_ROOT` is served by your web server (nginx) or a CDN
- Ensure `MEDIA_ROOT` is writable and served (user logos)

## 3) Email (Production)
- Set SMTP with env vars:
  - `EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend`
  - `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_USE_TLS`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`
  - `DEFAULT_FROM_EMAIL=no-reply@yourdomain`

## 4) WeasyPrint PDF Dependencies
WeasyPrint requires system libraries for rendering.
- Windows: install prebuilt WeasyPrint / GTK/WebKit dependencies (see weasyprint.org)
- Linux (Debian/Ubuntu example):
  - `apt-get install -y libpango-1.0-0 libgdk-pixbuf2.0-0 libcairo2 libffi-dev libpangoft2-1.0-0 libpangocairo-1.0-0`
- Verify runtime can fetch images from `MEDIA_URL`. The app passes `base_url` to resolve URLs.

## 5) Security and Middleware
- `SECURE_SSL_REDIRECT=True` behind HTTPS
- Set `CSRF_COOKIE_SECURE=True`, `SESSION_COOKIE_SECURE=True` when using HTTPS
- Consider `X-Frame-Options`, `Content-Security-Policy`

## 6) Internationalization
- Compile messages: `django-admin compilemessages` (or `python manage.py compilemessages`) before build
- Confirm default language is Kreyòl (`LANGUAGE_CODE=ht`) and language switcher functioning

## 7) Application Server
- Use a WSGI server (gunicorn/uwsgi) behind nginx
- Configure health check URL and logging

## 8) Database Migrations
- Run `python manage.py migrate` on deploy
- Ensure new UniqueConstraint for `(user, invoice_number)` has been applied

## 9) Monitoring and Logs
- Configure application logs (gunicorn/nginx) and error reporting as needed

## 10) Backups
- Schedule periodic DB backups
- Backup media assets (logos)

---

## Quick Commands (reference)

- Migrations:
  - `python manage.py makemigrations`
  - `python manage.py migrate`

- Static files:
  - `python manage.py collectstatic --noinput`

- i18n:
  - `python manage.py makemessages -l ht`
  - `python manage.py compilemessages`

