# Debugging Guide - Fantasma Protocol

## Common Errors and Solutions

### 1. MetaMask Errors (Can Ignore)

**Errors**:
```
evmAsk.js:5 Uncaught TypeError: Cannot redefine property: ethereum
MetaMask encountered an error setting the global Ethereum provider
```

**Cause**: MetaMask and other Ethereum wallet extensions trying to inject providers

**Solution**: ✅ **IGNORE THESE** - They don't affect Fantasma functionality
- Fantasma uses Liquid Network, not Ethereum
- These are browser extension conflicts
- No action needed

---

### 2. POST /api/v1/supply 400 (Bad Request)

**Error**: `POST http://localhost:8000/api/v1/supply 400 (Bad Request)`

**Possible Causes**:

#### A. Missing or Invalid Asset Selection
**Symptom**: Error message about asset_id validation

**Solution**:
1. Make sure you selected an asset from the dropdown
2. Check browser console for the actual request payload
3. Verify asset_id is not empty

#### B. Amount Too Small
**Symptom**: Error message "Amount must be at least 1000 satoshis"

**Solution**:
- Minimum amount is 0.00001 (1000 satoshis)
- Enter at least 0.00001 in the form
- Example valid amounts: 0.001, 0.01, 1.0

#### C. Amount Not Integer
**Symptom**: Pydantic validation error about type

**Solution**: ✅ **FIXED** - Amount is now forced to integer
- Frontend now uses `Math.floor()` to ensure integer
- Should work automatically

#### D. Backend Not Running
**Symptom**: Connection refused or network error

**Solution**:
```bash
cd backend
python -m uvicorn src.main:app --reload
```

---

### 3. Debugging Steps

#### Step 1: Check Browser Console

Open DevTools (F12) and look for:
```javascript
Supply request: {
  user_address: "lq1qtest123",
  asset_id: "btc_asset_id_placeholder",
  amount: 100000000
}
```

**What to check**:
- ✅ `asset_id` is not empty
- ✅ `amount` is a number (not string)
- ✅ `amount` >= 1000

#### Step 2: Check Backend Logs

Look at the terminal where backend is running:
```
INFO:     127.0.0.1:xxxxx - "POST /api/v1/supply HTTP/1.1" 400 Bad Request
```

**If you see validation errors**, they'll show the exact field and problem.

#### Step 3: Test API Directly

```bash
# Test with curl
curl -X POST http://localhost:8000/api/v1/supply \
  -H "Content-Type: application/json" \
  -d '{
    "user_address": "lq1qtest123",
    "asset_id": "btc_asset_id_placeholder",
    "amount": 100000000
  }'
```

**Expected Response** (201 Created):
```json
{
  "position_id": 1,
  "user_address": "lq1qtest123",
  "asset_id": "btc_asset_id_placeholder",
  "amount_supplied": 100000000,
  "atoken_amount": 100000000,
  "liquidity_index": 1000000000000000000000000000,
  "tx_id": "simulated_tx_hash..."
}
```

**If this works**, the problem is in the frontend.
**If this fails**, the problem is in the backend.

---

### 4. Frontend Debugging

#### Enable Verbose Logging

The frontend now logs all requests. Check console for:
```javascript
Supply request: { ... }
API Error: <detailed error message>
```

#### Check Network Tab

1. Open DevTools (F12)
2. Go to Network tab
3. Click on the failed `/supply` request
4. Look at:
   - **Request Payload**: What was sent
   - **Response**: What error was returned

#### Common Issues

**Empty asset_id**:
```javascript
// BAD
{ asset_id: "", amount: 100000000 }

// GOOD
{ asset_id: "btc_asset_id_placeholder", amount: 100000000 }
```

**String amount instead of number**:
```javascript
// BAD
{ amount: "100000000" }

// GOOD
{ amount: 100000000 }
```

---

### 5. Backend Debugging

#### Check Validation

The backend validates:
1. `user_address`: 10-100 characters
2. `asset_id`: 10-100 characters (relaxed for MVP)
3. `amount`: integer >= 1000

#### Check Database

```bash
cd backend
sqlite3 fantasma.db

# Check if reserve exists
SELECT * FROM reserve_states;

# Check if user exists
SELECT * FROM users;

# Check positions
SELECT * FROM supply_positions;
```

#### Check Logs

Backend logs everything:
```
INFO: Supply request: user=lq1qtest123, asset=btc_asse..., amount=100000000
INFO: Supply: user=lq1qtest123, asset=btc_asse..., amount=100000000, atoken_amount=100000000
INFO: Supply transaction broadcast: simulated_tx_hash...
```

---

### 6. Quick Fixes

#### Fix 1: Restart Backend

```bash
# Stop with Ctrl+C
cd backend
python -m uvicorn src.main:app --reload
```

#### Fix 2: Clear Browser Cache

```
Ctrl+Shift+R (Windows/Linux)
Cmd+Shift+R (Mac)
```

#### Fix 3: Reinstall Frontend Dependencies

```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
npm start
```

#### Fix 4: Reset Database

```bash
cd backend
rm fantasma.db
alembic upgrade head
python -m uvicorn src.main:app --reload
```

---

### 7. Verification Checklist

Before reporting a bug, verify:

- [ ] Backend is running (`http://localhost:8000/health` returns OK)
- [ ] Frontend is running (`http://localhost:3000` loads)
- [ ] Browser console shows no CORS errors
- [ ] Asset is selected in dropdown
- [ ] Amount is >= 0.00001
- [ ] Network tab shows request was sent
- [ ] Backend logs show request received

---

### 8. Getting Help

If still stuck, provide:

1. **Browser console output** (full error)
2. **Backend logs** (terminal output)
3. **Network tab** (request/response)
4. **Steps to reproduce**
5. **What you expected**
6. **What actually happened**

---

## Summary

**Most Common Issues**:
1. ✅ MetaMask errors → Ignore them
2. ✅ 400 Bad Request → Check asset selection and amount
3. ✅ Backend not running → Start it
4. ✅ Frontend errors → Check console

**Quick Test**:
```bash
# 1. Backend health
curl http://localhost:8000/health

# 2. Supply test
curl -X POST http://localhost:8000/api/v1/supply \
  -H "Content-Type: application/json" \
  -d '{"user_address":"lq1qtest123","asset_id":"btc_asset_id_placeholder","amount":100000000}'

# 3. Check positions
curl http://localhost:8000/api/v1/positions/lq1qtest123
```

If all three work, the backend is fine. Problem is in frontend.
