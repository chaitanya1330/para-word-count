# Para Word Count - Complete Project Documentation

## Table of Contents
1. [Project Overview](#project-overview)
2. [Tech Stack](#tech-stack)
3. [System Architecture](#system-architecture)
4. [Data Models](#data-models)
5. [How Celery Works](#how-celery-works)
6. [API Endpoints](#api-endpoints)
7. [User Flow](#user-flow)
8. [Component Interactions](#component-interactions)
9. [Deployment](#deployment)

---

## Project Overview

**Para Word Count** is a Django-based web application that allows users to upload text paragraphs and perform word frequency analysis. The application uses asynchronous task processing with Celery to tokenize and count word occurrences efficiently.

### Key Features
- User registration and authentication
- Text paragraph submission via REST API
- Automatic word tokenization and counting (using Celery)
- Word search across all paragraphs
- PostgreSQL database for persistence
- Redis for caching and Celery message broker
- Docker containerization
- RESTful API architecture

---

## Tech Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Backend Framework** | Django 6.0.2 | Web framework |
| **API** | Django REST Framework 3.14.0 | REST API endpoints |
| **Task Queue** | Celery 5.3.4 | Asynchronous task processing |
| **Message Broker** | Redis 5.0.1 | Celery message broker & cache |
| **Database** | PostgreSQL (psycopg2) | Primary data store |
| **WSGI Server** | Gunicorn 21.2.0 | Production server |
| **Authentication** | Django Auth | User registration & login |
| **Containerization** | Docker & Docker Compose | Deployment |

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     CLIENT / FRONTEND                        │
│          (Web Interface or API Client)                        │
└────────────────────┬────────────────────────────────────────┘
                     │
                     │ HTTP Requests
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                   DJANGO WEB SERVER                          │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ URL Routes → Views → Serializers → API Handlers     │  │
│  │ - Registration View                                   │  │
│  │ - Login View                                          │  │
│  │ - Home View                                           │  │
│  │ - save_paragraph_api                                 │  │
│  │ - search_word_api                                    │  │
│  └──────────────────────────────────────────────────────┘  │
│                     │                                        │
└─────────────────────┼────────────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┐
        │             │             │
        ▼             ▼             ▼
    ┌────────┐ ┌──────────┐ ┌─────────────┐
    │ Queue  │ │Database  │ │ Redis Cache │
    │ Tasks  │ │ (Setup & │ │ & Broker    │
    │        │ │ Queries) │ │             │
    │PostgreSQL      │ │             │
    └────────┘ └──────────┘ └─────────────┘
        │
        ▼
    ┌────────────────────────┐
    │  CELERY TASK QUEUE     │
    │  (Redis Broker)        │
    └────────────────────────┘
        │
        ▼
    ┌────────────────────────┐
    │ CELERY WORKERS         │
    │ - tokenize_paragraph   │
    │   task execution       │
    └────────────────────────┘
        │
        ▼
    ┌────────────────────────┐
    │  PostgreSQL Database   │
    │  Write results back    │
    └────────────────────────┘
```

---

## Data Models

### 1. **User Model** (Custom)
```python
class User(models.Model):
    name: CharField(max_length=255)
    email: EmailField(unique=True)
    date_of_birth: DateField
    created_date: DateTimeField(auto_now_add=True)
    modified_date: DateTimeField(auto_now=True)
```
- Stores custom user information
- Email is unique per user
- Separate from Django's built-in User model

### 2. **Paragraph Model**
```python
class Paragraph(models.Model):
    user: ForeignKey(AuthUser, CASCADE)  # Links to Django's User
    raw_text: TextField()
    created_at: DateTimeField(auto_now_add=True)
    
    Meta: ordered by creation date (newest first)
```
- Stores raw text submitted by users
- Links to Django's built-in User model for authentication
- Automatically ordered by creation date
- Each user can have multiple paragraphs

### 3. **WordOccurrence Model**
```python
class WordOccurrence(models.Model):
    paragraph: ForeignKey(Paragraph, CASCADE)
    word: CharField(max_length=255, db_index=True)
    count: IntegerField(default=1)
    
    Meta:
        unique_together: ('paragraph', 'word')
        indexes: Index on (word, -count)
```
- Stores word frequency data for each paragraph
- One WordOccurrence record per unique word per paragraph
- Indexed on `word` and `count` for fast searches
- Unique constraint prevents duplicate word entries

### Database Relationships Diagram
```
Django User (built-in)
    │
    └──── (1 to Many) ──── Paragraph
                               │
                               └──── (1 to Many) ──── WordOccurrence
```

---

## How Celery Works

### 1. **Celery Configuration** (`para_word_count/celery.py`)

```python
import os
from celery import Celery

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'para_word_count.settings')

# Initialize Celery app
app = Celery('para_word_count')

# Load configuration from Django settings
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks from all registered Django apps
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
```

**What happens here:**
- Celery app is initialized and named 'para_word_count'
- Configuration is loaded from Django settings with `CELERY_` prefix
- `autodiscover_tasks()` automatically finds tasks.py files in apps
- The debug_task is provided for testing

### 2. **Celery Task Definition** (`user/tasks.py`)

```python
@shared_task
def tokenize_paragraph(paragraph_id):
    """
    Text tokenization process:
    1. Fetch paragraph from database
    2. Convert text to lowercase
    3. Extract words using regex (\b\w+\b)
    4. Count occurrences of each word
    5. Save to WordOccurrence model
    """
    
    try:
        paragraph = Paragraph.objects.get(id=paragraph_id)
        
        # Step 1: Extract words (case-insensitive)
        text = paragraph.raw_text.lower()
        words = re.findall(r'\b\w+\b', text)  # Regex finds word boundaries
        
        # Step 2: Count occurrences
        word_count = {}
        for word in words:
            if len(word) > 1:  # Ignore single-char words
                word_count[word] = word_count.get(word, 0) + 1
        
        # Step 3: Save to database
        for word, count in word_count.items():
            WordOccurrence.objects.get_or_create(
                paragraph=paragraph,
                word=word,
                defaults={'count': count}
            )
        
        # Return success metadata
        return {
            'status': 'success',
            'paragraph_id': paragraph_id,
            'unique_words': len(word_count),
            'total_words': len(words)
        }
        
    except Paragraph.DoesNotExist:
        return {'status': 'error', 'message': 'Paragraph not found'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}
```

### 3. **Celery Task Execution Flow**

#### Current Implementation (Synchronous):
```python
# In save_paragraph_api view:
for para_text in paragraphs_text:
    paragraph = Paragraph.objects.create(user=request.user, raw_text=para_text)
    tokenize_paragraph(paragraph.id)  # ← Executed immediately
    created_paragraphs.append(paragraph.id)
```

**Flow:**
1. User submits paragraph via API
2. Django creates Paragraph record in database
3. `tokenize_paragraph()` is called directly (NOT queued)
4. Task processes immediately before response is sent
5. WordOccurrence records are created
6. User gets response with results

#### How to Make It Asynchronous:
To make it truly asynchronous, change to:
```python
# Queue the task instead of executing immediately
tokenize_paragraph.delay(paragraph.id)  # .delay() queues to Redis

# Returns immediately with task ID
# Worker processes in background
```

### 4. **Celery Message Broker (Redis)**

Redis acts as the message broker:
1. Django sends task message to Redis queue
2. Celery worker pulls message from queue
3. Worker executes the tokenize_paragraph task
4. Results stored back in database
5. Tasks can be retried if they fail

**Docker Compose Redis Service:**
```yaml
redis:
  image: redis:latest
  ports:
    - "6379:6379"
  volumes:
    - redis_data:/data
```

### 5. **Starting Celery Worker**

To run Celery worker (after making tasks async):
```bash
# Terminal 1: Start Celery worker
celery -A para_word_count worker -l info

# Terminal 2: (Optional) Monitor tasks
celery -A para_word_count events
```

---

## API Endpoints

### 1. **User Registration**
```
POST /user/register/
Content-Type: application/x-www-form-urlencoded

username=john&password=pass123&email=john@example.com
```

**Response:**
```
Redirects to login page with success message
```

**Backend Process:**
1. UserRegisterForm validates input
2. User saved to Django's User model
3. Sends welcome email (best effort)
4. Redirects to login

---

### 2. **User Login**
```
POST /user/login/
Content-Type: application/x-www-form-urlencoded

username=john&password=pass123
```

**Response:**
```
Redirects to home page if successful
Error message if credentials invalid
```

---

### 3. **Save Paragraph API** ⭐ **(Uses Celery)**
```
POST /api/save-paragraph/
Authorization: Bearer <token>
Content-Type: application/json

{
    "raw_text": "First paragraph...\n\n\nSecond paragraph..."
}
```

**Request Flow:**
```
1. User sends text with multiple paragraphs
2. Django view splits text by blank lines (\n\n+)
3. For each paragraph:
   a. Save Paragraph record to database
   b. Call tokenize_paragraph(paragraph_id)  [CELERY TASK]
   c. Task processes words and counts
   d. WordOccurrence records created
4. Return success response with paragraph IDs
```

**Response:**
```json
{
    "status": "success",
    "message": "Saved and processed 2 paragraphs successfully",
    "paragraphs_created": 2,
    "paragraph_ids": [1, 2]
}
```

**Code Flow:**
```python
# views.py - save_paragraph_api()
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def save_paragraph_api(request):
    raw_text = request.data.get('raw_text', '').strip()
    
    # Split into paragraphs (separated by 2+ newlines)
    paragraphs_text = re.split(r'\n\n+', raw_text)
    paragraphs_text = [p.strip() for p in paragraphs_text if p.strip()]
    
    created_paragraphs = []
    for para_text in paragraphs_text:
        # Create in database
        paragraph = Paragraph.objects.create(user=request.user, raw_text=para_text)
        
        # ⭐ CELERY TASK CALLED HERE
        tokenize_paragraph(paragraph.id)  # Currently synchronous
        # tokenize_paragraph.delay(paragraph.id)  # Would be asynchronous
        
        created_paragraphs.append(paragraph.id)
    
    return Response({'status': 'success', ...})
```

---

### 4. **Search Word API** ⭐
```
GET /api/search-word/?word=python
Authorization: Bearer <token>
```

**Request Flow:**
```
1. User queries for a word
2. Django searches WordOccurrence model
3. Finds top 10 matches sorted by count
4. Returns paragraphs containing word with frequency
```

**Query:**
```python
# Efficient database query with:
# - Filtering by word (indexed)
# - Joining with Paragraph (select_related)
# - Sorting by count (indexed)
# - Limiting to 10 results

word_occurrences = WordOccurrence.objects.filter(
    word=word
).select_related('paragraph').order_by('-count')[:10]
```

**Response:**
```json
{
    "status": "success",
    "word": "python",
    "results_count": 2,
    "results": [
        {
            "paragraph_id": 1,
            "user_name": "john",
            "raw_text": "Python is a great programming language...",
            "word_count": 5,
            "created_at": "2025-02-15T10:30:00Z"
        },
        {
            "paragraph_id": 2,
            "user_name": "jane",
            "raw_text": "Python makes development faster...",
            "word_count": 3,
            "created_at": "2025-02-15T11:20:00Z"
        }
    ]
}
```

---

## User Flow

### Complete User Journey

#### 1. **Registration Flow**
```
User fills registration form
    ↓
POST /user/register/
    ↓
UserRegisterForm validates
    ↓
User saved to database
    ↓
Welcome email sent (optional)
    ↓
Redirect to login page
```

#### 2. **Authentication Flow**
```
User logs in with credentials
    ↓
POST /user/login/
    ↓
Django authenticates against User model
    ↓
Session created
    ↓
Redirect to /user/home/
```

#### 3. **Paragraph Upload & Processing Flow**
```
User authenticated (has session/token)
    ↓
POST /api/save-paragraph/ with text
    ↓
Django splits text by blank lines
    ↓
For each paragraph:
    ├─ Create Paragraph record
    ├─ Trigger tokenize_paragraph task [CELERY]
    │   ├─ Fetch paragraph
    │   ├─ Convert to lowercase
    │   ├─ Extract words with regex
    │   ├─ Count occurrences
    │   └─ Save WordOccurrence records
    └─ Return paragraph ID
    ↓
API returns success response
```

#### 4. **Word Search Flow**
```
User authenticated
    ↓
GET /api/search-word/?word=python
    ↓
Django queries WordOccurrence model
    ↓
Filters where word = 'python'
    ↓
Joins with Paragraph and User data
    ↓
Sorts by count (descending)
    ↓
Limits to 10 results
    ↓
Returns JSON with results
```

### Authentication & Permissions

```python
# Login required for web views
@login_required(login_url='login')
def home(request):
    return render(request, 'user/home.html')

# Authentication required for API endpoints
@permission_classes([IsAuthenticated])
def save_paragraph_api(request):
    # request.user contains current authenticated user
    paragraph = Paragraph.objects.create(user=request.user, raw_text=text)
```

---

## Component Interactions

### How Everything Connects: User API Submission Example

#### Scenario: User posts 2 paragraphs about Python

**Step 1: API Request**
```
POST /api/save-paragraph/
Content-Type: application/json
Authorization: Bearer token

{
    "raw_text": "Python is a programming language widely used for web development, data science, and automation.\n\n\nPython's simplicity makes it a favorite among beginners and professionals alike."
}
```

**Step 2: Django Routing**
```
URL Pattern: /api/save-paragraph/
    ↓
Routes to: save_paragraph_api() view
    ↓
Requires: IsAuthenticated permission
    ↓
request.user = authenticated user from token
```

**Step 3: Text Processing in View**
```python
raw_text = request.data.get('raw_text')
# "Python is a programming language...\n\n\nPython's simplicity..."

paragraphs_text = re.split(r'\n\n+', raw_text)
# Result: [
#     "Python is a programming language widely used for web development, data science, and automation.",
#     "Python's simplicity makes it a favorite among beginners and professionals alike."
# ]
```

**Step 4: Database Operations**
```
For each paragraph text:

Iteration 1:
  → Paragraph.objects.create(
        user=authenticated_user,
        raw_text="Python is a programming language..."
    )
    # Creates: Paragraph(id=1, user_id=5, raw_text="...")
    
  → tokenize_paragraph(1)
    # Task executed HERE

Iteration 2:
  → Paragraph.objects.create(
        user=authenticated_user,
        raw_text="Python's simplicity makes..."
    )
    # Creates: Paragraph(id=2, user_id=5, raw_text="...")
    
  → tokenize_paragraph(2)
    # Task executed HERE
```

**Step 5: Celery Task Execution (tokenize_paragraph)**

For Paragraph ID 1:
```
1. Fetch: paragraph = Paragraph.objects.get(id=1)

2. Extract text: text = "python is a programming language..."
   (converted to lowercase)

3. Find words using regex \b\w+\b:
   ['python', 'is', 'a', 'programming', 'language', ...]
   (single-char words like 'a' removed)

4. Count occurrences:
   {
       'python': 1,
       'is': 1,
       'a': 1,
       'programming': 1,
       'language': 1,
       ...
   }

5. Save to database:
   WordOccurrence.objects.create(paragraph_id=1, word='python', count=1)
   WordOccurrence.objects.create(paragraph_id=1, word='is', count=1)
   WordOccurrence.objects.create(paragraph_id=1, word='language', count=1)
   ... (repeat for all words)

6. Return success metadata:
   {
       'status': 'success',
       'paragraph_id': 1,
       'unique_words': 15,
       'total_words': 20
   }
```

Same happens for Paragraph ID 2...

**Step 6: API Response**
```json
{
    "status": "success",
    "message": "Saved and processed 2 paragraphs successfully",
    "paragraphs_created": 2,
    "paragraph_ids": [1, 2]
}
```

**Step 7: Database State After Processing**
```
Paragraph table:
┌─────┬────────┬─────────────────────────────────────────┐
│ id  │ user_id│ raw_text                                 │
├─────┼────────┼─────────────────────────────────────────┤
│ 1   │ 5      │ Python is a programming language...     │
│ 2   │ 5      │ Python's simplicity makes it a...       │
└─────┴────────┴─────────────────────────────────────────┘

WordOccurrence table:
┌─────┬──────────────┬────────┬───────┐
│ id  │ paragraph_id │ word   │ count │
├─────┼──────────────┼────────┼───────┤
│ 1   │ 1            │ python │ 1     │
│ 2   │ 1            │ is     │ 1     │
│ 3   │ 1            │ language│ 1    │
│ ... │ ...          │ ...    │ ...   │
│ 20  │ 2            │ python │ 1     │
│ 21  │ 2            │ simplicity│ 1  │
└─────┴──────────────┴────────┴───────┘
```

**Step 8: User Searches for "python"**
```
GET /api/search-word/?word=python

Query executed:
WordOccurrence.objects
    .filter(word='python')
    .select_related('paragraph')
    .order_by('-count')[:10]

Results returned:
[
    {
        "paragraph_id": 1,
        "user_name": "john",
        "word_count": 1,
        ...
    },
    {
        "paragraph_id": 2,
        "user_name": "john",
        "word_count": 1,
        ...
    }
]
```

---

## Deployment

### Docker Composition

```yaml
Services:
  web ─→ Django app (port 8000)
         ├─ Runs: python manage.py migrate && gunicorn
         └─ Depends on: postgres, redis

  postgres ─→ Database (port 5432)
             └─ Volume: postgres_data

  redis ─→ Cache & Message Broker (port 6379)
           └─ Volume: redis_data
```

### Running Locally

```bash
# Start all services
docker-compose up -d

# Run migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser

# View logs
docker-compose logs -f web

# Stop services
docker-compose down
```

### Production Celery Worker

To run async task workers:
```bash
# Start Celery worker (separate container)
docker-compose run web celery -A para_word_count worker -l info

# Or in docker-compose.yml add:
worker:
  build: .
  command: celery -A para_word_count worker -l info
  depends_on:
    - redis
    - postgres
```

---

## Key Takeaways: How Celery Integrates

1. **Celery Setup** - Configured in `para_word_count/celery.py` to use Django settings
2. **Task Definition** - `tokenize_paragraph()` in `user/tasks.py` does the actual work
3. **Task Triggering** - Called from `save_paragraph_api()` view
4. **Message Broker** - Redis queues tasks (currently synchronous, can be made async)
5. **Task Execution** - Celery worker processes tasks and saves results
6. **Result Handling** - Results stored back in WordOccurrence model

**Current Flow:** Synchronous (tasks executed immediately)
**Can Be:** Asynchronous (tasks queued, processed in background)

---

## Summary

The **Para Word Count** application is a full-stack Django system that:
1. Authenticates users
2. Accepts paragraph uploads via REST API
3. Processes text with Celery tasks (tokenization & word counting)
4. Stores results in PostgreSQL
5. Provides search functionality across all paragraphs
6. Runs in Docker containers
7. Uses Redis for message brokering and caching

All components work together seamlessly through Django's ORM, REST Framework, and Celery integration.

---

*Documentation for Para Word Count Project*
*Generated: February 15, 2026*
