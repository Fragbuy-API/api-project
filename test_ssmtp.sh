#!/bin/bash
# A simple script to test your SSMTP configuration

# Email settings - change these to match your configuration
EMAIL_TO="david@ngr.ai"  # Change to your email
EMAIL_FROM="api-monitor@qboid.com"
EMAIL_SUBJECT="Test Email from API Monitor"

# Create temporary email file
TEMP_EMAIL="/tmp/test_email.txt"

# Email content
cat > "${TEMP_EMAIL}" << EOF
To: ${EMAIL_TO}
From: ${EMAIL_FROM}
Subject: ${EMAIL_SUBJECT}

This is a test email from the API monitoring system.
If you're receiving this, your SSMTP configuration is working correctly!

Timestamp: $(date)
Server: $(hostname)

EOF

# Send the email using ssmtp
echo "Sending test email to ${EMAIL_TO}..."
cat "${TEMP_EMAIL}" | ssmtp "${EMAIL_TO}"
STATUS=$?

# Check if email was sent successfully
if [ $STATUS -eq 0 ]; then
  echo "✅ Email appears to have been sent successfully (exit code: ${STATUS})"
else
  echo "❌ Failed to send email (exit code: ${STATUS})"
fi

# Clean up
rm -f "${TEMP_EMAIL}"

echo "Done. Check your inbox for the test email."
echo "If you don't receive it, check your server's mail logs:"
echo "  sudo tail -f /var/log/mail.log"