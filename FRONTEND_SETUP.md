# A.V.A.R. Frontend - Complete Setup Guide

## Overview

The A.V.A.R. (Anti-AI Verification and Adjudication Registry) frontend is a modern, fully-functional Vue 3 application integrated with the backend microservices architecture. It provides a complete user interface for browsing competitions, submitting photos, and managing submissions.

## Technology Stack

### Core Technologies
- **Vue 3** (v3.5.23) - Progressive JavaScript framework with Composition API
- **Vite** (v7.2.2) - Next-generation frontend build tool
- **TypeScript** - Type-safe development
- **Vue Router** (v4.6.3) - Official routing library
- **Pinia** (v3.0.4) - State management

### UI & Styling
- **Tailwind CSS** (v3.4.1) - Utility-first CSS framework
- **shadcn-vue** (v2.3.2) - Beautiful, accessible UI components
- **Radix Vue** (v1.9.17) - Unstyled, accessible component primitives
- **Lucide Vue Next** - Icon library

### API & State
- **Axios** (v1.13.2) - HTTP client for API requests
- **@vueuse/core** (v14.0.0) - Collection of Vue composition utilities

## Project Structure

```
src/frontend/
├── src/
│   ├── api/                    # API client and service modules
│   │   ├── client.ts          # Axios client with interceptors
│   │   ├── auth.ts            # Authentication API
│   │   ├── competitions.ts    # Competitions API
│   │   ├── submissions.ts     # Submissions API
│   │   └── index.ts           # API exports
│   │
│   ├── components/            # Reusable components
│   │   ├── ui/               # shadcn-vue components
│   │   │   ├── button/
│   │   │   ├── card/
│   │   │   ├── input/
│   │   │   ├── label/
│   │   │   ├── textarea/
│   │   │   ├── alert/
│   │   │   ├── badge/
│   │   │   ├── avatar/
│   │   │   ├── dropdown-menu/
│   │   │   └── separator/
│   │   └── Layout.vue        # Main layout with navigation
│   │
│   ├── stores/               # Pinia state management
│   │   ├── auth.ts          # Authentication store
│   │   ├── competitions.ts  # Competitions store
│   │   └── submissions.ts   # Submissions store
│   │
│   ├── types/               # TypeScript type definitions
│   │   └── index.ts        # All types (User, Competition, Submission, etc.)
│   │
│   ├── views/              # Page components
│   │   ├── Home.vue       # Landing page
│   │   ├── Login.vue      # Login page
│   │   ├── Register.vue   # Registration page
│   │   ├── Competitions.vue        # Competitions listing
│   │   ├── CompetitionDetail.vue   # Competition details
│   │   ├── Submit.vue              # Submission form
│   │   └── MySubmissions.vue       # User's submissions
│   │
│   ├── lib/               # Utility functions
│   │   └── utils.ts      # Helper functions (cn, etc.)
│   │
│   ├── App.vue           # Root component
│   ├── main.ts           # Application entry point
│   ├── style.css         # Global styles with Tailwind directives
│   └── vite-env.d.ts     # TypeScript declarations
│
├── public/               # Static assets
├── dist/                # Production build output
│
├── .env.development     # Development environment variables
├── .env.production      # Production environment variables
├── components.json      # shadcn-vue configuration
├── Dockerfile          # Multi-stage Docker build
├── nginx.conf          # Nginx configuration for production
├── package.json        # Dependencies and scripts
├── pnpm-lock.yaml     # Lock file
├── postcss.config.js  # PostCSS configuration
├── tailwind.config.js # Tailwind CSS configuration
├── tsconfig.json      # TypeScript configuration
├── vite.config.ts     # Vite configuration
└── README.md          # Frontend-specific documentation
```

## Features Implemented

### 1. Authentication System
- **User Registration** ([Register.vue](src/views/Register.vue))
  - Email, username, password fields
  - Optional fields: full name, country
  - Client-side validation
  - Automatic login after registration

