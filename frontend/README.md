# Billau - Frontend

React + TypeScript frontend for the Billau UTXO lending protocol.

## Tech Stack

- **React 18** - UI library
- **TypeScript** - Type safety
- **Vite** - Build tool
- **TailwindCSS** - Styling
- **React Query** - Data fetching
- **Axios** - HTTP client

## Setup

```bash
# Install dependencies
npm install

# Copy environment variables
cp .env.example .env

# Start development server
npm start
```

The app will run on http://localhost:3000

## Available Scripts

- `npm start` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm test` - Run tests
- `npm run lint` - Lint code
- `npm run format` - Format code

## Project Structure

```
src/
├── components/      # React components
│   ├── SupplyForm.tsx
│   └── PositionCard.tsx
├── pages/          # Page components
│   └── Supply.tsx
├── hooks/          # Custom React hooks
│   └── usePositions.ts
├── services/       # API client
│   └── api.ts
├── main.tsx        # Entry point
└── index.css       # Global styles
```

## Features

- **Supply Assets**: Deposit BTC/USDT to earn interest
- **View Positions**: See your aToken holdings and accrued interest
- **Real-time Updates**: Positions refresh every 30 seconds
- **Responsive Design**: Works on desktop and mobile

## Environment Variables

Create a `.env` file:

```env
REACT_APP_API_URL=http://localhost:8000/api/v1
REACT_APP_NETWORK=regtest
```

## Development

The frontend connects to the backend API at `http://localhost:8000`.

Make sure the backend is running:

```bash
cd ../backend
uvicorn src.main:app --reload
```

## Building for Production

```bash
npm run build
```

Output will be in the `dist/` directory.
