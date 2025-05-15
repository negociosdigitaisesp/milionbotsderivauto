# Supabase Email Confirmation Setup Guide

This document explains how to properly configure Supabase to send email confirmations and handle authentication callbacks.

## 1. Create .env.local File

Create a `.env.local` file in the project root with your Supabase credentials:

```
# Supabase Configuration
VITE_SUPABASE_URL=https://xzbuustfkngfonlpsoxw.supabase.co
VITE_SUPABASE_ANON_KEY=sbp_df3e13a68890ee4a89520de955941bfb6ba56ca1
VITE_SITE_URL=http://localhost:5173
```

## 2. Configure Supabase Project Settings

Follow these steps in your Supabase dashboard:

### Authentication Settings

1. Go to **Authentication > Settings**
2. Under **Email Auth**, ensure the following are enabled:
   - Email signup
   - "Confirm email" checkbox should be ON
   - "Secure email change" should be ON

### URL Configuration

1. Go to **Authentication > URL Configuration**
2. Set **Site URL** to your production URL or `http://localhost:5173` for development
3. Add the following URLs to **Redirect URLs**:
   - `http://localhost:5173/auth/callback` (for development)
   - `https://your-domain.com/auth/callback` (for production)

### Email Template Settings

Customize the email templates in **Authentication > Email Templates**:
- Ensure the **Confirmation** template is properly configured
- Test the template to make sure emails are sending correctly

## 3. SMTP Configuration (Optional but Recommended)

For production use, configure a custom SMTP server:

1. Go to **Project Settings > General**
2. Scroll down to **Email Auth**
3. Click **Enable Custom SMTP**
4. Enter your SMTP server details:
   - Host (e.g., `smtp.gmail.com`)
   - Port (e.g., `587`)
   - Username & Password
   - Sender Name & Email

## 4. Troubleshooting

If email confirmations are not working:

1. **Check Logs**: Go to **Database > Logs** to see authentication events
2. **Verify Email Delivery**: Check spam folders and mail server logs
3. **Test with Supabase CLI**: Use `supabase email test` to verify email settings
4. **Verify URL Configurations**: Make sure all URLs are correct and accessible
5. **Check Rate Limits**: Be aware of Supabase's email sending limits

## 5. Debug Mode

To enable more detailed logging:

1. Add `VITE_SUPABASE_DEBUG=true` to your `.env.local` file
2. Check browser console for detailed authentication logs
3. Restart your development server

## Note About Demo Mode

If the application detects missing or invalid Supabase credentials, it will automatically fall back to "Demo Mode" where authentication is simulated locally without requiring email confirmations. This is useful for development and testing but should not be used in production. 