- **User Login** ([Login.vue](src/views/Login.vue))
  - Email and password authentication
  - JWT token management
  - Auto-redirect to previous page after login

- **Auth Store** ([stores/auth.ts](src/stores/auth.ts))
  - JWT token storage in localStorage
  - Automatic token refresh on 401 errors
  - Current user state management
  - Login/logout/register actions

### 2. Competition System
- **Competition Listing** ([Competitions.vue](src/views/Competitions.vue))
  - Grid view of all active competitions
  - Status badges (Open, Closed, Judging, etc.)
  - Filter by status
  - Pagination support
  - Competition metadata display

- **Competition Details** ([CompetitionDetail.vue](src/views/CompetitionDetail.vue))
  - Full competition information
  - Submission requirements
  - Rules and guidelines
  - Deadline information
  - Prize details
  - Submit button (with auth check)

- **Competitions Store** ([stores/competitions.ts](src/stores/competitions.ts))
  - Fetch all competitions
  - Fetch by ID or slug
  - Create/update/delete (for organizers)
  - Current competition state

### 3. Submission System
- **Submit Photo** ([Submit.vue](src/views/Submit.vue))
  - Title and description fields
  - JPG file upload (required)
  - RAW file upload (optional or required based on competition)
  - File validation
  - Progress indication

- **My Submissions** ([MySubmissions.vue](src/views/MySubmissions.vue))
  - Grid view of user's submissions
  - Status badges (Pending, Analyzing, Approved, Rejected)
  - Verification verdict display
  - Confidence score
  - Camera metadata
  - Judging scores
  - Competition information

- **Submissions Store** ([stores/submissions.ts](src/stores/submissions.ts))
  - Create submission with file upload
  - Fetch user's submissions
  - Fetch by competition
  - Delete submission
  - Current submission state

### 4. Navigation & Layout
- **Layout Component** ([components/Layout.vue](src/components/Layout.vue))
  - Sticky header with navigation
  - Logo and branding
  - Auth-aware menu (different for logged-in/out users)
  - User dropdown menu with avatar
  - Footer
  - Responsive design

- **Navigation Links:**
  - Home / Landing page
  - Competitions
  - My Submissions (auth required)
  - Login / Sign Up (guest only)
  - User menu (logged in users)

### 5. Home/Landing Page
- **Hero Section**
  - A.V.A.R. branding
  - Value proposition
  - CTA buttons

- **Features Section**
  - AI Detection
  - Fair Competition
  - Professional Judging

- **How It Works**
  - 4-step process explanation
  - Visual steps with numbers

- **Call to Action**
  - Sign-up prompt

### 6. API Integration
- **API Client** ([api/client.ts](src/api/client.ts))
  - Axios instance with base URL
  - Request interceptor for auth tokens
  - Response interceptor for error handling
  - Automatic token refresh on 401
  - 30-second timeout

- **API Services:**
  - Authentication API ([api/auth.ts](src/api/auth.ts))
    - register, login, getCurrentUser, logout
  - Competitions API ([api/competitions.ts](src/api/competitions.ts))
    - getAll, getById, getBySlug, create, update, delete
  - Submissions API ([api/submissions.ts](src/api/submissions.ts))
    - getAll, getById, create (with FormData), delete

### 7. Type Safety
- **TypeScript Types** ([types/index.ts](src/types/index.ts))
  - User, UserRegister, UserLogin, TokenResponse
  - Competition, CompetitionCreate, CompetitionUpdate
  - Submission, SubmissionCreate
  - Score
  - API response types
  - Error types

### 8. Routing
- **Vue Router Configuration** ([main.ts](src/main.ts))
  - Home (/)
  - Login (/login)
  - Register (/register)
  - Competitions (/competitions)
  - Competition Detail (/competitions/:id)
  - Submit (/submit/:competitionId) - Auth required
  - My Submissions (/my-submissions) - Auth required

