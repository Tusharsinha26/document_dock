# DocumentDock

> *"Editorial design meets modern productivity software."*
> **A bespoke document repository and proactive expiry intelligence platform.**

DocumentDock is a full-stack Django web application backed by MongoDB (via PyMongo), created with an original editorial visual identity. It departs radically from generic AI-generated templates or off-the-shelf admin dashboards, offering an art-directed experience inspired by high-end publications, European design studios, and premium fintech tools.

---

## 1. Creative Direction & Brand Identity

### Design Philosophy
- **Editorial Warmth**: Rich typography, asymmetrical layouts, tactile paper/document styling, and natural lighting.
- **Calm Chronometry**: Proactive countdowns, statutory buffers (e.g., 6-month passport validity rules), and quiet reminders instead of chaotic alert notifications.
- **Authentic Craftsmanship**: Custom geometric monogram mark, restrained micro-interactions, and refined status pills.

### Color Palette
| Color | Hex | Role |
| :--- | :--- | :--- |
| **Warm Ivory** | `#F7F5EF` | Primary canvas & background |
| **Deep Forest Green** | `#183D32` | Primary grounding, luxury accents, primary CTAs |
| **Muted Terracotta** | `#D98250` | Warm accent, action windows, urgent countdowns |
| **High-Contrast Charcoal** | `#252824` | Primary typography & deep neutral |
| **Soft Sage** | `#DDE6DC` | Secondary borders, gentle indicator badges |
| **Parchment White** | `#FFFFFF` | Card surfaces & document sheets |

### Typography
- **Headings**: *Playfair Display* — an expressive, high-contrast serif font providing literary elegance.
- **Body & UI**: *DM Sans* — a clean, humanistic sans-serif engineered for digital legibility.
- **Technical Specs**: *JetBrains Mono* — used for document serials, hashes, and status tags.

---

## 2. Key Features

1. **Editorial Landing Page**:
   - **Hero Section**: Asymmetric composition featuring real editorial photography, brand manifesto, and an integrated floating expiry radar preview.
   - **Problem Breakdown ("Small deadlines. Big consequences.")**: Visual storytelling explaining real-world scenarios (the grounded flight, the lapsed auto policy, the tenancy renewal trap).
   - **The 3-Step Protocol**: Horizontal/vertical timeline illustrating document archiving, date tracking, and timely renewal.
   - **Feature Showcase**: Alternating editorial spreads highlighting vault categorization, expiry chronometry, and renewal checklists.
   - **Live Interface Simulation**: Interactive preview showcasing the live dashboard and data tables.
   - **Security & Privacy ("Your papers are your business")**: Zero ad tracking, isolated user storage, and cryptographic token session handling.

2. **Authenticated Dashboard**:
   - Total Documents, Active/Protected, Expiring Soon (Terracotta highlight), and Lapsed/Action Required metrics.
   - **Upcoming Expiry Timeline**: Chronological visual feed showing days remaining, category tags, and direct inspection links.
   - **Recent Uploads**: Fast access to newly archived items.
   - **Vault Composition Breakdown**: Visual progress meters charting records across life domains.

3. **Document Management & Repository (`/documents/`)**:
   - Live client-side and server-side search by title, number, issuer, and notes.
   - Category filtering (Identity & Travel, Vehicles & Transport, Insurance & Health, Property & Housing, Professional & Work, Personal & Finance).
   - Status filtering (Active, Expiring Soon, Expired, Permanent Lifetime).
   - Multi-field sorting (Expiry soonest first, furthest first, newest added, alphabetical).

4. **Add / Edit Document Experience (`/documents/add/`)**:
   - Responsive two-column editorial form with instant drag-and-drop file upload.
   - Configurable advance warning windows (e.g., 30, 60, 90 days).
   - Permanent/Lifetime document toggle (for birth certificates, diplomas).

5. **Document Detail Inspection (`/documents/<id>/`)**:
   - Prominent countdown banner reflecting document health.
   - Full metadata breakdown with issuing authority and notes.
   - Step-by-step renewal action protocol checklist.
   - Integrated digital asset viewer (image scans or PDF preview).

---

## 3. Technical Architecture (For College Presentation)

When explaining this project to a professor or evaluator, here are the key technical highlights:

1. **Full-Stack Django (Backend)**:
   - Built on Python 3 and Django 6.
   - Custom `vault` application handling views, forms, business logic, and routing.
   - Django's built-in session authentication framework ensures secure login, registration, and password hashing (`PBKDF2`).

2. **MongoDB Data Layer (`vault/db.py`)**:
   - Leverages **PyMongo** to interface with MongoDB database `documentdock_db` and the `documents` collection.
   - **Dynamic Date Chronometry**: Expiry status and remaining days are calculated dynamically upon query relative to `date.today()`, eliminating stale or hardcoded database values.
   - **Resilient Fallback**: Includes a transparent JSON fallback mechanism so that if MongoDB is temporarily offline or running in a sandboxed port environment, the application continues to run without throwing unhandled exceptions.

3. **Asset Handling & Security**:
   - File uploads are validated and stored in `media/documents/`.
   - All document CRUD operations are strictly scoped to `request.user.id`, guaranteeing tenant isolation.

---

## 4. Quickstart Guide

### 1. Activate Environment
```bash
source venv/bin/activate
```

### 2. Apply Migrations (User Auth & Sessions)
```bash
python manage.py migrate
```

### 3. Start MongoDB (Optional)
If MongoDB is installed locally:
```bash
brew services start mongodb-community
```
*(If MongoDB is not running, DocumentDock will automatically use its internal persistent fallback store without any errors!)*

### 4. Run Development Server
```bash
python manage.py runserver
```
Visit `http://127.0.0.1:8000/` in your browser.

### 5. Instant Demo Access
To immediately evaluate the dashboard with pre-seeded realistic documents (British Passport, Allianz Insurance, Lease Agreement, etc.), click **"Explore Demo"** or **"Launch Interactive Demo Vault"** on the landing page or login screen (`/demo/`).

