# Email Configuration Guide

To enable OTP email sending, you need to configure SMTP settings.

## Quick Setup

1. Create a `.env` file in the project root directory
2. Add the following configuration:

```env
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
```

## Gmail Setup (Recommended)

### Step 1: Enable 2-Step Verification
1. Go to your Google Account settings
2. Navigate to **Security**
3. Enable **2-Step Verification**

### Step 2: Generate App Password
1. Go to: https://myaccount.google.com/apppasswords
2. Select **Mail** and **Other (Custom name)**
3. Enter "Health Food Monitor" as the name
4. Click **Generate**
5. Copy the 16-character password (no spaces)

### Step 3: Configure .env File
```env
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=xxxx xxxx xxxx xxxx
```
*(Remove spaces from the app password when pasting)*

## Other Email Providers

### Outlook/Hotmail
```env
SMTP_SERVER=smtp-mail.outlook.com
SMTP_PORT=587
SMTP_USERNAME=your_email@outlook.com
SMTP_PASSWORD=your_password
```

### Yahoo Mail
```env
SMTP_SERVER=smtp.mail.yahoo.com
SMTP_PORT=587
SMTP_USERNAME=your_email@yahoo.com
SMTP_PASSWORD=your_app_password
```

## Testing

After configuration:
1. Restart your Flask application
2. Register a new user
3. Check your email inbox (and spam folder) for the OTP

## Troubleshooting

- **Authentication Error**: Make sure you're using an App Password (not your regular password) for Gmail
- **Connection Error**: Check your firewall/antivirus settings
- **OTP not received**: Check spam folder, verify SMTP settings are correct
- **Still not working**: The OTP will be displayed on the verification page as a fallback

## Development Mode

If email is not configured, the OTP will automatically be displayed on the verification page, so you can still test the application without email setup.

