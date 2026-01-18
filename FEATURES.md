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

- [ ] 2.1 Statistics cards (total invoices, paid, unpaid, overdue counts)
- [ ] 2.2 Total revenue display (sum of paid invoices)
- [ ] 2.3 Total outstanding amount display
- [ ] 2.4 Payment rate percentage
- [ ] 2.5 Total clients count
- [ ] 2.6 Recent invoices list (last 5)
- [ ] 2.7 Recent clients list (last 5)
- [ ] 2.8 Quick action buttons (create invoice, add client, view all)

---

## 3. Client Management

- [ ] 3.1 Create new client
- [ ] 3.2 View client list
- [ ] 3.3 View client detail with associated invoices
- [ ] 3.4 Edit client information
- [ ] 3.5 Delete client
- [ ] 3.6 Quick invoice creation from client profile

---

## 4. Item Management (Reusable Catalog)

- [ ] 4.1 Create new item
- [ ] 4.2 View item list
- [ ] 4.3 Edit item
- [ ] 4.4 Delete item
- [ ] 4.5 Item selection in invoice forms
- [ ] 4.6 Item detail API endpoint (JSON)

---

## 5. Invoice Management

- [ ] 5.1 Create new invoice with line items
- [ ] 5.2 Auto-generated invoice numbers (INV-YYYY-XXXXX)
- [ ] 5.3 View invoice list
- [ ] 5.4 View invoice detail
- [ ] 5.5 Edit invoice and line items
- [ ] 5.6 Delete invoice
- [ ] 5.7 Status management (Draft, Sent, Paid, Overdue, Canceled)
- [ ] 5.8 Currency selection (HTG, USD)
- [ ] 5.9 Tax percentage calculation
- [ ] 5.10 Discount percentage calculation
- [ ] 5.11 Dynamic line item add/remove
- [ ] 5.12 Automatic calculations (line totals, subtotal, tax, discount, total)
- [ ] 5.13 Notes/payment terms field

---

## 6. Invoice List Features

- [ ] 6.1 Status filter buttons
- [ ] 6.2 Status badges (color-coded)
- [ ] 6.3 Invoice counts by status
- [ ] 6.4 Total amounts display (all, paid, outstanding)
- [ ] 6.5 Responsive table view (desktop)
- [ ] 6.6 Responsive card view (mobile)

---

## 7. PDF Generation

- [ ] 7.1 Generate PDF invoice
- [ ] 7.2 PDF includes all invoice details and itemization
- [ ] 7.3 Automatic filename generation
- [ ] 7.4 Download PDF functionality

---

## 8. Email Functionality

- [ ] 8.1 Send invoice via email
- [ ] 8.2 To/CC/BCC fields with validation
- [ ] 8.3 Customizable subject line
- [ ] 8.4 Customizable message body
- [ ] 8.5 Optional PDF attachment
- [ ] 8.6 Reply-To header support
- [ ] 8.7 Auto-change draft status to sent after email

---

## 9. Localization

- [ ] 9.1 Haitian Creole language support (default)
- [ ] 9.2 English language support
- [ ] 9.3 Language toggle/switching
- [ ] 9.4 Multi-currency display (HTG, USD)

---

## 10. Security & Access Control

- [ ] 10.1 Login required for all protected features
- [ ] 10.2 User-specific data isolation
- [ ] 10.3 Unique invoice numbers per user

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
