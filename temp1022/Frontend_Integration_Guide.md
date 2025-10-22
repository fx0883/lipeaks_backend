# User Feedback System - Frontend Integration Guide

## Table of Contents
1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Software Management APIs](#software-management-apis)
4. [Feedback Management APIs](#feedback-management-apis)
5. [Reply Management APIs](#reply-management-apis)
6. [Voting APIs](#voting-apis)
7. [Attachment APIs](#attachment-apis)
8. [Email Management APIs](#email-management-apis)
9. [Statistics APIs](#statistics-apis)
10. [Error Handling](#error-handling)
11. [WebSocket Support](#websocket-support)
12. [Best Practices](#best-practices)

## Overview

The User Feedback System provides RESTful APIs for managing software products, collecting user feedback, and handling email notifications. All APIs use JSON for request/response bodies and follow standard HTTP status codes.

### Base URL
```
Production: https://api.yourdomain.com/api/v1/feedbacks/
Development: http://localhost:8000/api/v1/feedbacks/
```

### Common Headers
```http
Content-Type: application/json
Accept: application/json
Authorization: Bearer <jwt-token>  # For authenticated endpoints
X-Tenant-ID: <tenant-id>  # Optional, handled by middleware
```

### Response Format
All successful responses follow this structure:
```json
{
  "data": {...},     // For single object
  "results": [...],  // For lists
  "count": 100,      // Total count for paginated lists
  "next": "...",     // Next page URL
  "previous": "..."  // Previous page URL
}
```

Error responses:
```json
{
  "error": "Error message",
  "errors": {
    "field_name": ["Error detail"]
  },
  "code": "ERROR_CODE"
}
```

## Authentication

Most endpoints require JWT authentication. Anonymous users can only submit feedback.

### Login (Get JWT Token)
```http
POST /api/v1/auth/login/
```

**Request:**
```json
{
  "username": "user@example.com",
  "password": "password123"
}
```

**Response:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 1,
    "username": "user@example.com",
    "email": "user@example.com",
    "is_tenant_admin": true
  }
}
```

### Refresh Token
```http
POST /api/v1/auth/refresh/
```

**Request:**
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

## Software Management APIs

### 1. Software Categories

#### List Categories
```http
GET /api/v1/feedbacks/software-categories/
```

**Query Parameters:**
- `is_active` (boolean): Filter by active status
- `search` (string): Search in name and description

**Response:**
```json
{
  "count": 3,
  "results": [
    {
      "id": 1,
      "name": "Web Applications",
      "code": "web",
      "description": "Web-based software applications",
      "icon": "web",
      "sort_order": 1,
      "is_active": true,
      "software_count": 5,
      "created_at": "2025-01-01T00:00:00Z",
      "updated_at": "2025-01-01T00:00:00Z"
    }
  ]
}
```

#### Create Category (Tenant Admin Only)
```http
POST /api/v1/feedbacks/software-categories/
```

**Request:**
```json
{
  "name": "Mobile Applications",
  "code": "mobile",
  "description": "Mobile software applications",
  "icon": "smartphone",
  "sort_order": 2,
  "is_active": true
}
```

**Response:** 201 Created
```json
{
  "id": 2,
  "name": "Mobile Applications",
  "code": "mobile",
  "description": "Mobile software applications",
  "icon": "smartphone",
  "sort_order": 2,
  "is_active": true,
  "software_count": 0,
  "created_at": "2025-01-15T10:30:00Z",
  "updated_at": "2025-01-15T10:30:00Z"
}
```

#### Update Category
```http
PATCH /api/v1/feedbacks/software-categories/{id}/
```

**Request:**
```json
{
  "name": "Mobile Apps",
  "sort_order": 3
}
```

### 2. Software Products

#### List Software
```http
GET /api/v1/feedbacks/software/
```

**Query Parameters:**
- `category` (integer): Filter by category ID
- `status` (string): Filter by status (development/testing/released/maintenance/deprecated)
- `is_active` (boolean): Filter by active status
- `search` (string): Search in name, code, description

**Response:**
```json
{
  "count": 2,
  "results": [
    {
      "id": 1,
      "name": "CRM System",
      "code": "crm_system",
      "description": "Customer Relationship Management System",
      "category": 1,
      "category_name": "Web Applications",
      "logo": "http://example.com/media/feedbacks/software/logos/2025/01/crm_logo.png",
      "current_version": "v2.1.0",
      "status": "released",
      "is_active": true,
      "total_feedbacks": 42,
      "open_feedbacks": 5,
      "version_count": 10,
      "created_at": "2025-01-01T00:00:00Z",
      "updated_at": "2025-01-15T00:00:00Z"
    }
  ]
}
```

#### Create Software (Tenant Admin Only)
```http
POST /api/v1/feedbacks/software/
```

**Request:**
```json
{
  "name": "ERP System",
  "code": "erp_system",
  "description": "Enterprise Resource Planning System",
  "category_id": 1,
  "website": "https://erp.example.com",
  "owner": "John Doe",
  "team": "ERP Team",
  "contact_email": "support@erp.example.com",
  "tags": ["enterprise", "saas", "cloud"],
  "metadata": {
    "license_type": "subscription",
    "deployment": "cloud"
  },
  "status": "released",
  "is_active": true
}
```

**Response:** 201 Created
```json
{
  "id": 2,
  "name": "ERP System",
  "code": "erp_system",
  "description": "Enterprise Resource Planning System",
  "category": {
    "id": 1,
    "name": "Web Applications",
    "code": "web"
  },
  "logo": null,
  "website": "https://erp.example.com",
  "current_version": null,
  "owner": "John Doe",
  "team": "ERP Team",
  "contact_email": "support@erp.example.com",
  "tags": ["enterprise", "saas", "cloud"],
  "metadata": {
    "license_type": "subscription",
    "deployment": "cloud"
  },
  "status": "released",
  "is_active": true,
  "total_feedbacks": 0,
  "open_feedbacks": 0,
  "versions": [],
  "latest_stable_version": null,
  "created_at": "2025-01-15T10:45:00Z",
  "updated_at": "2025-01-15T10:45:00Z"
}
```

#### Get Software Details
```http
GET /api/v1/feedbacks/software/{id}/
```

**Response:** Includes full details with versions array.

#### Add Software Version
```http
POST /api/v1/feedbacks/software/{id}/versions/
```

**Request:**
```json
{
  "version": "v2.2.0",
  "version_code": 220,
  "release_date": "2025-01-15",
  "release_notes": "## New Features\n- Dark mode support\n- Performance improvements\n\n## Bug Fixes\n- Fixed login issue",
  "is_stable": true,
  "is_active": true,
  "download_url": "https://example.com/download/v2.2.0"
}
```

## Feedback Management APIs

### 1. Submit Feedback (Public)
```http
POST /api/v1/feedbacks/feedbacks/
```

**Request (Authenticated User):**
```json
{
  "title": "Feature request: Dark mode",
  "description": "It would be great to have a dark mode option for better eye comfort during night usage.",
  "feedback_type": "feature",
  "priority": "medium",
  "software": 1,
  "software_version": 10,
  "environment_info": {
    "os": "Windows 11",
    "browser": "Chrome 120",
    "screen_resolution": "1920x1080",
    "timezone": "UTC+8"
  }
}
```

**Request (Anonymous User):**
```json
{
  "title": "Bug: Application crashes on startup",
  "description": "The application crashes immediately after launching...",
  "feedback_type": "bug",
  "priority": "high",
  "software": 1,
  "software_version": 10,
  "contact_email": "user@example.com",
  "contact_name": "John Doe",
  "environment_info": {
    "os": "macOS 14.0",
    "app_version": "2.1.0",
    "device": "MacBook Pro M1"
  }
}
```

**Response:** 201 Created
```json
{
  "id": 1,
  "title": "Bug: Application crashes on startup",
  "description": "The application crashes immediately after launching...",
  "feedback_type": "bug",
  "priority": "high",
  "status": "submitted",
  "software": {
    "id": 1,
    "name": "CRM System",
    "current_version": "v2.1.0"
  },
  "software_version": {
    "id": 10,
    "version": "v2.1.0",
    "release_date": "2025-01-01"
  },
  "user": null,
  "contact_email": "user@example.com",
  "contact_name": "John Doe",
  "email_verified": false,
  "email_notification_enabled": true,
  "environment_info": {
    "os": "macOS 14.0",
    "app_version": "2.1.0",
    "device": "MacBook Pro M1"
  },
  "vote_count": 0,
  "reply_count": 0,
  "attachments": [],
  "created_at": "2025-01-15T11:00:00Z"
}
```

**Note:** Anonymous users will receive a verification email.

### 2. List Feedback
```http
GET /api/v1/feedbacks/feedbacks/
```

**Query Parameters:**
- `software` (integer): Filter by software ID
- `software_version` (integer): Filter by version ID
- `feedback_type` (string): bug/feature/improvement/question/other
- `status` (string): submitted/reviewing/confirmed/in_progress/resolved/closed/rejected/duplicate
- `priority` (string): critical/high/medium/low
- `user` (integer): Filter by user ID (admin only)
- `email_verified` (boolean): Filter by email verification
- `search` (string): Search in title, description, email
- `ordering` (string): created_at/-created_at/vote_count/-vote_count/reply_count/-reply_count/priority/-priority

**Response:**
```json
{
  "count": 25,
  "next": "http://api.example.com/api/v1/feedbacks/feedbacks/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "title": "Bug: Application crashes on startup",
      "description": "The application crashes immediately after launching...",
      "feedback_type": "bug",
      "type_display": "Bug Report",
      "priority": "high",
      "priority_display": "High",
      "status": "reviewing",
      "status_display": "Reviewing",
      "software": 1,
      "software_name": "CRM System",
      "software_version": 10,
      "version_number": "v2.1.0",
      "submitter": {
        "name": "John Doe",
        "email": "user@example.com"
      },
      "contact_email": "user@example.com",
      "vote_count": 5,
      "reply_count": 2,
      "created_at": "2025-01-15T11:00:00Z",
      "updated_at": "2025-01-15T14:30:00Z"
    }
  ]
}
```

### 3. Get Feedback Details
```http
GET /api/v1/feedbacks/feedbacks/{id}/
```

**Response:**
```json
{
  "id": 1,
  "title": "Bug: Application crashes on startup",
  "description": "The application crashes immediately after launching...",
  "feedback_type": "bug",
  "priority": "high",
  "status": "reviewing",
  "software": {
    "id": 1,
    "name": "CRM System",
    "code": "crm_system",
    "description": "Customer Relationship Management System",
    "category": 1,
    "category_name": "Web Applications",
    "logo": "http://example.com/media/logos/crm.png",
    "current_version": "v2.1.0",
    "status": "released",
    "is_active": true,
    "total_feedbacks": 42,
    "open_feedbacks": 5,
    "version_count": 10
  },
  "software_version": {
    "id": 10,
    "version": "v2.1.0",
    "version_code": 210,
    "release_date": "2025-01-01",
    "release_notes": "Bug fixes and performance improvements",
    "is_stable": true,
    "is_active": true
  },
  "user": null,
  "user_info": {
    "name": "John Doe",
    "email": "user@example.com",
    "is_registered": false
  },
  "contact_email": "user@example.com",
  "contact_name": "John Doe",
  "email_verified": true,
  "email_notification_enabled": true,
  "environment_info": {
    "os": "macOS 14.0",
    "app_version": "2.1.0",
    "device": "MacBook Pro M1"
  },
  "ip_address": "192.168.1.100",
  "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
  "assigned_to": null,
  "resolved_at": null,
  "resolution_notes": null,
  "view_count": 15,
  "vote_count": 5,
  "reply_count": 2,
  "attachments": [
    {
      "id": 1,
      "file": "http://example.com/media/feedbacks/attachments/2025/01/error_log.txt",
      "file_url": "http://example.com/media/feedbacks/attachments/2025/01/error_log.txt",
      "filename": "error_log.txt",
      "file_size": 2048,
      "mime_type": "text/plain",
      "uploaded_by": null,
      "created_at": "2025-01-15T11:05:00Z"
    }
  ],
  "replies": [
    {
      "id": 1,
      "feedback": 1,
      "user": 2,
      "user_name": "support_agent",
      "user_email": "support@example.com",
      "content": "Thank you for reporting this issue. We're investigating the crash.",
      "is_internal_note": false,
      "email_sent": true,
      "email_sent_at": "2025-01-15T11:30:00Z",
      "created_at": "2025-01-15T11:30:00Z",
      "updated_at": "2025-01-15T11:30:00Z"
    }
  ],
  "status_history": [
    {
      "id": 1,
      "feedback": 1,
      "from_status": "submitted",
      "to_status": "reviewing",
      "from_status_display": "Submitted",
      "to_status_display": "Reviewing",
      "changed_by": 2,
      "changed_by_name": "support_agent",
      "reason": "Assigned to development team",
      "created_at": "2025-01-15T11:30:00Z"
    }
  ],
  "user_vote": 1,  // 1 for upvote, -1 for downvote, null if not voted
  "created_at": "2025-01-15T11:00:00Z",
  "updated_at": "2025-01-15T14:30:00Z"
}
```

### 4. Update Feedback
```http
PATCH /api/v1/feedbacks/feedbacks/{id}/
```

**Request:**
```json
{
  "title": "Bug: Application crashes on startup [CRITICAL]",
  "priority": "critical",
  "assigned_to": 5
}
```

**Note:** Users can only update their own feedback if it hasn't been replied to.

### 5. Change Feedback Status (Admin Only)
```http
PATCH /api/v1/feedbacks/feedbacks/{id}/status/
```

**Request:**
```json
{
  "status": "in_progress",
  "reason": "Assigned to development team for investigation"
}
```

**Response:**
```json
{
  "id": 1,
  "status": "in_progress",
  // ... full feedback object
}
```

### 6. Verify Email (Anonymous Feedback)
```http
POST /api/v1/feedbacks/feedbacks/{id}/verify-email/
```

**Request:**
```json
{
  "token": "a1b2c3d4e5f6g7h8i9j0"
}
```

**Response:**
```json
{
  "message": "Email verified successfully"
}
```

### 7. Toggle Email Notifications
```http
PATCH /api/v1/feedbacks/feedbacks/{id}/notifications/
```

**Request:**
```json
{
  "enabled": false
}
```

**Response:**
```json
{
  "message": "Notification settings updated",
  "email_notification_enabled": false
}
```

## Reply Management APIs

### 1. Add Reply to Feedback (Admin Only)
```http
POST /api/v1/feedbacks/feedbacks/{feedback_id}/replies/
```

**Request:**
```json
{
  "content": "Thank you for your feedback. We've identified the issue and will release a fix in v2.1.1.",
  "is_internal_note": false
}
```

**Response:** 201 Created
```json
{
  "id": 2,
  "feedback": 1,
  "user": 2,
  "user_name": "support_agent",
  "user_email": "support@example.com",
  "content": "Thank you for your feedback. We've identified the issue and will release a fix in v2.1.1.",
  "is_internal_note": false,
  "email_sent": false,
  "email_sent_at": null,
  "created_at": "2025-01-15T15:00:00Z",
  "updated_at": "2025-01-15T15:00:00Z"
}
```

**Note:** Email notification will be sent asynchronously if not an internal note.

### 2. List Replies
```http
GET /api/v1/feedbacks/feedbacks/{feedback_id}/replies/
```

**Response:**
```json
{
  "count": 2,
  "results": [
    {
      "id": 1,
      "feedback": 1,
      "user": 2,
      "user_name": "support_agent",
      "user_email": "support@example.com",
      "content": "Thank you for reporting this issue. We're investigating.",
      "is_internal_note": false,
      "email_sent": true,
      "email_sent_at": "2025-01-15T11:30:00Z",
      "created_at": "2025-01-15T11:30:00Z",
      "updated_at": "2025-01-15T11:30:00Z"
    }
  ]
}
```

**Note:** Non-staff users won't see internal notes.

## Voting APIs

### 1. Vote on Feedback
```http
POST /api/v1/feedbacks/feedbacks/{id}/vote/
```

**Request:**
```json
{
  "vote_type": 1  // 1 for upvote, -1 for downvote
}
```

**Response:**
```json
{
  "message": "Vote recorded",
  "vote_type": 1,
  "total_votes": 6
}
```

### 2. Remove Vote
```http
DELETE /api/v1/feedbacks/feedbacks/{id}/vote/
```

**Response:** 204 No Content

## Attachment APIs

### 1. Upload Attachment
```http
POST /api/v1/feedbacks/feedbacks/{feedback_id}/attachments/
Content-Type: multipart/form-data
```

**Request (Form Data):**
```
file: [binary file data]
```

**Allowed file types:** jpg, jpeg, png, gif, pdf, doc, docx, txt, log, zip
**Max file size:** 10MB

**Response:** 201 Created
```json
{
  "id": 2,
  "file": "http://example.com/media/feedbacks/attachments/2025/01/screenshot.png",
  "file_url": "http://example.com/media/feedbacks/attachments/2025/01/screenshot.png",
  "filename": "screenshot.png",
  "file_size": 154320,
  "mime_type": "image/png",
  "uploaded_by": 1,
  "created_at": "2025-01-15T15:30:00Z"
}
```

### 2. List Attachments
```http
GET /api/v1/feedbacks/feedbacks/{feedback_id}/attachments/
```

### 3. Delete Attachment
```http
DELETE /api/v1/feedbacks/feedbacks/{feedback_id}/attachments/{id}/
```

**Response:** 204 No Content

## Email Management APIs

### 1. Email Templates (Tenant Admin Only)

#### List Templates
```http
GET /api/v1/feedbacks/email-templates/
```

**Response:**
```json
{
  "count": 3,
  "results": [
    {
      "id": 1,
      "name": "Feedback Reply Notification",
      "template_type": "reply",
      "template_type_display": "Reply Notification",
      "subject": "Re: {feedback_title}",
      "body_html": "<!DOCTYPE html>...",
      "body_text": "New Reply to Your Feedback...",
      "is_active": true,
      "variables": {
        "feedback_title": "Feedback title",
        "reply_content": "Reply content",
        "reply_user": "User who replied"
      },
      "created_at": "2025-01-01T00:00:00Z",
      "updated_at": "2025-01-01T00:00:00Z"
    }
  ]
}
```

#### Create Template
```http
POST /api/v1/feedbacks/email-templates/
```

**Request:**
```json
{
  "name": "Custom Welcome Email",
  "template_type": "welcome",
  "subject": "Welcome to {software_name} Feedback System",
  "body_html": "<!DOCTYPE html><html><body><h1>Welcome!</h1><p>Thank you for using {software_name}.</p></body></html>",
  "body_text": "Welcome! Thank you for using {software_name}.",
  "is_active": true,
  "variables": {
    "software_name": "Name of the software"
  }
}
```

### 2. Email Logs (Read Only)

#### List Email Logs
```http
GET /api/v1/feedbacks/email-logs/
```

**Query Parameters:**
- `feedback` (integer): Filter by feedback ID
- `status` (string): pending/sending/sent/failed/bounced
- `email_type` (string): reply/status_change/verification/summary

**Response:**
```json
{
  "count": 10,
  "results": [
    {
      "id": 1,
      "feedback": 1,
      "email_type": "reply",
      "email_type_display": "Reply Notification",
      "recipient": "user@example.com",
      "subject": "Re: Bug: Application crashes on startup",
      "content": "<!DOCTYPE html>...",
      "status": "sent",
      "status_display": "Sent",
      "sent_at": "2025-01-15T11:30:15Z",
      "error_message": null,
      "retry_count": 0,
      "created_at": "2025-01-15T11:30:00Z",
      "updated_at": "2025-01-15T11:30:15Z"
    }
  ]
}
```

## Statistics APIs

### Get Feedback Statistics (Admin Only)
```http
GET /api/v1/feedbacks/statistics/
```

**Query Parameters:**
- `software` (integer): Filter by software ID
- `date_from` (date): Start date (YYYY-MM-DD)
- `date_to` (date): End date (YYYY-MM-DD)

**Response:**
```json
{
  "total_feedbacks": 150,
  "open_feedbacks": 25,
  "resolved_feedbacks": 100,
  "avg_resolution_time": "3 days, 4:30:00",
  "feedbacks_by_type": {
    "bug": 60,
    "feature": 40,
    "improvement": 30,
    "question": 15,
    "other": 5
  },
  "feedbacks_by_status": {
    "submitted": 10,
    "reviewing": 5,
    "confirmed": 10,
    "in_progress": 15,
    "resolved": 100,
    "closed": 5,
    "rejected": 3,
    "duplicate": 2
  },
  "feedbacks_by_priority": {
    "critical": 10,
    "high": 30,
    "medium": 80,
    "low": 30
  },
  "top_voted_feedbacks": [
    {
      "id": 5,
      "title": "Feature request: Dark mode",
      "vote_count": 25,
      "feedback_type": "feature",
      "status": "confirmed"
    }
  ],
  "recent_feedbacks": [
    {
      "id": 150,
      "title": "Bug: Export function not working",
      "created_at": "2025-01-15T16:00:00Z",
      "feedback_type": "bug",
      "priority": "high"
    }
  ],
  "daily_trend": [
    {
      "date": "2025-01-15",
      "count": 5
    },
    {
      "date": "2025-01-14",
      "count": 8
    }
  ]
}
```

## Error Handling

### Common Error Responses

#### 400 Bad Request
```json
{
  "error": "Invalid input data",
  "errors": {
    "title": ["This field is required."],
    "software": ["Invalid pk \"999\" - object does not exist."]
  }
}
```

#### 401 Unauthorized
```json
{
  "error": "Authentication credentials were not provided.",
  "code": "not_authenticated"
}
```

#### 403 Forbidden
```json
{
  "error": "You don't have permission to perform this action.",
  "code": "permission_denied"
}
```

#### 404 Not Found
```json
{
  "error": "Not found.",
  "code": "not_found"
}
```

#### 429 Too Many Requests
```json
{
  "error": "Request was throttled. Expected available in 57 seconds.",
  "code": "throttled"
}
```

## WebSocket Support

For real-time updates, connect to WebSocket endpoint:

```javascript
const ws = new WebSocket('wss://api.example.com/ws/feedbacks/');

ws.onopen = () => {
  // Authenticate
  ws.send(JSON.stringify({
    type: 'auth',
    token: 'your-jwt-token'
  }));
  
  // Subscribe to feedback updates
  ws.send(JSON.stringify({
    type: 'subscribe',
    channel: 'feedback_updates',
    software_id: 1
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  switch(data.type) {
    case 'feedback_created':
      console.log('New feedback:', data.feedback);
      break;
    case 'feedback_updated':
      console.log('Feedback updated:', data.feedback);
      break;
    case 'reply_added':
      console.log('New reply:', data.reply);
      break;
  }
};
```

## Best Practices

### 1. Pagination
Always paginate list endpoints:
```javascript
async function fetchAllFeedback() {
  let allFeedback = [];
  let nextUrl = '/api/v1/feedbacks/feedbacks/';
  
  while (nextUrl) {
    const response = await fetch(nextUrl);
    const data = await response.json();
    allFeedback = [...allFeedback, ...data.results];
    nextUrl = data.next;
  }
  
  return allFeedback;
}
```

### 2. Error Handling
```javascript
async function submitFeedback(feedbackData) {
  try {
    const response = await fetch('/api/v1/feedbacks/feedbacks/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(feedbackData)
    });
    
    if (!response.ok) {
      const error = await response.json();
      
      // Handle validation errors
      if (error.errors) {
        Object.entries(error.errors).forEach(([field, messages]) => {
          console.error(`${field}: ${messages.join(', ')}`);
        });
      }
      
      throw new Error(error.error || 'Request failed');
    }
    
    return await response.json();
  } catch (error) {
    console.error('Failed to submit feedback:', error);
    throw error;
  }
}
```

### 3. File Upload with Progress
```javascript
async function uploadAttachment(feedbackId, file) {
  const formData = new FormData();
  formData.append('file', file);
  
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    
    xhr.upload.addEventListener('progress', (event) => {
      if (event.lengthComputable) {
        const percentComplete = (event.loaded / event.total) * 100;
        console.log(`Upload progress: ${percentComplete.toFixed(2)}%`);
      }
    });
    
    xhr.addEventListener('load', () => {
      if (xhr.status === 201) {
        resolve(JSON.parse(xhr.responseText));
      } else {
        reject(new Error(xhr.statusText));
      }
    });
    
    xhr.addEventListener('error', () => {
      reject(new Error('Upload failed'));
    });
    
    xhr.open('POST', `/api/v1/feedbacks/feedbacks/${feedbackId}/attachments/`);
    xhr.setRequestHeader('Authorization', `Bearer ${token}`);
    xhr.send(formData);
  });
}
```

### 4. Optimistic Updates
```javascript
// Vote on feedback with optimistic update
async function voteFeedback(feedbackId, voteType) {
  // Update UI immediately
  updateVoteUI(feedbackId, voteType);
  
  try {
    const response = await fetch(`/api/v1/feedbacks/feedbacks/${feedbackId}/vote/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({ vote_type: voteType })
    });
    
    if (!response.ok) {
      // Revert UI on error
      revertVoteUI(feedbackId);
      throw new Error('Vote failed');
    }
    
    const data = await response.json();
    // Update with actual vote count from server
    updateVoteCount(feedbackId, data.total_votes);
  } catch (error) {
    console.error('Vote failed:', error);
    showError('Failed to record vote');
  }
}
```

### 5. Caching Strategy
```javascript
class FeedbackCache {
  constructor() {
    this.cache = new Map();
    this.ttl = 5 * 60 * 1000; // 5 minutes
  }
  
  set(key, data) {
    this.cache.set(key, {
      data,
      timestamp: Date.now()
    });
  }
  
  get(key) {
    const cached = this.cache.get(key);
    if (!cached) return null;
    
    if (Date.now() - cached.timestamp > this.ttl) {
      this.cache.delete(key);
      return null;
    }
    
    return cached.data;
  }
  
  invalidate(pattern) {
    for (const key of this.cache.keys()) {
      if (key.includes(pattern)) {
        this.cache.delete(key);
      }
    }
  }
}

const feedbackCache = new FeedbackCache();

async function getFeedback(id) {
  const cacheKey = `feedback:${id}`;
  const cached = feedbackCache.get(cacheKey);
  
  if (cached) {
    return cached;
  }
  
  const response = await fetch(`/api/v1/feedbacks/feedbacks/${id}/`);
  const data = await response.json();
  
  feedbackCache.set(cacheKey, data);
  return data;
}
```

### 6. Debounced Search
```javascript
function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

const searchFeedback = debounce(async (query) => {
  const response = await fetch(`/api/v1/feedbacks/feedbacks/?search=${encodeURIComponent(query)}`);
  const data = await response.json();
  displaySearchResults(data.results);
}, 300);

// Usage
searchInput.addEventListener('input', (e) => {
  searchFeedback(e.target.value);
});
```

## Sample React Integration

```jsx
// hooks/useFeedback.js
import { useState, useEffect } from 'react';
import { feedbackApi } from '../api/feedback';

export function useFeedback(feedbackId) {
  const [feedback, setFeedback] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  useEffect(() => {
    async function fetchFeedback() {
      try {
        setLoading(true);
        const data = await feedbackApi.getFeedback(feedbackId);
        setFeedback(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }
    
    if (feedbackId) {
      fetchFeedback();
    }
  }, [feedbackId]);
  
  const updateFeedback = async (updates) => {
    try {
      const updated = await feedbackApi.updateFeedback(feedbackId, updates);
      setFeedback(updated);
      return updated;
    } catch (err) {
      setError(err.message);
      throw err;
    }
  };
  
  const addReply = async (content, isInternal = false) => {
    try {
      const reply = await feedbackApi.addReply(feedbackId, {
        content,
        is_internal_note: isInternal
      });
      
      // Update local state
      setFeedback(prev => ({
        ...prev,
        replies: [...prev.replies, reply],
        reply_count: prev.reply_count + 1
      }));
      
      return reply;
    } catch (err) {
      setError(err.message);
      throw err;
    }
  };
  
  return {
    feedback,
    loading,
    error,
    updateFeedback,
    addReply
  };
}

// components/FeedbackDetail.jsx
import React from 'react';
import { useFeedback } from '../hooks/useFeedback';

function FeedbackDetail({ feedbackId }) {
  const { feedback, loading, error, addReply } = useFeedback(feedbackId);
  const [replyContent, setReplyContent] = useState('');
  const [submitting, setSubmitting] = useState(false);
  
  const handleReplySubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    
    try {
      await addReply(replyContent);
      setReplyContent('');
      toast.success('Reply sent successfully');
    } catch (err) {
      toast.error('Failed to send reply');
    } finally {
      setSubmitting(false);
    }
  };
  
  if (loading) return <Spinner />;
  if (error) return <ErrorMessage message={error} />;
  if (!feedback) return <NotFound />;
  
  return (
    <div className="feedback-detail">
      <h1>{feedback.title}</h1>
      <div className="metadata">
        <span className="status">{feedback.status_display}</span>
        <span className="type">{feedback.type_display}</span>
        <span className="priority">{feedback.priority_display}</span>
      </div>
      
      <div className="content">
        <p>{feedback.description}</p>
      </div>
      
      <div className="replies">
        <h2>Replies ({feedback.reply_count})</h2>
        {feedback.replies.map(reply => (
          <Reply key={reply.id} reply={reply} />
        ))}
      </div>
      
      <form onSubmit={handleReplySubmit}>
        <textarea
          value={replyContent}
          onChange={(e) => setReplyContent(e.target.value)}
          placeholder="Write a reply..."
          required
        />
        <button type="submit" disabled={submitting}>
          {submitting ? 'Sending...' : 'Send Reply'}
        </button>
      </form>
    </div>
  );
}
```

## Rate Limiting

API endpoints have the following rate limits:

- **Anonymous users**: 10 requests per minute
- **Authenticated users**: 60 requests per minute
- **Feedback submission**: 5 per hour per IP
- **File uploads**: 10 per hour per user

Exceeded limits return 429 status with retry information in headers:
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1673784000
Retry-After: 57
```

## CORS Configuration

The API supports CORS for frontend applications. Include your domain in allowed origins:

```javascript
// Development
const API_BASE = 'http://localhost:8000/api/v1/feedbacks/';

// Production
const API_BASE = 'https://api.yourdomain.com/api/v1/feedbacks/';

// Axios configuration
axios.defaults.baseURL = API_BASE;
axios.defaults.headers.common['Content-Type'] = 'application/json';
axios.defaults.withCredentials = true; // For cookie-based sessions
```

## Testing the APIs

### Using cURL

```bash
# Submit feedback (anonymous)
curl -X POST http://localhost:8000/api/v1/feedbacks/feedbacks/ \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Feedback",
    "description": "This is a test",
    "feedback_type": "bug",
    "priority": "medium",
    "software": 1,
    "contact_email": "test@example.com"
  }'

# Get feedback list (authenticated)
curl -X GET http://localhost:8000/api/v1/feedbacks/feedbacks/ \
  -H "Authorization: Bearer your-jwt-token"

# Vote on feedback
curl -X POST http://localhost:8000/api/v1/feedbacks/feedbacks/1/vote/ \
  -H "Authorization: Bearer your-jwt-token" \
  -H "Content-Type: application/json" \
  -d '{"vote_type": 1}'
```

### Using Postman

Import the OpenAPI schema from `/api/v1/schema/` to automatically generate a Postman collection with all endpoints.

## Support

For API support and questions:
- Documentation: `/api/v1/docs/`
- OpenAPI Schema: `/api/v1/schema/`
- Email: api-support@yourdomain.com
