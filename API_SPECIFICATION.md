# Google Calendar Backend API 規格文檔

## 概述
這是一個Django REST API後端，提供Google Calendar整合功能，支援用戶認證、日曆事件管理和雙向同步。

## 基本資訊
- **Base URL**: `http://localhost:8000`
- **API版本**: 1.0.0
- **認證方式**: Django Session Authentication + Google OAuth 2.0
- **數據格式**: JSON
- **編碼**: UTF-8

---

## 認證流程

### 快速開始
1. **使用登入頁面** (推薦): 訪問 `http://localhost:8000/login/`
2. **直接API調用**: 按照以下步驟進行

### 1. 獲取Google OAuth URL
```http
GET /auth/google/
```

**響應**:
```json
{
    "auth_url": "https://accounts.google.com/o/oauth2/auth?...",
    "message": "Redirect user to this URL to authenticate with Google"
}
```

### 2. OAuth回調處理
```http
GET /auth/callback/?code=<authorization_code>&state=<state>
```

**響應**:
```json
{
    "message": "Successfully authenticated with Google",
    "user": {
        "id": 1,
        "username": "user@example.com",
        "email": "user@example.com",
        "first_name": "John",
        "last_name": "Doe"
    }
}
```

### 3. 檢查認證狀態
```http
GET /auth/status/
```
**需要認證**: ✅
**注意**: 此端點需要用戶已完成認證，未認證用戶會收到403錯誤

**響應**:
```json
{
    "authenticated": true,
    "user": {
        "id": 1,
        "username": "user@example.com",
        "email": "user@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "is_google_authenticated": true,
        "google_email": "user@gmail.com",
        "token_expires_at": "2025-09-05T10:00:00Z"
    }
}
```

### 4. 刷新Token
```http
POST /auth/refresh/
```
**需要認證**: ✅

**響應**:
```json
{
    "message": "Token refreshed successfully"
}
```

### 5. 登出
```http
POST /auth/logout/
```
**需要認證**: ✅

**響應**:
```json
{
    "message": "Logged out successfully"
}
```

### 6. 撤銷Google存取權限
```http
POST /auth/revoke/
```
**需要認證**: ✅

**響應**:
```json
{
    "message": "Google access revoked successfully"
}
```

---

## 日曆事件管理

### 1. 獲取事件列表
```http
GET /api/events/
```
**需要認證**: ✅

**查詢參數**:
- `start` (optional): ISO 8601格式的開始日期時間
- `end` (optional): ISO 8601格式的結束日期時間

**範例請求**:
```http
GET /api/events/?start=2025-09-01T00:00:00Z&end=2025-09-30T23:59:59Z
```

**響應**:
```json
[
    {
        "id": 1,
        "user": {
            "id": 1,
            "username": "user@example.com",
            "email": "user@example.com",
            "first_name": "John",
            "last_name": "Doe"
        },
        "google_event_id": "abc123def456",
        "title": "團隊會議",
        "description": "每週團隊同步會議",
        "start_datetime": "2025-09-05T14:00:00Z",
        "end_datetime": "2025-09-05T15:00:00Z",
        "location": "會議室A",
        "is_all_day": false,
        "recurrence_rule": null,
        "calendar_id": "primary",
        "status": "confirmed",
        "created_at": "2025-09-04T10:00:00Z",
        "updated_at": "2025-09-04T10:00:00Z",
        "synced_with_google": true,
        "last_synced_at": "2025-09-04T10:00:00Z"
    }
]
```

### 2. 創建事件
```http
POST /api/events/
```
**需要認證**: ✅

**請求體**:
```json
{
    "title": "新會議",
    "description": "會議描述",
    "start_datetime": "2025-09-06T10:00:00Z",
    "end_datetime": "2025-09-06T11:00:00Z",
    "location": "線上會議",
    "is_all_day": false,
    "calendar_id": "primary"
}
```

**響應**:
```json
{
    "id": 2,
    "user": {...},
    "google_event_id": "xyz789abc123",
    "title": "新會議",
    "description": "會議描述",
    "start_datetime": "2025-09-06T10:00:00Z",
    "end_datetime": "2025-09-06T11:00:00Z",
    "location": "線上會議",
    "is_all_day": false,
    "recurrence_rule": null,
    "calendar_id": "primary",
    "status": "confirmed",
    "created_at": "2025-09-05T06:00:00Z",
    "updated_at": "2025-09-05T06:00:00Z",
    "synced_with_google": true,
    "last_synced_at": "2025-09-05T06:00:00Z"
}
```

### 3. 獲取單一事件
```http
GET /api/events/{id}/
```
**需要認證**: ✅

**響應**: 與事件列表中的單一事件格式相同

