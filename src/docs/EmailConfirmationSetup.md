# Email Confirmation Issue Fix

This document provides step-by-step instructions to fix the email confirmation issue in your Million Bots project.

## 1. Database Setup

First, run the SQL script to properly setup your Supabase database. Your connection details are:

- **Database URL**: postgresql://postgres:@db.xzbuustfkngfonlpsoxw.supabase.co:5432/postgres 
- **Service Role Key**: sbp_df3e13a68890ee4a89520de955941bfb6ba56ca1

You can run the SQL script in two ways:

### Option 1: Using the Supabase Dashboard (Recommended)

1. Go to [Supabase Dashboard](https://app.supabase.com)
2. Select your project
3. Navigate to the SQL Editor
4. Open the file `src/scripts/full-database-setup.sql` from your project
5. Copy the entire contents and paste it into the SQL Editor
6. Click "Run" to execute the SQL statements

### Option 2: Using psql CLI (if available)

If you have PostgreSQL client tools installed:

```bash
psql "postgresql://postgres:@db.xzbuustfkngfonlpsoxw.supabase.co:5432/postgres?password=your_password" -f "src/scripts/full-database-setup.sql"
```

## 2. Configure Supabase Authentication

1. Go to your [Supabase Dashboard](https://app.supabase.com)
2. Select your project
3. Navigate to **Authentication** > **URL Configuration**
4. Set the **Site URL** to: 
   - For development: `http://localhost:5173`
   - For production: your actual domain URL
5. Add the following to **Redirect URLs**:
   - `http://localhost:5173/auth/callback`
   - Your production URL + `/auth/callback` (if applicable)

## 3. Configure Email Templates

1. In the Supabase Dashboard, go to **Authentication** > **Email Templates**
2. Click on the **Confirmation** template
3. Ensure it has:
   - A clear subject line
   - A visible confirmation button
   - Clear instructions
4. Click **Save**

## 4. Create `.env.local` File

Create a file named `.env.local` in the root of your project with the following content:

```
# Supabase Configuration
VITE_SUPABASE_URL=https://xzbuustfkngfonlpsoxw.supabase.co
VITE_SUPABASE_ANON_KEY=your_anon_key_here
VITE_SITE_URL=http://localhost:5173
```

Replace `your_anon_key_here` with your actual anon/public key (not the service role key).

## 5. Verify Authentication Settings

In the Supabase Dashboard:

1. Go to **Authentication** > **Settings**
2. Under **Email Auth**:
   - Ensure "Enable Email Signup" is ON
   - Set "Confirm Email" to ON

## 6. Test the Flow

1. Restart your development server
2. Try registering a new user
3. Check your email for the confirmation link
4. Complete the confirmation process

## Troubleshooting

If you're still having issues:

### Check Email Delivery

1. In Supabase Dashboard, go to **Authentication** > **Users**
2. Verify if users are being created with "email_confirmed_at" as NULL
3. Check your email spam folder for confirmation emails

### Enable SMTP for Production

For reliable email delivery:

1. Go to **Project Settings** > **Authentication**
2. Scroll to **SMTP Settings**
3. Enable and configure with your email provider's details

### Check Logs

1. In Supabase Dashboard, go to **Database** > **Logs**
2. Look for auth-related errors
3. In your application, add `VITE_SUPABASE_DEBUG=true` to your `.env.local` file and check browser console for detailed logs

### Advanced: Test Email Templates

You can test email templates directly through the Supabase API:

```js
await supabase.auth.admin.sendEmail(
  'test@example.com',
  { 
    type: 'signup', 
    email: 'test@example.com' 
  }
)
```

Run this in the browser console while authenticated as an admin to send a test email. 