# Nexus AI Backend - Customer Support API

A high-performance FastAPI backend for the Nexus AI customer support platform. Features AI-powered chat with agentic workflows using Gemini API, ticket management with advanced filtering, and JWT-based authentication.

![GitHub](https://img.shields.io/badge/GitHub-Charles7458/customer--support--agent--backend-blue?logo=github)
![Python](https://img.shields.io/badge/Python-3.12+-3776ab?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-009485?logo=fastapi)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-14+-336791?logo=postgresql)

## 📋 Overview

Nexus AI Backend is a robust REST API built with FastAPI that powers the customer support platform. It combines intelligent AI capabilities with traditional ticket management, real-time chat, and secure authentication.

### Core Features

- **🤖 AI Chat with Agentic Workflow** - Gemini API integration with function calling for intelligent customer interactions
- **🎟️ Advanced Ticket Management** - Full CRUD operations with filtering, pagination, and status tracking
- **💬 Real-time Chat System** - Message management and conversation history
- **🔐 JWT Authentication** - Secure token-based authentication with refresh tokens
- **📊 Database Migrations** - Alembic-managed schema versioning
- **⚡ High Performance** - Async/await support for concurrent request handling
- **📝 API Documentation** - Auto-generated Swagger/OpenAPI docs

## 🚀 Getting Started

### Prerequisites

- **Python** 3.12 or higher
- **PostgreSQL** 14 or higher
- **pip** (Python package manager)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Charles7458/customer-support-agent-backend.git
   cd customer-support-agent-backend
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Run database migrations**
   ```bash
   alembic upgrade head
   ```

6. **Start the development server**
   ```bash
   uvicorn main:app --reload
   ```

   The API will be available at `http://localhost:8000`
   - API docs: `http://localhost:8000/docs`
   - ReDoc: `http://localhost:8000/redoc`

### Development Commands

```bash
# Start development server with auto-reload
uvicorn main:app --reload

# Run migrations
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "Description of changes"

# Downgrade to previous migration
alembic downgrade -1

# Check database status
alembic current

# Run tests (if configured)
pytest

# Format code
black .

# Lint code
flake8 .
```

## 🏗️ Project Structure

```
.
├── alembic/                 # Database migrations
│   ├── versions/           # Migration files
│   └── env.py             # Alembic configuration
├── app/
│   ├── api/                # API route handlers
│   │   ├── auth.py        # Authentication endpoints
│   │   ├── chat.py        # Chat endpoints
│   │   ├── tickets.py     # Ticket management endpoints
│   │   └── ai.py          # AI response generation
│   ├── models/             # SQLAlchemy ORM models
│   ├── schemas/            # Pydantic request/response models
│   ├── services/           # Business logic
│   │   ├── auth_service.py
│   │   ├── ticket_service.py
│   │   ├── chat_service.py
│   │   └── ai_service.py
│   ├── utils/              # Utility functions
│   ├── middleware/         # Custom middleware
│   └── core/               # Core configuration
│       └── config.py       # Settings and environment variables
├── main.py                 # Application entry point
├── requirements.txt        # Python dependencies
├── .env.example           # Environment variables template
└── README.md              # This file
```

## 🔌 API Endpoints

### Authentication

| Method | Endpoint               |
| ------ | ---------------------- |
| GET    | `/auth/me`             |
| POST   | `/auth/signup`         |
| POST   | `/auth/login`          |
| POST   | `/auth/logout`         |
| DELETE | `/auth/del-acc`        |
| POST   | `/auth/support/signup` |
| POST   | `/auth/support/login`  |

### User Profile
| Method | Endpoint              |
| ------ | --------------------- |
| PUT    | `/users/update-name`  |
| PUT    | `/users/update-email` |
| PUT    | `/users/update-pswd`  |

 ### Chat
 | Method | Endpoint       |
| ------ | -------------- |
| GET    | `/chat/`       |

### Support Chat

| Method | Endpoint         |
| ------ | ---------------- |
| POST   | `/support-chat/` |


### Tickets

| Method | Endpoint                     |
| ------ | ---------------------------- |
| GET    | `/tickets/`                  |
| POST   | `/tickets/create-ticket`     |
| PUT    | `/tickets/update`            |
| POST   | `/tickets/generate-response` |

### Support-agent-facing

| Method | Endpoint                         |
| ------ | -------------------------------- |
| GET    | `/tickets/support/`              |
| POST   | `/tickets/support/create-ticket` |

### Insert endpoints
| Method | Endpoint         |
| ------ | ---------------- |
| POST   | `/orders/insert` |
| ------ | ------------------------- |
| POST   | `/orders/tracking/insert` |
| ------ | ------------- |
| POST   | `/faq/insert` |




**Example:**
```bash
# Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password"}'

# Response
{
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "name": "John Doe"
  }
}
```

### Tickets

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/tickets` | List all tickets (with filtering & pagination) |
| `POST` | `/tickets` | Create a new ticket |
| `GET` | `/tickets/{id}` | Get ticket details |
| `PUT` | `/tickets/{id}` | Update ticket |
| `DELETE` | `/tickets/{id}` | Delete ticket |
| `GET` | `/tickets/{id}/messages` | Get ticket conversation history |

**Query Parameters for `/tickets`:**
```
- status: open, closed, in_progress (filter by status)
- priority: low, medium, high (filter by priority)
- assigned_to: user_id (filter by assignee)
- page: 1 (pagination page number)
- limit: 10 (items per page)
- search: keyword (search in title and description)
```

**Example:**
```bash
# Get paginated tickets with filtering
curl -X GET "http://localhost:8000/tickets?status=open&priority=high&page=1&limit=10" \
  -H "Authorization: Bearer {access_token}"

# Response
{
  "data": [
    {
      "id": "uuid",
      "title": "Login not working",
      "description": "Cannot login to the platform",
      "status": "open",
      "priority": "high",
      "created_at": "2024-01-15T10:30:00Z",
      "assigned_to": "user_id"
    }
  ],
  "total": 45,
  "page": 1,
  "limit": 10
}
```

### Chat

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/chat/conversations` | List all conversations |
| `POST` | `/chat/conversations` | Create new conversation |
| `GET` | `/chat/conversations/{id}` | Get conversation details |
| `POST` | `/chat/conversations/{id}/messages` | Send message |
| `GET` | `/chat/conversations/{id}/messages` | Get message history |

**Example:**
```bash
# Send a message
curl -X POST http://localhost:8000/chat/conversations/{conversation_id}/messages \
  -H "Authorization: Bearer {access_token}" \
  -H "Content-Type: application/json" \
  -d '{"content": "Hello, I need help with..."}'
```

### AI Response Generation

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/generate-response` | Generate AI response for a message |

**Request Body:**
```json
{
  "prompt": "You are a helpful customer support agent",
  "message": "I can't reset my password"
}
```

**Response:**
```json
{
  "response": "I understand you're having trouble resetting your password. Here's how to fix it...",
  "status": "success"
}
```

**AI Workflow:**
The AI chat system uses Gemini API with function calling to:
1. Analyze customer messages
2. Determine intent and context
3. Call appropriate functions (look up account, check system status, etc.)
4. Generate contextual, helpful responses
5. Handle complex multi-turn conversations

## 🔑 Environment Variables

Create a `.env` file in the project root with the following key variables:

```env
# Database
ASYNC_DB_URL=postgresql://user:password@localhost:5432/nexus_ai

# JWT Configuration
SECRET_KEY=your-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Gemini API
GEMINI_API_KEY=your-gemini-api-key

# CORS
FRONTEND_URL=http://localhost:5173,http://localhost:3000

# Environment
ENVIRONMENT=development
DEBUG=True
```

**Key Variables Explanation:**

| Variable | Purpose | Example |
|----------|---------|---------|
| `ASYNC_DB_URL` | PostgreSQL connection string | `postgresql://user:pass@localhost/db` |
| `SECRET_KEY` | JWT signing key (use strong random value) | Generate with `openssl rand -hex 32` |
| `GEMINI_API_KEY` | Google Gemini API key for AI features | From Google Cloud Console |
| `FRONTEND_URL` | Allowed frontend origins (comma-separated) | `http://localhost:5173` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | JWT token expiration time | `30` |

See `.env.example` for all available variables.

## 📊 Database Setup

### Initial Setup

1. **Create PostgreSQL database:**
   ```bash
   createdb nexus_ai
   ```

2. **Run migrations:**
   ```bash
   alembic upgrade head
   ```

### Alembic Migrations

Alembic manages database schema versioning.

**Create a new migration:**
```bash
alembic revision --autogenerate -m "Add user_roles table"
```

**Apply migrations:**
```bash
alembic upgrade head
```

**Rollback to previous version:**
```bash
alembic downgrade -1
```

**Check current migration status:**
```bash
alembic current
```

**View migration history:**
```bash
alembic history
```

## 🔐 Authentication Flow

The API uses JWT (JSON Web Tokens) for authentication:

1. **Login** → Receive `access_token` and `refresh_token`
2. **API Requests** → Include `Authorization: Bearer {access_token}` header
3. **Token Expiration** → Use `refresh_token` to get new `access_token`
4. **Logout** → Token is invalidated on the backend

**Protected Endpoints:**
All endpoints except `/auth/login` and `/auth/register` require a valid JWT token.

```bash
# With token
curl -X GET http://localhost:8000/tickets \
  -H "Authorization: Bearer eyJhbGc..."
```

## 🤖 AI Agentic Workflow

The AI chat system uses Gemini API with function calling to handle customer inquiries intelligently:

- **Intent Recognition** - Understands customer needs from natural language
- **Function Calling** - Executes relevant functions (check ticket status, look up user info, etc.)
- **Multi-turn Conversations** - Maintains context across multiple messages
- **Error Handling** - Gracefully handles edge cases and provides helpful feedback

Example: Customer asks "Where's my order?" → AI calls `look_up_order()` function → Returns tracking info

## 📚 Technology Stack

| Technology | Version | Purpose |
|-----------|---------|---------|
| FastAPI | 0.104+ | Web framework |
| SQLAlchemy | 2.0+ | ORM |
| PostgreSQL | 14+ | Database |
| Alembic | 1.12+ | Migrations |
| Pydantic | 2.0+ | Data validation |
| Python-jose | Latest | JWT handling |
| Google Gemini API | Latest | AI capabilities |
| Uvicorn | Latest | ASGI server |

## ⚡ Performance Considerations

- **Async/Await** - All endpoints support concurrent requests
- **Connection Pooling** - Configured for optimal database connection management
- **Pagination** - Implement pagination on list endpoints to handle large datasets
- **Caching** - Consider caching frequently accessed data (tickets, user profiles)
- **Rate Limiting** - Implement rate limiting on sensitive endpoints like auth

## 🛠️ Troubleshooting

### Database Connection Error
```
Error: could not connect to server: Connection refused
```
**Solution:** Ensure PostgreSQL is running and `ASYNC_DB_URL` in `.env` is correct.

### JWT Token Expired
```
Error: Token has expired
```
**Solution:** Use the `refresh_token` endpoint to get a new access token.

### Gemini API Key Invalid
```
Error: Invalid API key provided
```
**Solution:** Verify `GEMINI_API_KEY` in `.env` matches your actual Gemini API key from Google Cloud Console.

### Migration Conflicts
```
Error: Target database is not up to date
```
**Solution:** Run `alembic upgrade head` to apply pending migrations.

## 📚 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com)
- [SQLAlchemy ORM](https://docs.sqlalchemy.org)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Alembic Documentation](https://alembic.sqlalchemy.org)
- [JWT Introduction](https://jwt.io)
- [Google Gemini API Docs](https://ai.google.dev)
- [Pydantic Documentation](https://docs.pydantic.dev)

## 📧 Support

For issues or questions, please create an issue in the [GitHub repository](https://github.com/Charles7458/customer-support-agent-backend/issues).

## 📝 License

This project is part of the Nexus AI customer support platform.

---

**Built with ❤️ for powerful customer support automation**
