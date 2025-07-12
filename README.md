Team members k nam Or email dalde readme mae
Aashi :aashikohad05@gmail.com 
Aditi:aditibhattad2310@gmail.com
pranay:pranaykalamkar22@gmail.com
sachin: sachinryadav1805@gmail.com
# SwapSkills - Skill Swap Platform (Enhanced)

## 🚀 Features:
- Register/Login with password hashing (secure)
- Add/View offered and wanted skills
- Public/Private profile visibility
- Browse/search other users' profiles
- Send, accept, reject, delete swap requests
- Leave feedback and rating after swap
- Upload profile photo
- Admin panel to ban users, moderate content, view logs
- 🎨 Styled using Bootstrap 5
- 📧 Real Email Verification using Gmail SMTP

## 📦 Setup Instructions

1. Clone/Download this project.
2. Install requirements:
```bash
pip install flask flask-session flask-mail itsdangerous werkzeug
```
3. Set up Gmail App Password:
   - Go to https://myaccount.google.com/security
   - Enable 2-Step Verification
   - Create an App Password for Gmail
4. Create a file `config.py` in the root folder:

```python
EMAIL_ADDRESS = "your_email@gmail.com"
EMAIL_PASSWORD = "your_app_password"
```

5. Run the app:
```bash
python app.py
```

6. Open browser at [http://127.0.0.1:5000](http://127.0.0.1:5000)

## 📬 Email Confirmation
- After registering, the app sends a confirmation email.
- The user must click the link to verify the email before login (can be made optional).