### 4. 更新事件
```http
PUT /api/events/{id}/
```
**需要認證**: ✅

**請求體**: 與創建事件相同格式，可部分更新

**響應**: 更新後的事件資料

### 5. 刪除事件
```http
DELETE /api/events/{id}/
```
**需要認證**: ✅

**響應**:
```http
204 No Content
```

---

## Google Calendar整合

### 1. 同步事件
```http
POST /api/sync/
```
**需要認證**: ✅

**響應**:
```json
{
    "message": "Successfully synced 5 events from Google Calendar",
    "synced_count": 5
}
```

### 2. 獲取用戶的Google日曆列表
```http
GET /api/calendars/
```
**需要認證**: ✅

**響應**:
```json
{
    "calendars": [
        {
            "id": "primary",
            "summary": "user@gmail.com",
            "description": "主要日曆",
            "timeZone": "Asia/Taipei",
            "accessRole": "owner",
            "selected": true,
            "primary": true
        },
        {
            "id": "calendar2@group.calendar.google.com",
            "summary": "工作日曆",
            "description": "團隊共用日曆",
            "timeZone": "Asia/Taipei",
            "accessRole": "reader",
            "selected": true,
            "primary": false
        }
    ],
    "count": 2
}
```

---

## 用戶管理

### 1. 獲取用戶檔案
```http
GET /users/profile/
```
**需要認證**: ✅

**響應**:
```json
{
    "profile": {
        "user": {
            "id": 1,
            "username": "user@example.com",
            "email": "user@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "date_joined": "2025-09-01T10:00:00Z"
        },
        "google_id": "123456789012345678901",
        "google_email": "user@gmail.com",
        "token_expires_at": "2025-09-05T10:00:00Z",
        "created_at": "2025-09-01T10:00:00Z",
        "updated_at": "2025-09-05T06:00:00Z"
    }
}
```

### 2. 更新用戶檔案
```http
PUT /users/profile/update/
```
**需要認證**: ✅

**請求體**:
```json
{
    "first_name": "Jane",
    "last_name": "Smith",
    "email": "jane@example.com"
}
```

**響應**:
```json
{
    "message": "Profile updated successfully",
    "profile": {
        "user": {
            "id": 1,
            "username": "user@example.com",
            "email": "jane@example.com",
            "first_name": "Jane",
            "last_name": "Smith",
            "date_joined": "2025-09-01T10:00:00Z"
        },
        "google_id": "123456789012345678901",
        "google_email": "user@gmail.com",
        "token_expires_at": "2025-09-05T10:00:00Z",
        "created_at": "2025-09-01T10:00:00Z",
        "updated_at": "2025-09-05T06:00:00Z"
    }
}
```

---

## 登入頁面

### 使用內建登入頁面
訪問 `http://localhost:8000/login/` 可以使用提供的登入頁面，包含以下功能：

1. **Google OAuth 登入**
   - 一鍵Google登入按鈕
   - 自動處理認證流程

2. **認證狀態檢查**
   - 實時檢查用戶認證狀態
   - 顯示用戶資訊和Google認證狀態

3. **API測試工具**
   - CORS連接測試
   - 事件API測試
   - Google同步功能測試

4. **用戶管理**
   - 查看用戶檔案
   - 安全登出功能

### 頁面端點
- `GET /login/` - 登入頁面
- `GET /` - API資訊頁面 (JSON格式)

---

## 錯誤處理

### 常見錯誤碼

| HTTP狀態碼 | 錯誤類型 | 描述 |
|----------|---------|------|
| 400 | Bad Request | 請求格式錯誤或缺少必要參數 |
| 401 | Unauthorized | 未認證或認證已過期 |
| 403 | Forbidden | 權限不足 |
| 404 | Not Found | 資源不存在 |
| 500 | Internal Server Error | 服務器內部錯誤 |

### 錯誤響應格式
```json
{
    "error": "錯誤描述信息"
}
```

**範例錯誤響應**:
```json
{
    "error": "User not authenticated with Google"
}
```

---

## 數據模型

### 事件模型 (CalendarEvent)
```json
{
    "id": "整數，事件ID",
    "user": "用戶物件",
    "google_event_id": "字串，Google事件ID",
    "title": "字串，事件標題",
    "description": "字串，事件描述",
    "start_datetime": "ISO 8601日期時間，開始時間",
    "end_datetime": "ISO 8601日期時間，結束時間",
    "location": "字串，地點",
    "is_all_day": "布林值，是否全天事件",
    "recurrence_rule": "字串，重複規則",
    "calendar_id": "字串，日曆ID",
    "status": "字串，事件狀態",
    "created_at": "ISO 8601日期時間，創建時間",
    "updated_at": "ISO 8601日期時間，更新時間",
    "synced_with_google": "布林值，是否已與Google同步",
    "last_synced_at": "ISO 8601日期時間，最後同步時間"
}
```

