# Insurance Policy Parser

A comprehensive insurance policy processing application that uses AI to extract, analyze, and query policy documents. Built with Flask backend and React frontend.

## 🚀 Features

### Core Functionality
- **Document Processing**: Upload and process insurance policy PDFs using AI
- **Policy Query System**: Ask natural language questions about policies
- **Roofing Invoice Processing**: Upload roofing invoices with policy linking
- **Property Features**: Track property features and roof age
- **Policy Context Updates**: Update policy renewal dates and property features
- **Vector Search**: AI-powered document search and retrieval

### Technical Features
- **AI-Powered Extraction**: Google AI for text extraction and analysis
- **Cloud Storage**: Google Cloud Storage for document storage
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Background Processing**: Celery with Redis for async tasks
- **Modern UI**: React with TypeScript and Tailwind CSS
- **Real-time Updates**: WebSocket integration for live processing

## 🏗️ Architecture

### Backend (Flask + SQLAlchemy)
- **Port**: 5001
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Processing**: Celery + Redis for async tasks
- **API**: RESTful endpoints with CORS support

### Frontend (React + TypeScript)
- **Port**: 5173
- **UI**: React with Radix UI components
- **State**: TanStack Query for server state
- **Styling**: Tailwind CSS

## 🛠️ Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL database
- Redis (optional - for Celery tasks)
- Google Cloud Project with billing enabled

### 1. Clone and Setup
```bash
git clone <repository>
cd InsurancePolicyParser
```

### 2. Backend Setup
```bash
# Create virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1  # Windows
source venv/bin/activate     # Mac/Linux

# Install dependencies
pip install -r requirements.txt
```

### 3. Frontend Setup
```bash
cd frontend
npm install
cd ..
```

### 4. Environment Configuration
Create a `.env` file with your configuration:

```env
# Flask Configuration
SECRET_KEY=your-secret-key-here
FLASK_ENV=development

# Database Configuration
SQLALCHEMY_DATABASE_URI=postgresql://username:password@localhost/database_name

# Google Cloud Storage Configuration
GOOGLE_CLOUD_STORAGE_BUCKET=your-bucket-name
GCS_ORIGINAL_PDFS_PREFIX=original/
GCS_STRUCTURED_JSONS_PREFIX=structured/

# Google AI Configuration
GOOGLE_AI_API_KEY=your-google-ai-api-key
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json

# Redis Configuration (optional)
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

### 5. Initialize Database
```bash
flask db upgrade
```

### 6. Start the Application

#### Option A: Use the integrated script
```bash
.\start_both.bat
```

#### Option B: Manual start
```bash
# Terminal 1 - Backend
python run.py

# Terminal 2 - Frontend
cd frontend
npm run dev
```

### 7. Access the Application
- **Frontend**: http://localhost:5000
- **Backend API**: http://localhost:5001
- **Health Check**: http://localhost:5001/pipeline/health

## 📊 API Endpoints

### Core API
- `GET /api/dashboard/stats` - Dashboard statistics
- `GET /api/policies` - List policies with pagination
- `GET /api/policies/:id` - Get specific policy
- `GET /api/policies/search?q=query` - Search policies
- `POST /api/policies/upload` - Upload policy document
- `POST /api/roofing-invoices/upload` - Upload roofing invoice
- `POST /api/policies/query` - Query policy documents
- `PATCH /api/policies/:id/context` - Update policy context

### Pipeline API
- `POST /pipeline/upload-and-process` - Process documents with pipeline
- `GET /pipeline/status/:task_id` - Get pipeline status
- `GET /pipeline/health` - Health check

## 🔧 Development

### Project Structure
```
InsurancePolicyParser/
├── app/                    # Flask backend application
│   ├── routes/            # API routes
│   ├── services/          # Business logic services
│   ├── models.py          # Database models
│   └── db.py              # Database configuration
├── frontend/              # React frontend
│   └── client/
│       ├── src/
│       │   ├── components/ # React components
│       │   ├── pages/      # Page components
│       │   ├── hooks/      # Custom hooks
│       │   └── lib/        # Utilities and API client
├── scripts/               # Utility scripts
├── tests/                 # Test files
├── migrations/            # Database migrations
└── data/                  # Sample data
```

### Key Components

#### Backend Services
- **InsuranceDocumentProcessorService**: Processes PDF documents using AI
- **VectorService**: Handles document embeddings and vector search
- **ProactiveAdvisorService**: Provides proactive policy recommendations

#### Frontend Components
- **EnhancedUpload**: Unified upload interface for policies and invoices
- **PolicyQuery**: AI-powered policy query system
- **PolicyContext**: Policy context update interface
- **Dashboard**: Main application dashboard

### Database Models
- **ProcessedPolicyData**: Stores processed policy information
- **PolicyChunk**: Stores document chunks for vector search
- **RoofingInvoice**: Stores roofing invoice data
- **ProcessingTask**: Tracks processing task status

## 🧪 Testing

### Run Tests
```bash
# Backend tests
python test_complete_workflow.py
python test_policy_context_update.py
python test_roofing_invoice_features.py

# Frontend tests
cd frontend
npm test
```

### Test Features
- Policy document upload and processing
- Roofing invoice upload with policy linking
- Policy query system with AI responses
- Property features and roof age calculation
- Policy context updates

## 🚀 Deployment

### Local Production Setup
1. Set up PostgreSQL database
2. Configure Google Cloud services
3. Set up Redis for Celery tasks
4. Configure environment variables
5. Run database migrations
6. Start the application

## 🐛 Troubleshooting

### Common Issues

1. **Database Connection Errors**
   - Verify database connection string in `.env`
   - Run `flask db upgrade` to initialize database

2. **Google AI API Errors**
   - Check API key is correct
   - Ensure billing is enabled on Google Cloud project
   - Verify Generative AI API is enabled

3. **Redis Connection Errors**
   - Install Redis locally or use Docker
   - Or comment out Celery-related code for basic functionality

4. **Frontend Connection Errors**
   - Ensure backend is running on port 5001
   - Check CORS configuration
   - Verify API endpoints are accessible

### Debug Steps
1. Check application logs for detailed error messages
2. Verify all environment variables are set correctly
3. Test individual endpoints with curl or Postman
4. Check frontend console for JavaScript errors

## 📈 Performance

### Optimization Tips
- Use Redis for caching and session storage
- Implement database connection pooling
- Enable compression for API responses
- Use CDN for static assets in production
- Implement rate limiting for API endpoints

### Monitoring
- Application health checks
- Database query performance
- API response times
- Error tracking and logging

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues or questions:
1. Check the application logs
2. Review the troubleshooting section
3. Create an issue on GitHub
4. Contact the development team

---

**Note**: This application requires Google Cloud services for full functionality. Ensure you have the necessary API keys and billing enabled for production use. 