- **Navigation Guards:**
  - Auto-fetch current user if token exists
  - Redirect to login for protected routes
  - Preserve redirect URL

### 9. UI Components (shadcn-vue)
- Button - Various variants and sizes
- Card - Container with header, content, footer
- Input - Text input fields
- Label - Form labels
- Textarea - Multi-line text input
- Alert - Alert messages with variants
- Badge - Status indicators
- Avatar - User avatars with fallback
- Dropdown Menu - User menu with items
- Separator - Visual dividers

## Environment Variables

### Development ([.env.development](src/frontend/.env.development))
```env
VITE_API_BASE_URL=http://localhost:8080/api/v1
VITE_API_GATEWAY_URL=http://localhost:8000/api/v1
VITE_AI_DETECTION_URL=http://localhost:8001/api/v1
VITE_APP_NAME=A.V.A.R. - Anti-AI Verification and Adjudication Registry
VITE_APP_ENV=development
```

### Production ([.env.production](src/frontend/.env.production))
```env
VITE_API_BASE_URL=http://competition-service:8080/api/v1
VITE_API_GATEWAY_URL=http://api-gateway:8000/api/v1
VITE_AI_DETECTION_URL=http://ai-detection-service:8001/api/v1
VITE_APP_NAME=A.V.A.R. - Anti-AI Verification and Adjudication Registry
VITE_APP_ENV=production
```

## Docker Setup

### Dockerfile ([Dockerfile](src/frontend/Dockerfile))

Multi-stage build with three targets:

1. **Development Stage**
   - Node 20 Alpine
   - pnpm package manager
   - Hot reload with Vite dev server
   - Port 5173

2. **Build Stage**
   - Optimized production build
   - TypeScript compilation
   - Asset optimization

3. **Production Stage**
   - Nginx Alpine
   - Serves static files from /dist
   - Custom nginx configuration
   - Port 80
   - Health check endpoint

### Nginx Configuration ([nginx.conf](src/frontend/nginx.conf))
- SPA routing (all routes serve index.html)
- Gzip compression
- Security headers
- Static asset caching (1 year)
- Health check endpoint
- Hidden files protection

### Docker Compose Integration

The frontend is already configured in the main [docker-compose.yml](../../docker-compose.yml):

```yaml
# Production frontend (port 3000:80)
frontend:
  build:
    context: ./src/frontend
    dockerfile: Dockerfile
    target: production
  container_name: avar-frontend
  ports:
    - "3000:80"
  depends_on:
    - api-gateway
    - competition-service
  networks:
    - avar-network
  healthcheck:
    test: ["CMD-SHELL", "wget --no-verbose --tries=1 --spider http://localhost/ || exit 1"]
    interval: 30s
    timeout: 10s
    retries: 3
  restart: unless-stopped

# Development frontend (port 5173:5173)
frontend-dev:
  build:
    context: ./src/frontend
    dockerfile: Dockerfile
    target: development
  container_name: avar-frontend-dev
  environment:
    - VITE_API_URL=http://localhost:8080
    - VITE_AI_DETECTION_URL=http://localhost:8001
  ports:
    - "5173:5173"
  volumes:
    - ./src/frontend:/app
    - /app/node_modules
  depends_on:
    - api-gateway
    - competition-service
  networks:
    - avar-network
  restart: unless-stopped
  profiles:
    - development
```

## Getting Started

### Prerequisites
- Node.js 20 or higher
- pnpm (or npm/yarn)

### Local Development

1. **Install dependencies:**
   ```bash
   cd src/frontend
   pnpm install
   ```

2. **Start development server:**
   ```bash
   pnpm dev
   ```
   Access at: http://localhost:5173

3. **Build for production:**
   ```bash
   pnpm build
   ```

4. **Preview production build:**
   ```bash
   pnpm preview
   ```

### Docker Development

1. **Start with development profile:**
   ```bash
   docker-compose --profile development up frontend-dev
   ```

2. **Build and start production:**
   ```bash
   docker-compose up --build frontend
   ```

