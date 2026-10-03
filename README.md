# CIMS - Campus Infrastructure Monitoring System

A web application where students report campus infrastructure problems (broken lights, water issues, Wi-Fi, etc.) and admins track and resolve them. It runs locally on the campus Wi-Fi network.

## Features

- **Secure sign up and sign in** with email, username validation, password rules and a generic login error
- **Report complaints** with title, location, description and an optional photo
- **AI-based priority** (High / Medium / Low) assigned automatically using the Gemini API
- **Admin panel** to review complaints and update their status (Pending, In Progress, Resolved)
- **Email notifications**
  - Admin gets an email when a student files a new complaint
  - Student gets an email when the status of their complaint changes
- **Analytics dashboard** with priority chart, top locations, status breakdown and average resolution time
- **Overdue complaints** flagged when unresolved for more than 6 days

## Tech Stack

- **Backend:** Python, Flask, Flask-SQLAlchemy
- **Database:** SQLite
- **Frontend:** HTML, CSS, vanilla JavaScript, Chart.js
- **AI:** Google Gemini API
- **Email:** Gmail SMTP (`smtplib`)

## Project Structure

```
campus-infrastructure-monitoring/
  backend/
    app.py            # Flask app and API routes
    email_utils.py    # Email sending functions
    .env.example      # Template for required settings
    requirements.txt
  frontend/           # HTML pages and static files
```

## How to Run

1. **Clone the project**
```
   git clone https://github.com/sakshishinde5172-cmd/campus-infrastructure-monitoring.git
   cd campus-infrastructure-monitoring
```

2. **Create and activate a virtual environment**
```
   python -m venv venv
   venv\Scripts\Activate.ps1
```

3. **Install the packages**
```
   pip install -r backend\requirements.txt
```

4. **Create the settings file**

   Copy `backend\.env.example` to `backend\.env` and fill in your own values:
```
   GEMINI_API_KEY=your_gemini_key
   EMAIL_ADDRESS=your_sender_gmail@gmail.com
   EMAIL_APP_PASSWORD=your_16_letter_gmail_app_password
   ADMIN_EMAIL=your_admin_email@gmail.com
```
   The Gmail account needs 2-Step Verification turned on to create an App Password.

5. **Start the server**
```
   cd backend
   python app.py
```

6. **Open the site** at http://localhost:5000. Other devices on the same Wi-Fi can use `http://YOUR-PC-IP:5000`.

## Author

Sakshi Shinde

