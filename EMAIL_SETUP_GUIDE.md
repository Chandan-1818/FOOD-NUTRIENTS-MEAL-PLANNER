# Email Configuration Guide for OTP Verification

This guide will help you configure email settings so users can receive OTP codes via email.

## Quick Setup (Recommended)

Run the automated configuration script:

```bash
python configure_email.py
```

This script will guide you through the entire setup process.

## Manual Setup

### Step 1: Create Gmail App Password

1. **Enable 2-Step Verification**
   - Go to: https://myaccount.google.com/security
   - Click on "2-Step Verification"
   - Follow the prompts to enable it

2. **Generate App Password**
   - Go to: https://myaccount.google.com/apppasswords
   - Select "Mail" as the app
   - Select "Other (Custom name)" as the device
   - Enter "Food Insight" as the name
   - Click "Generate"
   - **Copy the 16-character password** (it looks like: `abcd efgh ijkl mnop`)

### Step 2: Create .env File

Create a file named `.env` in your project root with the following content:

```env
# Email Configuration for OTP Verification
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_16_character_app_password
```

**Important Notes:**
- Replace `your_email@gmail.com` with your Gmail address
- Replace `your_16_character_app_password` with the App Password (remove spaces)
- **DO NOT** use your regular Gmail password - it won't work!

### Step 3: Test Email Configuration

Run the test script:

```bash
python test_email.py
```

Enter your email address when prompted. If you receive the test email, your configuration is working!

## Troubleshooting

### Authentication Failed

**Problem:** `SMTPAuthenticationError` when sending emails

**Solutions:**
1. Make sure you're using an **App Password**, not your regular Gmail password
2. Verify that 2-Step Verification is enabled on your Google account
3. Check that the App Password was copied correctly (no spaces)

### Email Not Received

**Problem:** Test email not arriving in inbox

**Solutions:**
1. Check your spam/junk folder
2. Verify the recipient email address is correct
3. Check your internet connection
4. Verify SMTP server and port settings:
   - Gmail: `smtp.gmail.com:587`
   - Outlook: `smtp-mail.outlook.com:587`
   - Yahoo: `smtp.mail.yahoo.com:587`

### Other Email Providers

If you're not using Gmail, update the SMTP settings in your `.env` file:

**Outlook/Hotmail:**
```env
SMTP_SERVER=smtp-mail.outlook.com
SMTP_PORT=587
SMTP_USERNAME=your_email@outlook.com
SMTP_PASSWORD=your_password
```

**Yahoo:**
```env
SMTP_SERVER=smtp.mail.yahoo.com
SMTP_PORT=587
SMTP_USERNAME=your_email@yahoo.com
SMTP_PASSWORD=your_app_password
```

**Custom SMTP:**
```env
SMTP_SERVER=your_smtp_server.com
SMTP_PORT=587
SMTP_USERNAME=your_email@domain.com
SMTP_PASSWORD=your_password
```

## Security Notes

1. **Never commit `.env` file to Git** - it contains sensitive information
2. The `.env` file is already in `.gitignore` - don't remove it
3. For production (Render), add these as environment variables in the Render dashboard
4. App Passwords are safer than regular passwords - use them!

## Production Deployment (Render)

When deploying to Render, add these environment variables in the Render dashboard:

1. Go to your service → Environment
2. Add the following variables:
   - `SMTP_SERVER` = `smtp.gmail.com`
   - `SMTP_PORT` = `587`
   - `SMTP_USERNAME` = `your_email@gmail.com`
   - `SMTP_PASSWORD` = `your_app_password`

## Verification

After configuration:

1. Restart your Flask app
2. Register a new account
3. Check your email for the OTP code
4. Enter the OTP to verify your account

If everything works, you're all set! 🎉

