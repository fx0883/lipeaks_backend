# User Feedback System - Quick Start Guide

## 🚀 5-Minute Setup

### 1. Install Dependencies
```bash
pip install -r feedbacks/requirements.txt
```

### 2. Run Migrations
```bash
python manage.py migrate
```

### 3. Create Email Templates
```bash
python manage.py init_feedback_templates
```

### 4. Start Services
```bash
# Terminal 1: Start Redis
docker run -d -p 6379:6379 redis:latest

# Terminal 2: Start Celery Worker
celery -A core worker -l info

# Terminal 3: Start Django Server
python manage.py runserver
```

### 5. Check System Health
```bash
python manage.py check_health --verbose
```

**Expected Output:**
```
✅ Redis: Available (or ⚠️ degraded mode)
✅ Database: Connected
✅ Celery: Configured
✅ Email: SMTP configured
```

### 6. Access API Documentation
Open browser: http://localhost:8000/api/v1/docs/

## ⚠️ What if Redis is Not Available?

**Don't worry!** The system has automatic fallback.

### Option 1: Run Without Redis (Degraded Mode)
```bash
# Just start Django (no Redis, no Celery)
python manage.py runserver

# System will work, but:
# - Email sending is synchronous (slower)
# - API responses take 3-5 seconds
# - Still fully functional
```

### Option 2: Use Database Broker
```bash
# Edit core/settings.py
CELERY_BROKER_URL = 'django-db'
CELERY_RESULT_BACKEND = 'django-db'

# Add to INSTALLED_APPS
INSTALLED_APPS += ['django_celery_results']

# Migrate
python manage.py migrate django_celery_results

# Start Celery (uses database instead of Redis)
celery -A core worker -l info
```

**See**: [cPanel_Deployment_Guide.md](cPanel_Deployment_Guide.md) for details

## 🧪 Quick Test - Submit Feedback

### Using cURL (Anonymous)
```bash
curl -X POST http://localhost:8000/api/v1/feedbacks/feedbacks/ \
  -H "Content-Type: application/json" \
  -d '{
    "title": "My First Feedback",
    "description": "Testing the feedback system",
    "feedback_type": "feature",
    "priority": "medium",
    "software": 1,
    "contact_email": "test@example.com"
  }'
```

### Using JavaScript
```javascript
// Submit feedback
const submitFeedback = async () => {
  const response = await fetch('http://localhost:8000/api/v1/feedbacks/feedbacks/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      title: 'Feature Request: Dark Mode',
      description: 'Please add dark mode support',
      feedback_type: 'feature',
      priority: 'medium',
      software: 1,
      contact_email: 'user@example.com'
    })
  });
  
  const data = await response.json();
  console.log('Feedback submitted:', data);
};

// List feedback (requires authentication)
const listFeedback = async (token) => {
  const response = await fetch('http://localhost:8000/api/v1/feedbacks/feedbacks/', {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  
  const data = await response.json();
  console.log('Feedback list:', data.results);
};
```

## 🔑 Authentication Quick Start

### Get JWT Token
```javascript
const login = async () => {
  const response = await fetch('http://localhost:8000/api/v1/auth/login/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      username: 'admin@example.com',
      password: 'password123'
    })
  });
  
  const data = await response.json();
  return data.access; // JWT token
};
```

## 📱 React Quick Integration

### Install Axios
```bash
npm install axios
```

### Create API Service
```javascript
// api/feedback.js
import axios from 'axios';

const API_BASE = 'http://localhost:8000/api/v1/feedbacks';

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const feedbackAPI = {
  // List feedback
  list: (params = {}) => api.get('/feedbacks/', { params }),
  
  // Get single feedback
  get: (id) => api.get(`/feedbacks/${id}/`),
  
  // Submit feedback
  create: (data) => api.post('/feedbacks/', data),
  
  // Add reply
  addReply: (feedbackId, data) => 
    api.post(`/feedbacks/${feedbackId}/replies/`, data),
  
  // Vote
  vote: (feedbackId, voteType) => 
    api.post(`/feedbacks/${feedbackId}/vote/`, { vote_type: voteType }),
  
  // Upload attachment
  uploadAttachment: (feedbackId, file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post(`/feedbacks/${feedbackId}/attachments/`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  },
};
```

