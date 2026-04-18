# 🚗 Car Rental Management System

A full-stack web application for managing car rentals, built with **Flask** and **MySQL** as a DBMS Mini Project. The system handles end-to-end rental operations including customer management, fleet tracking, booking lifecycle, payment processing, and automated vehicle servicing.

---

## ✨ Features

| Module | Capabilities |
|--------|-------------|
| **Dashboard** | At-a-glance stats — total customers, cars, active bookings, and pending services |
| **Customers** | Add and view customers with phone, address, driving license, and UPI details |
| **Cars** | Register vehicles with number plate, name, type, and hourly rent rate |
| **Bookings** | Create, complete, or cancel bookings with automatic car availability management |
| **Payments** | Record payments (UPI / Cash / Card) against bookings |
| **Servicing** | Track vehicle maintenance; mark services as completed to release cars |
| **Auto-Servicing Trigger** | MySQL trigger automatically schedules servicing after every 10 completed bookings per car |
| **Health Check API** | `GET /api/health` endpoint for monitoring |

---

## 🛠️ Tech Stack

- **Backend:** Python 3, Flask
- **Database:** MySQL 8+
- **ORM / Driver:** PyMySQL (with DictCursor)
- **Templating:** Jinja2 (Flask templates)
- **Frontend:** HTML, CSS, JavaScript
- **Config:** python-dotenv (`.env` file)

---

## 📐 Database Schema

```
┌─────────────┐       ┌─────────────┐
│  customers   │       │    cars      │
├─────────────┤       ├─────────────┤
│ customer_id  │◄──┐   │ car_id       │◄──┐
│ customer_name│   │   │ car_number..│   │
│ phone        │   │   │ car_name     │   │
│ address      │   │   │ vehicle_type │   │
│ driving_lic..│   │   │ rent_per_hour│   │
│ upi_id       │   │   │ status       │   │
│ created_at   │   │   │ booking_count│   │
└─────────────┘   │   └─────────────┘   │
                  │                     │
            ┌─────┴─────────────────────┴──┐
            │          bookings             │
            ├───────────────────────────────┤
            │ booking_id                    │
            │ customer_id (FK → customers)  │
            │ car_id      (FK → cars)       │
            │ hours                         │
            │ total_rent                    │
            │ booking_date                  │
            │ status                        │
            └────────────┬──────────────────┘
                         │
              ┌──────────┴──────────┐
              │     payments        │
              ├─────────────────────┤
              │ payment_id          │
              │ booking_id (FK)     │
              │ amount_paid         │
              │ payment_method      │
              │ payment_status      │
              └─────────────────────┘

┌─────────────────────┐
│     servicing        │
├─────────────────────┤
│ service_id           │
│ car_id (FK → cars)   │
│ service_date         │
│ service_type         │
│ status               │
└─────────────────────┘
```

### 🔁 Trigger — `after_booking_completed`

When a booking status changes to **completed**:
1. The car's `booking_count` is incremented.
2. If `booking_count` reaches **10**, a servicing record is auto-created, the counter resets, and the car is put into **maintenance**.
3. Otherwise, the car is set back to **available**.

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.8+**
- **MySQL 8+** (running locally or remotely)
- **pip** package manager

### 1. Clone the repository

```bash
git clone <repository-url>
cd car_rental
```

### 2. Create a virtual environment (recommended)

```bash
python3 -m venv venv
source venv/bin/activate   # macOS / Linux
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Copy the example env file and update it with your MySQL credentials:

```bash
cp .env.example .env
```

Edit `.env`:

```env
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=car_rental
```

### 5. Set up the database schema

```bash
mysql -u root -p < schema.sql
```

This creates the `car_rental` database, all tables, and the auto-servicing trigger.

### 6. Run the application

```bash
python app.py
```

The app will start at **http://localhost:5000**.

---

## 📁 Project Structure

```
car_rental/
├── app.py              # Flask application — routes & business logic
├── db.py               # Database connection helper (PyMySQL)
├── schema.sql          # MySQL schema + trigger definition
├── requirements.txt    # Python dependencies
├── .env.example        # Environment variable template
├── static/
│   ├── css/            # Stylesheets
│   └── js/             # Client-side scripts
└── templates/
    ├── base.html       # Base layout (Jinja2)
    ├── index.html      # Dashboard
    ├── customers.html  # Customer management
    ├── cars.html       # Car fleet management
    ├── bookings.html   # Booking operations
    ├── payments.html   # Payment tracking
    └── servicing.html  # Vehicle servicing
```

---

## 🔌 API Endpoints

| Method | Route | Description |
|--------|-------|-------------|
| `GET` | `/` | Dashboard with summary stats |
| `GET / POST` | `/customers` | List & add customers |
| `GET / POST` | `/cars` | List & add cars |
| `GET / POST` | `/bookings` | List, create, complete, or cancel bookings |
| `GET / POST` | `/payments` | List & record payments |
| `GET / POST` | `/servicing` | List services & mark as completed |
| `GET` | `/api/health` | JSON health-check endpoint |

---

## 📝 License

This project is developed as part of a **DBMS Mini Project** for academic purposes.
