# Frontend Troubleshooting Guide

## Common Issues

### 1. "process is not defined" Error

**Problem**: Using `process.env` in Vite project

**Solution**: ✅ Fixed! Use `import.meta.env` instead
- Changed `process.env.REACT_APP_API_URL` to `import.meta.env.VITE_API_URL`
- Created `src/vite-env.d.ts` for TypeScript types

### 2. Blank Page / Nothing Appears

**Causes**:
- Backend not running
- API connection error
- Environment variables not set

**Solutions**:

1. **Check Backend is Running**:
   ```bash
   # In backend directory
   uvicorn src.main:app --reload
   ```
   Should see: `Uvicorn running on http://127.0.0.1:8000`

2. **Create .env file**:
   ```bash
   cd frontend
   cp .env.example .env
   ```
   
   Content of `.env`:
   ```env
   VITE_API_URL=http://localhost:8000/api/v1
   VITE_NETWORK=regtest
   ```

3. **Restart Vite**:
   ```bash
   # Stop with Ctrl+C, then:
   npm start
   ```

### 3. MetaMask Errors (Can be Ignored)

**Errors**:
```
evmAsk.js:5 Uncaught TypeError: Cannot redefine property: ethereum
MetaMask encountered an error setting the global Ethereum provider
```

**Cause**: MetaMask extension conflicts (normal for non-EVM apps)

**Solution**: These can be safely ignored. Fantasma uses Liquid Network, not Ethereum.

### 4. API Connection Failed

**Error in Console**:
```
GET http://localhost:8000/api/v1/positions/... net::ERR_CONNECTION_REFUSED
```

**Solution**:
1. Verify backend is running on port 8000
2. Check `.env` has correct `VITE_API_URL`
3. Test backend directly: http://localhost:8000/docs

### 5. TypeScript Errors

**Problem**: Red squiggly lines, type errors

**Solution**:
```bash
# Reinstall dependencies
rm -rf node_modules package-lock.json
npm install

# Check TypeScript
npx tsc --noEmit
```

### 6. TailwindCSS Not Working

**Problem**: Styles not applied, classes not working

**Solution**:
1. Check `tailwind.config.js` exists
2. Check `postcss.config.js` exists
3. Restart dev server
4. Clear browser cache (Ctrl+Shift+R)

## Verification Steps

### 1. Backend Health Check
```bash
curl http://localhost:8000/health
# Expected: {"status":"healthy"}
```

### 2. API Docs
Visit: http://localhost:8000/docs
Should see Swagger UI with endpoints

### 3. Frontend Dev Server
```bash
npm start
# Should see:
# VITE v5.x.x  ready in xxx ms
# ➜  Local:   http://localhost:3000/
```

### 4. Browser Console
Open DevTools (F12), check Console tab:
- ✅ No red errors (except MetaMask - ignore those)
- ✅ See "Download the React DevTools" message
- ✅ API calls to http://localhost:8000

## Environment Setup Checklist

- [ ] Node.js 18+ installed (`node --version`)
- [ ] Python 3.11+ installed (`python --version`)
- [ ] Backend dependencies installed (`pip install -r requirements.txt`)
- [ ] Frontend dependencies installed (`npm install`)
- [ ] Database migrated (`alembic upgrade head`)
- [ ] Backend running (`uvicorn src.main:app --reload`)
- [ ] `.env` file created in frontend directory
- [ ] Frontend running (`npm start`)

## Quick Reset

If everything is broken:

```bash
# Backend
cd backend
rm fantasma.db
alembic upgrade head
uvicorn src.main:app --reload

# Frontend (new terminal)
cd frontend
rm -rf node_modules package-lock.json
npm install
npm start
```

## Getting Help

1. Check browser console (F12)
2. Check backend logs in terminal
3. Verify all services running:
   - Backend: http://localhost:8000/health
   - Frontend: http://localhost:3000
4. Review `IMPLEMENTATION_STATUS.md`
5. Check `QUICKSTART.md`

## Known Limitations

- ⚠️ No wallet integration yet (uses hardcoded address)
- ⚠️ No actual UTXO transactions (coordinator not implemented)
- ⚠️ MetaMask errors are normal (Liquid ≠ Ethereum)
- ⚠️ Positions may be empty (need to supply assets first)
