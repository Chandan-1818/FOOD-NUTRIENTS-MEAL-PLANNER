# Quick Email Setup Guide

## Why you're not receiving emails:
The `.env` file is missing or not configured. This file contains your email credentials needed to send OTP emails.

## Solution: Create .env File

### Method 1: Manual Creation (Easiest)

1. **Create a new file** named `.env` in your project folder (`D:\Health_Food_Monitor`)

2. **Copy and paste this content** into the `.env` file:

```env
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
```

3. **Replace the placeholders:**
   - Replace `your_email@gmail.com` with your actual Gmail address
   - Replace `your_app_password` with your Gmail App Password (see below)

### Method 2: Using the Setup Script

Run this command in your terminal:
```bash
python setup_env.py
```

Then follow the interactive prompts.

---

## Getting Gmail App Password

**⚠️ IMPORTANT:** You CANNOT use your regular Gmail password. You need an App Password.

### Steps:

1. **Enable 2-Step Verification** (if not already enabled):
   - Go to: https://myaccount.google.com/security
   - Click "2-Step Verification" and follow the steps

2. **Generate App Password**:
   - Go to: https://myaccount.google.com/apppasswords
   - Select:
     - App: **Mail**
     - Device: **Other (Custom name)**
     - Name: **Health Food Monitor**
   - Click **Generate**
   - Copy the 16-character password (looks like: `abcd efgh ijkl mnop`)

3. **Paste in .env file**:
   - Remove all spaces from the password
   - Example: `abcdefghijklmnop`

---

## Example .env File

```env
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=myemail@gmail.com
SMTP_PASSWORD=abcdefghijklmnop
```

---

## After Creating .env File

1. **Save the file** (make sure it's named exactly `.env` - with the dot at the start)

2. **Restart your Flask app** (stop it with Ctrl+C and run `python app.py` again)

3. **Test it**:
   ```bash
   python test_email.py
   ```
   This will send a test email to verify everything works.

4. **Or test by registering** a new user - you should receive the OTP email!

---

## Troubleshooting

### Still not receiving emails?

1. **Check .env file exists** in the project root
2. **Verify credentials** are correct (no extra spaces)
3. **Check spam folder** - emails might be there
4. **Run test script**: `python test_email.py`
5. **Check console output** when registering - it shows email sending status

### Common Errors:

- **"Authentication Error"**: 
  - Make sure you're using App Password (not regular password)
  - Remove spaces from app password
  
- **"Connection Error"**: 
  - Check internet connection
  - Check firewall/antivirus settings

---

## Need Help?

Run these commands to check your configuration:
```bash
python check_email_config.py  # Check if .env is configured
python test_email.py           # Test email sending
```

