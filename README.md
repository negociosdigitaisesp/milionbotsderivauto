# Bot Strategy Hub

A web application for managing and optimizing bot strategies across different platforms.

## Features

- User authentication with Supabase
- Create and manage bot strategies 
- Analytics dashboard for bot performance
- Library of bot templates and strategies
- Customizable bot configurations

## Setup Instructions

### Prerequisites

- Node.js 16+ and npm
- A Supabase account (free tier is sufficient)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/your-username/bot-strategy-hub.git
cd bot-strategy-hub
```

2. Install dependencies:
```bash
npm install
```

3. Create a `.env.local` file in the project root with your Supabase credentials:
```
VITE_SUPABASE_URL=https://your-project-url.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key
VITE_SUPABASE_DEBUG=true  # Set to false in production
```

4. Set up your Supabase project:
   - Create a new project at [https://app.supabase.co](https://app.supabase.co)
   - Run the SQL from `full-database-setup.sql` in the SQL Editor
   - Follow the configuration steps in `src/docs/supabase-setup.md`

### Running the Application

Development mode:
```bash
npm run dev
```

Production build:
```bash
npm run build
npm run serve
```

## Authentication System

The authentication system uses Supabase Auth with email confirmation. Key components:

- `src/contexts/AuthContext.tsx` - Manages authentication state
- `src/lib/supabaseClient.ts` - Configures the Supabase client
- `src/pages/AuthCallback.tsx` - Handles login redirects and email confirmation

## Troubleshooting

### Common Issues

**"Auth session or user missing" Error**
- Check that your Supabase URL and anon key are correct in `.env.local`
- Ensure email confirmation is properly configured in Supabase dashboard
- Clear browser cache and local storage
- Enable debug mode with `VITE_SUPABASE_DEBUG=true`

**Email Confirmation Not Working**
- Verify the redirect URLs in Supabase are correctly set up
- Check your email templates in the Supabase dashboard
- Make sure your site URL is correctly configured

## Development Notes

- The application uses React with TypeScript
- Styling is done with Tailwind CSS
- Authentication is handled by Supabase
- State management uses React Context API

## License

MIT

## Deployment to Netlify

When deploying to Netlify, make sure to configure the following environment variables in Netlify's dashboard:

1. `VITE_SUPABASE_URL` - Your Supabase project URL (e.g., https://your-project-id.supabase.co)
2. `VITE_SUPABASE_ANON_KEY` - Your Supabase anon/public key

Additionally, ensure you have Netlify redirects correctly set up in the netlify.toml file for proper SPA routing and authentication callbacks.