### Full Stack Docker

1. **Start all services:**
   ```bash
   docker-compose up -d
   ```

2. **Access the application:**
   - Frontend: http://localhost:3000
   - API Gateway: http://localhost:8000
   - Competition Service: http://localhost:8080
   - AI Detection Service: http://localhost:8001

3. **View logs:**
   ```bash
   docker-compose logs -f frontend
   ```

4. **Stop all services:**
   ```bash
   docker-compose down
   ```

## Available Scripts

```bash
# Development
pnpm dev              # Start dev server with hot reload
pnpm build           # Build for production
pnpm preview         # Preview production build locally

# Adding Components
pnpm dlx shadcn-vue@latest add <component-name>
```

## API Integration

### Base URLs

The frontend connects to the backend services via environment variables:

**Local Development:**
- Competition Service: `http://localhost:8080/api/v1`
- API Gateway: `http://localhost:8000/api/v1`

**Docker Production:**
- Competition Service: `http://competition-service:8080/api/v1`
- API Gateway: `http://api-gateway:8000/api/v1`

### Authentication Flow

1. User logs in via [Login.vue](src/views/Login.vue)
2. Backend returns `{ access_token, refresh_token, user }`
3. Tokens stored in localStorage
4. All subsequent API requests include `Authorization: Bearer <token>` header
5. On 401 response, tokens are cleared and user redirected to login

### API Error Handling

- Network errors: Display error message
- 401 Unauthorized: Clear tokens, redirect to login
- 400 Bad Request: Show validation errors
- 500 Server Error: Show generic error message

## Styling & Theming

### Tailwind Configuration

The project uses Tailwind CSS with custom theme configuration in [tailwind.config.js](tailwind.config.js):

- Custom color palette (primary, secondary, destructive, etc.)
- CSS variables for theme colors
- Dark mode support (class-based)
- Custom border radius values
- Animations (accordion, etc.)

### CSS Variables

Defined in [src/style.css](src/style.css):

- Light theme (default)
- Dark theme (.dark class)
- HSL color format for easy theming

### Component Styling

All components use Tailwind utility classes with shadcn-vue's design system:

- Consistent spacing
- Responsive design (sm, md, lg breakpoints)
- Hover states
- Focus states
- Disabled states

## Adding New Features

### Adding a New Page

1. Create view component in `src/views/`
2. Add route in `src/main.ts`
3. Add navigation link in `src/components/Layout.vue` (if needed)
4. Update types in `src/types/index.ts` (if needed)

### Adding a New API Endpoint

1. Add function to appropriate service in `src/api/`
2. Add types to `src/types/index.ts`
3. Add store action in `src/stores/` (if needed)

### Adding a New UI Component

```bash
# Using shadcn-vue CLI
pnpm dlx shadcn-vue@latest add <component-name>

# Or create custom component in src/components/
```

## Testing

### Manual Testing Checklist

- [ ] User can register a new account
- [ ] User can log in with credentials
- [ ] User can browse competitions
- [ ] User can view competition details
- [ ] Authenticated user can submit photos
- [ ] User can view their submissions
- [ ] Status badges display correctly
- [ ] File upload works for JPG and RAW files
- [ ] Navigation works (all links functional)
- [ ] Responsive design works on mobile/tablet/desktop
- [ ] Error messages display correctly
- [ ] Loading states display correctly

### Testing with Backend

1. Start backend services:
   ```bash
   docker-compose up -d postgres redis ai-detection-service competition-service api-gateway
   ```

2. Start frontend:
   ```bash
   cd src/frontend
   pnpm dev
   ```

3. Test complete flow:
   - Register new user
   - Browse competitions
   - Submit a photo
   - View submission status

## Troubleshooting

### Build Issues

**Problem:** Build fails with TypeScript errors
```bash
# Solution: Check for unused variables, fix types
pnpm run build
```

