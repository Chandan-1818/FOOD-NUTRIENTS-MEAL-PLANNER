# 🚀 Quick Start - Receive OTP Emails

## Automatic Setup (Recommended)

Run this command to automatically create `.env` file and test email:

```bash
python auto_setup_email.py
```

The script will:
1. ✅ Ask you to select email provider (Gmail/Outlook/Yahoo)
2. ✅ Ask for your email and password
3. ✅ Create `.env` file automatically
4. ✅ Send you a test OTP email immediately
5. ✅ Verify everything works

---

## Manual Setup (Alternative)

If you prefer to create `.env` manually:

1. **Create `.env` file** in project root
2. **Add this content:**
   ```
   SMTP_SERVER=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USERNAME=your_email@gmail.com
   SMTP_PASSWORD=your_app_password
   ```
3. **Get Gmail App Password:** https://myaccount.google.com/apppasswords
4. **Test:** `python test_email.py`

---

## After Setup

1. **Restart Flask app** (if running)
2. **Register a new user** - OTP will be sent automatically!
3. **Check your email** for the OTP code

---

## Need Help?

- Run: `python check_email_config.py` - Check configuration
- Run: `python test_email.py` - Test email sending
- See: `QUICK_SETUP.md` - Detailed instructions

