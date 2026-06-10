# Auth-Gated App Testing Playbook (MAVIS Cloud)

NOTE - Do not be satisfied until you've tested the app completely especially the auth gated pages.
Auth is only enforced when backend `IS_CLOUD=true`. For local (`IS_CLOUD=false`) everything is open.

## Step 1: Create Test User & Session
```bash
mongosh --eval "
use('test_database');
var userId = 'test-user-' + Date.now();
var sessionToken = 'test_session_' + Date.now();
db.users.insertOne({
  user_id: userId,
  email: 'julio.silva2854@gmail.com',
  name: 'Test User',
  picture: 'https://via.placeholder.com/150',
  created_at: new Date()
});
db.user_sessions.insertOne({
  user_id: userId,
  session_token: sessionToken,
  expires_at: new Date(Date.now() + 7*24*60*60*1000),
  created_at: new Date()
});
print('Session token: ' + sessionToken);
print('User ID: ' + userId);
"
```

## Step 2: Test Backend API
```bash
# auth endpoint
curl -X GET "$URL/api/auth/me" -H "Authorization: Bearer YOUR_SESSION_TOKEN"
# password login
curl -X POST "$URL/api/auth/password" -H "Content-Type: application/json" -d '{"password":"<ADMIN_PASSWORD>"}'
```

## Step 3: Browser Testing
```python
await page.context.add_cookies([{
    "name": "session_token", "value": "YOUR_SESSION_TOKEN",
    "domain": "your-app.com", "path": "/",
    "httpOnly": True, "secure": True, "sameSite": "None"
}])
await page.goto("https://your-app.com")
```

## Checklist
- User document has user_id field (custom UUID)
- Session user_id matches user's user_id exactly
- All queries use {"_id": 0} projection
- /api/auth/me returns user data with cookie or Bearer
- Login page shows BOTH Google button and password field
- Email allowlist enforced (non-allowed Google email rejected)
- Public /p/analytics still works WITHOUT login