### 用戶模型 (User)
```json
{
    "id": "整數，用戶ID",
    "username": "字串，用戶名",
    "email": "字串，郵箱",
    "first_name": "字串，名字",
    "last_name": "字串，姓氏",
    "date_joined": "ISO 8601日期時間，加入時間"
}
```

---

## 開發注意事項

### 1. 認證流程
- **推薦方式**: 訪問 `/login/` 使用內建登入頁面
- **API方式**: 調用 `/auth/google/` 獲取授權URL，然後重定向用戶
- 用戶完成Google授權後會自動重定向到 `http://localhost:8000/auth/callback/`
- 使用Django的session認證，確保瀏覽器支援cookie
- Token會自動刷新，但建議監控 `token_expires_at` 欄位
- 認證完成後可調用 `/auth/status/` 確認狀態

### 2. 日期時間格式
- 所有日期時間使用 ISO 8601 格式 (YYYY-MM-DDTHH:MM:SSZ)
- 時區統一使用UTC，前端需要轉換為本地時間顯示

### 3. CORS配置
- 已配置允許 `localhost:3000` 和 `127.0.0.1:3000`
- 支援認證cookie跨域

### 4. CORS測試端點
```http
GET /cors-test/
POST /cors-test/
OPTIONS /cors-test/
```
**需要認證**: ❌

**用途**: 測試CORS設定是否正確配置

**響應**:
```json
{
    "method": "GET",
    "cors_enabled": true,
    "headers": {...},
    "message": "CORS is working correctly!"
}
```

### 5. 分頁
- 目前API不支援分頁，建議使用日期範圍過濾大量數據

### 6. 速率限制
- 目前無速率限制，生產環境建議添加

---

## 測試範例

### JavaScript Fetch 範例
```javascript
// 1. 檢查認證狀態 (認證後才能調用)
const checkAuth = async () => {
    try {
        const response = await fetch('http://localhost:8000/auth/status/', {
            credentials: 'include'
        });
        return response.ok;
    } catch {
        return false;
    }
};

// 2. 開始Google認證流程
const startGoogleAuth = async () => {
    const response = await fetch('http://localhost:8000/auth/google/', {
        credentials: 'include'
    });
    const data = await response.json();
    // 重定向用戶到Google認證頁面
    window.location.href = data.auth_url;
};

// 3. 獲取事件列表 (需要先認證)
const getEvents = async () => {
    const response = await fetch('http://localhost:8000/api/events/', {
        method: 'GET',
        credentials: 'include', // 重要：包含認證cookie
        headers: {
            'Content-Type': 'application/json',
        }
    });
    if (response.status === 403) {
        console.log('需要先進行Google認證');
        return;
    }
    const events = await response.json();
    return events;
};

// 4. 創建事件
const createEvent = async (eventData) => {
    const response = await fetch('http://localhost:8000/api/events/', {
        method: 'POST',
        credentials: 'include',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(eventData)
    });
    return await response.json();
};

// 完整使用範例
const main = async () => {
    // 檢查是否已認證
    const isAuthenticated = await checkAuth();
    
    if (!isAuthenticated) {
        console.log('用戶未認證，開始認證流程...');
        await startGoogleAuth();
        return;
    }
    
    // 獲取事件
    const events = await getEvents();
    console.log('事件列表:', events);
    
    // 創建新事件
    const newEvent = await createEvent({
        title: '新會議',
        start_datetime: '2025-09-06T10:00:00Z',
        end_datetime: '2025-09-06T11:00:00Z',
        description: '會議描述'
    });
    console.log('新事件:', newEvent);
};
```

### curl 測試範例
```bash
# 獲取Google認證URL
curl -X GET http://localhost:8000/auth/google/

# 獲取事件列表 (需要先認證)
curl -X GET http://localhost:8000/api/events/ \
  -H "Content-Type: application/json" \
  --cookie-jar cookies.txt --cookie cookies.txt
```

---

## 部署配置

### 環境變數
```env
DEBUG=False
SECRET_KEY=your-secret-key
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_REDIRECT_URI=http://your-domain.com/auth/callback/
```

### CORS和安全設置
生產環境需要更新：
- `ALLOWED_HOSTS`
- `CORS_ALLOWED_ORIGINS`
- `GOOGLE_REDIRECT_URI`

---

**最後更新**: 2025-09-05  
**版本**: 1.1.0  
**新增功能**: 
- 內建登入頁面 (`/login/`)
- CORS測試端點 (`/cors-test/`)
- 完整的JavaScript使用範例
- 改進的認證流程說明

**聯繫人**: Backend Team