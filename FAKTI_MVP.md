# Fakti SaaS Invoice Generator MVP

## Overview
Fakti is a SaaS invoice generator designed for Haitian businesses, with a focus on simplicity, multilingual support (Haitian Creole + English), and modern usability. Built with Django (backend) and Bootstrap (frontend), Fakti aims to empower small businesses to manage invoices efficiently and professionally.

---

## Core MVP Features

### 1. User Accounts & Authentication
- Email/password sign up, login, logout
- User profile: business name, logo, contact info
- Role support: admin, staff (optional for MVP)

### 2. Multilingual Support
- Haitian Creole (default) and English
- Language toggle in user settings
- Uses Django’s `gettext` for translations

### 3. Invoice Creation
- Create invoices with client info (name, address, phone/email)
- Add multiple line items (description, quantity, unit price)
- Automatic tax/discount fields
- Auto-calculated totals

### 4. Invoice Templates
- Branded templates (business logo + info)
- Download as PDF
- Email invoice to client

### 5. Client Management
- Save clients for reuse
- View client’s past invoices

### 6. Dashboard
- List of invoices (Paid, Unpaid, Overdue)
- Quick stats (total outstanding, total paid, etc.)

### 7. Payments (Basic)
- Mark invoice as Paid/Unpaid
- (Future: Integrate PayPal, Stripe, MonCash)

### 8. SaaS Features
- Subscription plans (free + paid tier)
- Stripe subscription integration (future)
- Plan-based limits (e.g., free = 5 invoices/month)

---

## Technology Stack
- **Backend:** Django (Python)
- **Frontend:** Bootstrap 5 (modern, responsive UI)
- **Database:** PostgreSQL (recommended)
- **PDF Generation:** WeasyPrint or ReportLab
- **Email:** Django’s email backend (SMTP)
- **Payments:** Stripe (future), MonCash (future)
- **i18n:** Django’s built-in translation system

---

## MVP Roadmap
1. **Project Setup**: Django project, Bootstrap integration, GitHub repo
2. **User Auth**: Registration, login, profile
3. **Multilingual**: Add Creole/English, translation files
4. **Invoice Model**: CRUD for invoices, line items, totals
5. **Client Model**: CRUD for clients
6. **Dashboard**: Invoice list, stats
7. **PDF/Email**: Generate/download PDF, send invoice email
8. **Payments**: Mark as paid/unpaid
9. **SaaS**: Basic plan limits, Stripe integration (future)

---

## Design Principles
- **Creole-first UI**: Prioritize Haitian Creole, with easy English toggle
- **Mobile-friendly**: Bootstrap for responsive design
- **Simple, modern look**: Clean, professional, easy to use
- **Offline PDF**: Download invoices for offline use

---

## Nice-to-Have (Post-MVP)
- Recurring invoices
- Expense tracking
- Team collaboration
- QR code for payment
- Offline-first/PWA

---

## Getting Started (for Developers)
1. Clone the repo
2. Set up Python & Django
3. Install dependencies
4. Run migrations
5. Start the dev server

---

## Learning Resources
- [Django Documentation](https://docs.djangoproject.com/)
- [Bootstrap Documentation](https://getbootstrap.com/)
- [Django i18n](https://docs.djangoproject.com/en/stable/topics/i18n/)
- [WeasyPrint](https://weasyprint.org/) / [ReportLab](https://www.reportlab.com/)

---

## License
MIT (or your choice)

---

*Let’s build Fakti together!*