**Problem:** Missing dependencies
```bash
# Solution: Reinstall dependencies
rm -rf node_modules pnpm-lock.yaml
pnpm install
```

### API Issues

**Problem:** CORS errors
- Ensure backend CORS_ORIGINS includes frontend URL
- Check backend .env file

**Problem:** 401 Unauthorized
- Clear localStorage and re-login
- Check JWT_SECRET_KEY matches between services

**Problem:** Cannot connect to backend
- Check backend services are running
- Verify API_BASE_URL in .env file
- Check docker network connectivity

### Docker Issues

**Problem:** Frontend container won't start
```bash
# Solution: Rebuild container
docker-compose build frontend
docker-compose up frontend
```

**Problem:** Cannot access on port 3000
- Check if port is already in use
- Verify port mapping in docker-compose.yml

## Performance Optimization

### Bundle Size

Current production build:
- Total JS: ~250 KB (gzipped: ~88 KB)
- Total CSS: ~20 KB (gzipped: ~4.5 KB)
- Lazy-loaded routes for code splitting

### Optimizations Implemented

1. **Code Splitting**
   - Routes lazy-loaded with dynamic imports
   - Component-level chunking

2. **Asset Optimization**
   - Vite's built-in minification
   - Tree-shaking for unused code
   - CSS purging via Tailwind

3. **Caching**
   - Static assets cached for 1 year (nginx)
   - Service worker ready (can be added)

4. **Network**
   - Gzip compression enabled
   - HTTP/2 support via nginx

## Security Considerations

### Implemented

1. **Authentication**
   - JWT tokens with expiration
   - HttpOnly cookies ready (can switch from localStorage)
   - Automatic token refresh

2. **API Security**
   - CORS configuration
   - Request timeouts (30s)
   - Input validation on frontend

3. **Headers (nginx)**
   - X-Frame-Options: SAMEORIGIN
   - X-Content-Type-Options: nosniff
   - X-XSS-Protection: 1; mode=block

### Recommendations

1. Switch from localStorage to httpOnly cookies for tokens
2. Implement Content Security Policy (CSP)
3. Add rate limiting on sensitive endpoints
4. Implement HTTPS in production
5. Add input sanitization library (DOMPurify)

## Future Enhancements

### Planned Features

1. **User Profile Management**
   - Edit profile
   - Change password
   - Avatar upload

2. **Advanced Filtering**
   - Filter competitions by status, date, prize
   - Search competitions
   - Sort options

3. **Submission Management**
   - Edit submission details
   - Delete submissions
   - View verification details modal

4. **Judging Interface** (for judges)
   - View assigned competitions
   - Score submissions
   - Add comments

5. **Organizer Dashboard** (for organizers)
   - Create competitions
   - Manage submissions
   - Assign judges
   - View analytics

6. **Notifications**
   - Real-time updates (WebSocket)
   - Email notifications
   - In-app notification center

7. **Social Features**
   - Follow photographers
   - Like submissions
   - Comments on submissions

8. **Advanced Analytics**
   - User statistics dashboard
   - Competition performance metrics
   - Submission trends

## Support & Documentation

### Related Documentation
- [Main README](../../README.md) - Project overview
- [Backend API Documentation](../../docs/API.md) - API endpoints
- [Docker Setup Guide](../../docs/DOCKER.md) - Docker configuration

### Component Documentation
- [shadcn-vue](https://www.shadcn-vue.com/) - UI components
- [Vue 3](https://vuejs.org/) - Vue framework
- [Vite](https://vitejs.dev/) - Build tool
- [Tailwind CSS](https://tailwindcss.com/) - Styling

### Getting Help
- Check existing issues on GitHub
- Review API documentation
- Check browser console for errors
- Review Docker logs

## Contributors

Built with Vue 3, shadcn-vue, and Tailwind CSS for the A.V.A.R. project.

## License

[Add your license information here]

---

**Last Updated:** November 7, 2024
**Version:** 1.0.0
**Status:** Production Ready ✅
