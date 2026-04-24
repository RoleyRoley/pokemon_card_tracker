# Pokemon Card Price Tracker - Frontend

A simple React frontend for searching Pokemon card prices from eBay listings.

## Quick Start

1. **Install dependencies**
   ```bash
   npm install
   ```

2. **Start development server**
   ```bash
   npm run dev
   ```
   The app will be available at `http://localhost:3000`

3. **Make sure the backend is running** (in a separate terminal)
   ```bash
   cd ..
   uvicorn app.main:app --reload
   ```
   Backend will be running at `http://localhost:8000`

## Features

- Search for Pokemon cards by name
- Filter by condition (raw or graded)
- View price statistics (lowest, highest, average, median)
- Sort results by price
- View both sold and unsold listings
- Direct links to eBay listings

## Build for Production

```bash
npm run build
```

Output will be in the `dist` folder.

## Tech Stack

- React 18
- Vite
- Axios
- CSS (vanilla)