### React Component Example
```jsx
import React, { useState, useEffect } from 'react';
import { feedbackAPI } from './api/feedback';

function FeedbackList() {
  const [feedbacks, setFeedbacks] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadFeedbacks();
  }, []);

  const loadFeedbacks = async () => {
    try {
      const response = await feedbackAPI.list();
      setFeedbacks(response.data.results);
    } catch (error) {
      console.error('Failed to load feedbacks:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleVote = async (feedbackId, voteType) => {
    try {
      await feedbackAPI.vote(feedbackId, voteType);
      // Refresh list or update local state
      loadFeedbacks();
    } catch (error) {
      console.error('Failed to vote:', error);
    }
  };

  if (loading) return <div>Loading...</div>;

  return (
    <div>
      <h2>Feedback List</h2>
      {feedbacks.map(feedback => (
        <div key={feedback.id} className="feedback-item">
          <h3>{feedback.title}</h3>
          <p>{feedback.description}</p>
          <div className="actions">
            <button onClick={() => handleVote(feedback.id, 1)}>
              👍 {feedback.vote_count}
            </button>
            <span>{feedback.status_display}</span>
          </div>
        </div>
      ))}
    </div>
  );
}
```

## 🎯 Common Use Cases

### 1. Submit Anonymous Feedback
```javascript
await feedbackAPI.create({
  title: 'Bug Report',
  description: 'App crashes on startup',
  feedback_type: 'bug',
  priority: 'high',
  software: 1,
  contact_email: 'user@example.com',
  environment_info: {
    os: 'Windows 11',
    browser: 'Chrome 120'
  }
});
```

### 2. Admin Reply to Feedback
```javascript
// Requires admin authentication
await feedbackAPI.addReply(feedbackId, {
  content: 'Thank you for your feedback. We are investigating.',
  is_internal_note: false  // Will send email
});
```

### 3. Change Feedback Status
```javascript
// Admin only
await api.patch(`/feedbacks/${feedbackId}/status/`, {
  status: 'in_progress',
  reason: 'Assigned to development team'
});
```

### 4. Upload Screenshot
```javascript
const fileInput = document.getElementById('file-input');
const file = fileInput.files[0];

await feedbackAPI.uploadAttachment(feedbackId, file);
```

## 📊 View Statistics (Admin)
```javascript
const getStats = async () => {
  const response = await api.get('/statistics/', {
    params: {
      software: 1,
      date_from: '2025-01-01',
      date_to: '2025-01-31'
    }
  });
  
  console.log('Total feedbacks:', response.data.total_feedbacks);
  console.log('By type:', response.data.feedbacks_by_type);
  console.log('Top voted:', response.data.top_voted_feedbacks);
};
```

## 🔍 Search and Filter
```javascript
// Search feedbacks
const results = await feedbackAPI.list({
  search: 'login issue',
  feedback_type: 'bug',
  status: 'submitted',
  ordering: '-created_at'
});
```

## 🚨 Error Handling
```javascript
try {
  await feedbackAPI.create(data);
} catch (error) {
  if (error.response?.status === 400) {
    // Validation errors
    const errors = error.response.data.errors;
    Object.entries(errors).forEach(([field, messages]) => {
      console.error(`${field}: ${messages.join(', ')}`);
    });
  } else if (error.response?.status === 401) {
    // Not authenticated
    console.error('Please login first');
  } else {
    // Other errors
    console.error('An error occurred:', error.message);
  }
}
```

## 📱 Mobile App Integration

### React Native Example
```javascript
import { Platform } from 'react-native';

const submitFeedback = async (feedbackData) => {
  // Add device info
  const enrichedData = {
    ...feedbackData,
    environment_info: {
      platform: Platform.OS,
      version: Platform.Version,
      device: Platform.constants?.Model,
    }
  };
  
  return feedbackAPI.create(enrichedData);
};
```

## 🔗 Useful Links

- **API Documentation**: http://localhost:8000/api/v1/docs/
- **Admin Panel**: http://localhost:8000/admin/
- **Celery Flower**: http://localhost:5555/ (if installed)

## 💡 Tips

1. **Always handle pagination** - API returns paginated results
2. **Cache software list** - It doesn't change often
3. **Use WebSocket for real-time updates** - See main documentation
4. **Implement retry logic** - For network failures
5. **Show loading states** - Better UX
6. **Handle rate limits** - Check headers for limits

## 🐛 Troubleshooting

### Email not sending?
1. Check Celery worker is running
2. Verify Redis connection
3. Check email settings in Django settings
4. Look at FeedbackEmailLog in admin

### 403 Forbidden?
1. Check authentication token
2. Verify user permissions
3. Ensure correct tenant context

### 400 Bad Request?
1. Check required fields
2. Validate data types
3. Ensure software exists

## 🎉 Next Steps

1. Customize email templates in admin
2. Add your software products
3. Test feedback submission flow
4. Configure production email settings
5. Deploy with proper Celery setup

Happy coding! 🚀
