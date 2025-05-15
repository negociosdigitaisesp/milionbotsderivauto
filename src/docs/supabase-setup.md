# Supabase Configuration Guide

## Initial Setup

1. Create a Supabase project at [https://app.supabase.co](https://app.supabase.co)
2. After creating your project, go to the Settings > API section to get your Project URL and anon/public key
3. Add these credentials to your `.env.local` file:

```
VITE_SUPABASE_URL=https://xzbuustfkngfonlpsoxw.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inh6YnV1c3Rma25nZm9ubHBzb3h3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDcyNjUxMjQsImV4cCI6MjA2Mjg0MTEyNH0.365xmSmpBypdRCAycYMlzcQW0OtCsifdazKfBYGiL1M
VITE_SUPABASE_DEBUG=true
```

## Database Setup

Run the provided `full-database-setup.sql` script in the SQL Editor within your Supabase dashboard to set up all necessary tables, triggers, and policies.

## Authentication Configuration

### Configure Email Authentication

1. Go to Authentication > Providers in your Supabase dashboard
2. Ensure Email provider is enabled
3. Configure the following settings:
   - Set "Confirm email" to ON
   - Set "Secure email change" to ON
   - Set "Double confirm changes" to ON to improve security

### Configure Email Templates

1. Go to Authentication > Email Templates
2. Customize the following templates:
   - Confirmation Email
   - Invite Email
   - Magic Link Email
   - Reset Password Email
   - Change Email Address
   
Make sure to update the branding, colors, and text to match your application.

### Configure Site URL and Redirect URLs

1. Go to Authentication > URL Configuration
2. Set Site URL to your production URL (e.g., `https://yourapp.com`)
3. Add Redirect URLs:
   - `http://localhost:5173/auth/callback` (for development)
   - `http://localhost:3000/auth/callback` (for development with different port)
   - `https://yourapp.com/auth/callback` (for production)

This is crucial for the authentication flow to work properly.

## Enabling Row Level Security (RLS)

Row Level Security is already configured in the database setup script, but ensure that:

1. RLS is enabled for all tables
2. Appropriate policies are in place as defined in the setup script
3. Test the policies to ensure users can only access their own data

## Environment Variables

Make sure your production environment has the following variables set:

```
VITE_SUPABASE_URL=your_supabase_url
VITE_SUPABASE_ANON_KEY=your_anon_key
```

## Troubleshooting Common Issues

### "Auth session or user missing" Error

This error typically occurs when:

1. The user session token is invalid or expired
2. The Supabase URL or API key is incorrect in your `.env.local` file
3. The authentication flow is interrupted

Solutions:
- Clear browser local storage and cookies
- Ensure your Supabase URL and anon key match exactly what's in your Supabase dashboard
- Check if your redirect URLs are properly configured
- Enable debugging with `VITE_SUPABASE_DEBUG=true` to see detailed logs

### Email Confirmation Not Working

If users aren't receiving confirmation emails:

1. Check the spam folder
2. Verify email templates are correctly set up
3. Ensure the Site URL and Redirect URLs are properly configured
4. Test the email provider settings

## Security Best Practices

1. Always use environment variables for Supabase credentials
2. Never expose your service_role key in client-side code
3. Implement proper Row Level Security policies
4. Use the PKCE auth flow for added security (already configured in the code)
5. Refresh tokens periodically

## Additional Resources

- [Supabase Auth Documentation](https://supabase.com/docs/guides/auth)
- [Supabase Row Level Security Guide](https://supabase.com/docs/guides/auth/row-level-security)
- [Supabase TypeScript Client Reference](https://supabase.com/docs/reference/javascript/typescript-support) 