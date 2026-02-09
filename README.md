# Stock Search Engine

A full-stack stock search application with advanced filtering and AI-powered search capabilities.

## 🏗️ Architecture

This is a monorepo containing:
- **Frontend**: React SPA with Vite, React Router, and Tailwind CSS
- **Backend**: Flask REST API with BM25 ranking and advanced search

## 🚀 Deployment (Vercel)

### Prerequisites
- GitHub repository connected to Vercel
- Vercel CLI (optional, for local testing)

### Deployment Steps

1. **Push your code to GitHub**
   ```bash
   git add .
   git commit -m "Deploy to Vercel"
   git push origin main
   ```

2. **Configure Vercel Project**
   - Import your repository in Vercel
   - Framework Preset: **Other**
   - Root Directory: **Leave as root** (important!)
   - Build Command: **Leave empty** (Vercel will use the builds config)
   - Output Directory: **Leave empty**

3. **Environment Variables** (Optional for local backend)
   
   In Vercel Dashboard, add environment variable (only if frontend calls external API):
   - `VITE_API_URL` = (leave empty for same-origin deployment)

4. **Deploy**
   - Vercel will automatically deploy on every push to main
   - Check build logs for any errors

### Vercel Configuration

The `vercel.json` file handles:
- ✅ API routes (`/api/*`) → Python backend
- ✅ Static assets with caching
- ✅ SPA fallback routing (all other routes → `index.html`)

This fixes the **page refresh crash issue** that occurs with React Router.

## 🛠️ Local Development

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Run Flask server
flask run
# or
python app_init.py
```

Backend will run on `http://localhost:5000`

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Create .env file for local development (optional)
# Copy .env.example to .env.local
# Set VITE_API_URL=http://localhost:5000 if backend runs separately

# Run development server
npm run dev
```

Frontend will run on `http://localhost:5173`

## 📝 What Was Fixed

### 1. **vercel.json Configuration** ❌ → ✅
   - **Before**: Redirected ALL routes (including `/api/*`) to `/index.html`
   - **After**: 
     - API routes (`/api/*`) → Python backend
     - Static assets → Served with cache headers
     - All other routes → `index.html` (for SPA routing)

### 2. **Frontend API Configuration** ❌ → ✅
   - **Before**: Required `VITE_API_URL` (missing in production)
   - **After**: Defaults to relative paths (`""`) when not set
   - Uses same-origin requests in production

### 3. **Backend API Export** ❌ → ✅
   - **Before**: Flask app not properly exported
   - **After**: Added `handler = app` for Vercel serverless

### 4. **Build Configuration** ❌ → ✅
   - **Before**: Missing build optimizations
   - **After**: 
     - Added `vercel-build` script to `package.json`
     - Configured Vite build options
     - Added development proxy for `/api` calls

### 5. **Environment Files** ❌ → ✅
   - Created `.env.production` with proper settings
   - Updated `.env.example` with correct documentation
   - Added `.env` files to `.gitignore`

## 🔑 Key Features

- 🔍 Advanced stock search with BM25 ranking
- 🤖 AI-powered query interpretation
- 📊 Real-time stock data fetching
- 🔐 User authentication
- 📈 Stock visualization
- 🎨 Modern UI with Tailwind CSS

## 📁 Project Structure

```
├── backend/               # Flask API
│   ├── api.py            # Entry point for Vercel
│   ├── app_init.py       # Flask app initialization
│   ├── routes/           # API routes
│   ├── core/             # Search & ranking logic
│   ├── services/         # Stock data services
│   └── utils/            # Database & utilities
├── frontend/             # React SPA
│   ├── src/
│   │   ├── components/   # React components
│   │   ├── pages/        # Page components
│   │   ├── routes/       # React Router setup
│   │   ├── services/     # API client
│   │   └── hooks/        # Custom hooks
│   └── dist/             # Build output (generated)
└── vercel.json           # Vercel configuration

```

## 🐛 Troubleshooting

### Page crashes on refresh
- ✅ **Fixed**: Updated `vercel.json` routing configuration

### API calls fail in production
- ✅ **Fixed**: API client uses relative paths by default

### 404 errors for routes like `/home`, `/search`
- ✅ **Fixed**: All non-API routes fall back to `index.html`

### CORS errors
- Check `backend/app_init.py` CORS configuration
- Add your Vercel deployment URL to allowed origins if needed

## 📦 Tech Stack

**Frontend:**
- React 19
- React Router 7
- Tailwind CSS 4
- Vite 7
- Axios

**Backend:**
- Flask 3
- Flask-CORS
- yfinance
- pandas
- spaCy

## 📄 License

This project is for educational/personal use.
