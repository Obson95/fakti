# Fakti Features List

This document lists all implemented features in the Fakti application. Each feature will be reviewed and tested in a dedicated branch.

---

## 1. User Authentication & Account Management

- [x] 1.1 User registration with username, email, password, business name
- [x] 1.2 User login
- [x] 1.3 User logout
- [x] 1.4 Password change (authenticated users)
- [x] 1.5 Password reset via email
- [x] 1.6 Account deletion
- [x] 1.7 Profile editing (first name, last name, email)
- [x] 1.8 Business profile editing (business name, address, phone, tax ID)
- [x] 1.9 Business logo upload
- [x] 1.10 Language preference setting (Haitian Creole/English)

---

## 2. Dashboard

- [x] 2.1 Statistics cards (total invoices, paid, unpaid, overdue counts)
- [x] 2.2 Total revenue display (sum of paid invoices)
- [x] 2.3 Total outstanding amount display
- [x] 2.4 Payment rate percentage
- [x] 2.5 Total clients count
- [x] 2.6 Recent invoices list (last 5)
- [x] 2.7 Recent clients list (last 5)
- [x] 2.8 Quick action buttons (create invoice, add client, view all)

---

## 3. Client Management

- [x] 3.1 Create new client
- [x] 3.2 View client list
- [x] 3.3 View client detail with associated invoices
- [x] 3.4 Edit client information
- [x] 3.5 Delete client
- [x] 3.6 Quick invoice creation from client profile

---

## 4. Item Management (Reusable Catalog)

- [x] 4.1 Create new item
- [x] 4.2 View item list
- [x] 4.3 Edit item
- [x] 4.4 Delete item
- [x] 4.5 Item selection in invoice forms
- [x] 4.6 Item detail API endpoint (JSON)

---

## 5. Invoice Management

- [x] 5.1 Create new invoice with line items
- [x] 5.2 Auto-generated invoice numbers (INV-YYYY-XXXXX)
- [x] 5.3 View invoice list
- [x] 5.4 View invoice detail
- [x] 5.5 Edit invoice and line items
- [x] 5.6 Delete invoice
- [x] 5.7 Status management (Draft, Sent, Paid, Overdue, Canceled)
- [x] 5.8 Currency selection (HTG, USD)
- [x] 5.9 Tax percentage calculation
- [x] 5.10 Discount percentage calculation
- [x] 5.11 Dynamic line item add/remove
- [x] 5.12 Automatic calculations (line totals, subtotal, tax, discount, total)
- [x] 5.13 Notes/payment terms field

---

## 6. Invoice List Features

- [x] 6.1 Status filter buttons
- [x] 6.2 Status badges (color-coded)
- [x] 6.3 Invoice counts by status
- [x] 6.4 Total amounts display (all, paid, outstanding)
- [x] 6.5 Responsive table view (desktop)
- [x] 6.6 Responsive card view (mobile)

---

## 7. PDF Generation

- [x] 7.1 Generate PDF invoice
- [x] 7.2 PDF includes all invoice details and itemization
- [x] 7.3 Automatic filename generation
- [x] 7.4 Download PDF functionality

---

## 8. Email Functionality

- [x] 8.1 Send invoice via email
- [x] 8.2 To/CC/BCC fields with validation
- [x] 8.3 Customizable subject line
- [x] 8.4 Customizable message body
- [x] 8.5 Optional PDF attachment
- [x] 8.6 Reply-To header support
- [x] 8.7 Auto-change draft status to sent after email

---

## 9. Localization

- [x] 9.1 Haitian Creole language support (default)
- [x] 9.2 English language support
- [x] 9.3 Language toggle/switching
- [x] 9.4 Multi-currency display (HTG, USD)

---

## 10. Security & Access Control

- [x] 10.1 Login required for all protected features
- [x] 10.2 User-specific data isolation
- [x] 10.3 Unique invoice numbers per user

---

## 11. Admin

- [ ] 11.1 Django admin interface access
- [ ] 11.2 Admin user management

---

## Branch Naming Convention

For each feature, create a branch using this format:
```
feature/<section>-<number>-<short-description>
```

Examples:
- `feature/1-1-user-registration`
- `feature/3-1-create-client`
- `feature/5-1-create-invoice`
- `feature/7-1-generate-pdf`

---

## Testing Workflow

1. Create feature branch from main
2. Review and test the feature
3. Fix any issues found
4. Write/update tests if needed
5. Mark feature as complete in this document
6. Merge branch back to main
