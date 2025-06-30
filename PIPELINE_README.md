# Insurance Policy Processing Pipeline

This document describes the backend pipeline for processing insurance policies using your existing services in the specified sequence.

## Pipeline Overview

The pipeline orchestrates your existing services in the following sequence:

1. **Document Processing**: `insurance_document_processor_service` + `process_policies`
2. **Vector Processing**: `vector_service` + `ingest_policies_to_vector_db`
3. **Chunk Storage**: `store_policy_chunks`
4. **Context Update**: `proactive_advisor_service` + `update_policy_context`

## Architecture

- **Flask Application**: Web API for pipeline management
- **Celery**: Task queue for asynchronous processing
- **Redis**: Message broker and result backend
- **PostgreSQL**: Database for storing processed data

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Start Redis Server

**Windows:**
- Download Redis for Windows from https://github.com/microsoftarchive/redis/releases
- Run `redis-server.exe`

**Linux/Mac:**
```bash
redis-server
```

**Docker:**
```bash
docker run -d -p 6379:6379 redis:alpine
```

### 3. Redis Configuration (Windows)

The pipeline requires Redis to be running as a message broker and result backend. Here's how to set it up on Windows:

#### Option A: Download and Run Redis Manually

1. **Download Redis for Windows:**
   - Go to https://github.com/microsoftarchive/redis/releases
   - Download the latest release (e.g., `Redis-x64-3.0.504.zip`)
   - Extract to a folder (e.g., `C:\Users\manth\Downloads\Redis-x64-3.0.504\`)

2. **Start Redis Server:**
   ```cmd
   # Open Command Prompt as Administrator
   C:\Users\manth\Downloads\Redis-x64-3.0.504\redis-server.exe C:\Users\manth\Downloads\Redis-x64-3.0.504\redis.windows.conf
   ```

3. **Verify Redis is Running:**
   ```bash
   python -c "import redis; r = redis.Redis(); r.ping(); print('Redis is working!')"
   ```

#### Option B: Install Redis as Windows Service

1. **Install Redis Service:**
   ```cmd
   # Run as Administrator
   C:\Users\manth\Downloads\Redis-x64-3.0.504\redis-server.exe --service-install C:\Users\manth\Downloads\Redis-x64-3.0.504\redis.windows.conf
   ```

2. **Start Redis Service:**
   ```cmd
   net start Redis
   ```

3. **Stop Redis Service:**
   ```cmd
   net stop Redis
   ```

#### Option C: Using Docker (if Docker Desktop is available)

1. **Start Docker Desktop**
2. **Run Redis Container:**
   ```bash
   docker run -d --name redis-server -p 6379:6379 redis:alpine
   ```

#### Windows-Specific Celery Configuration

**Important:** On Windows, Celery workers must use the `solo` pool to avoid multiprocessing issues:

```bash
# Start Celery worker with solo pool
celery -A celery_config worker --loglevel=info --pool=solo
```

**Why use `--pool=solo` on Windows?**
- The default `prefork` pool has known issues with Windows multiprocessing
- The `solo` pool runs all tasks in a single process, avoiding these issues
- This is the recommended approach for Windows environments

#### Troubleshooting Redis on Windows

**Common Issues:**

1. **"Access is denied" errors:**
   - Run Command Prompt as Administrator
   - Check Windows Defender/firewall settings

2. **"Connection refused" errors:**
   - Ensure Redis server is actually running
   - Check if port 6379 is not blocked by firewall
   - Verify Redis is binding to `127.0.0.1:6379`

3. **Redis not starting:**
   - Check if another Redis instance is already running
   - Verify the configuration file path is correct
   - Check Windows Event Viewer for error messages

**Testing Redis Connection:**
```python
import redis
try:
    r = redis.Redis(host='localhost', port=6379, db=0)
    r.ping()
    print("✓ Redis connection successful")
except Exception as e:
    print(f"✗ Redis connection failed: {e}")
```

### 4. Set Environment Variables

Create a `.env` file with your configuration:

```env
# Database
SQLALCHEMY_DATABASE_URI=postgresql://username:password@localhost/database_name

# Google Cloud Storage
GOOGLE_CLOUD_STORAGE_BUCKET=your-bucket-name
GOOGLE_AI_API_KEY=your-api-key
GOOGLE_APPLICATION_CREDENTIALS = "path/to/your/credentials"
GCS_ORIGINAL_PDFS_PREFIX=your-bucket-name/original_pdfs/timestamp_uuid_original.pdf
GCS_STRUCTURED_JSONS_PREFIX=your_bucket_name/structured_jsons/timestamp_uuid_structured.json

# Vector Embedding Model and Dimensions Used
EMBEDDING_MODEL_ID=text-embedding-004
EMBEDDING_DIMENSIONS=768

# Celery (optional, defaults to localhost)
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

### 5. Initialize Database

```bash
flask db upgrade
```

## Running the Pipeline

### Option 1: Start Everything Together

```bash
python start_pipeline.py
```

This will start both Flask and Celery worker.

### Option 2: Start Components Separately

**Terminal 1 - Flask Application:**
```bash
python run.py
```

**Terminal 2 - Celery Worker:**
```bash
python -m celery -A celery_config worker --loglevel=info --pool=solo
```

## Usage

### Command Line Interface

The pipeline provides a command-line interface for management:

```bash
# Run full pipeline
python scripts/manage_pipeline.py pipeline document1.pdf document2.pdf --invoices POLICY001:invoice1.pdf POLICY002:invoice2.pdf

# Run single step
python scripts/manage_pipeline.py step process_documents --file-paths document1.pdf document2.pdf
python scripts/manage_pipeline.py step vector_processing --policy-numbers POLICY001 POLICY002
python scripts/manage_pipeline.py step store_chunks --policy-numbers POLICY001 POLICY002
python scripts/manage_pipeline.py step update_context --policy-numbers POLICY001 POLICY002 --invoice-paths POLICY001:invoice1.pdf

# Check task status
python scripts/manage_pipeline.py status <task_id>

# List processed policies
python scripts/manage_pipeline.py list-policies
```

### API Endpoints

The pipeline exposes REST API endpoints:

#### Upload and Process Documents
```bash
POST /pipeline/upload-and-process
Content-Type: multipart/form-data

files: [policy documents]
invoice_files: [invoice documents] (optional)
```

#### Check Task Status
```bash
GET /pipeline/status/<task_id>
```

#### Run Single Step
```bash
POST /pipeline/run-step
Content-Type: application/json

{
  "step_name": "process_documents",
  "parameters": {
    "file_paths": ["document1.pdf", "document2.pdf"]
  }
}
```

#### List Policies
```bash
GET /pipeline/policies
```

#### Get Policy Details
```bash
GET /pipeline/policy/<policy_number>
```

#### Health Check
```bash
GET /pipeline/health
```

## Pipeline Steps Details

### Step 1: Document Processing
- Uses `InsuranceDocumentProcessorService` to extract structured data from PDFs
- Stores results in `ProcessedPolicyData` table
- Returns policy numbers for next steps

### Step 2: Vector Processing
- Generates embeddings for policy chunks using `VectorService`
- Stores vectors in vector database for similarity search
- Processes all successfully extracted policies

### Step 3: Chunk Storage
- Creates policy records in main database
- Stores policy chunks for retrieval and analysis
- Links chunks to original documents

### Step 4: Context Update
- Updates policy context with roof age from invoices
- Sets renewal dates from database expiration dates
- Prompts for additional features if needed

## Monitoring and Debugging

### Task Monitoring
- Use the API endpoint `/pipeline/status/<task_id>` to monitor task progress
- Check Celery worker logs for detailed processing information
- Use the management script to check task status from command line

### Database Queries
```sql
-- Check processed policies
SELECT * FROM processed_policy_data;

-- Check policy chunks
SELECT * FROM policy_chunks;

-- Check pipeline tasks
SELECT * FROM celery_taskmeta;
```

### Logs
- Flask application logs: Check console output
- Celery worker logs: Check worker console output
- Database logs: Check PostgreSQL logs

## Error Handling

The pipeline includes comprehensive error handling:

- **File Validation**: Checks file existence and format
- **Database Errors**: Handles connection and constraint violations
- **Service Errors**: Gracefully handles failures in individual services
- **Task Retries**: Celery can retry failed tasks
- **Progress Tracking**: Real-time progress updates for long-running tasks

## Scaling Considerations

### Horizontal Scaling
- Run multiple Celery workers: `celery -A celery_config worker --loglevel=info --concurrency=4 --pool=solo` (Windows)
- **Note:** On Windows, use `--pool=solo` to avoid multiprocessing issues
- Use Redis Cluster for high availability
- Load balance Flask application instances

### Performance Optimization
- Configure Celery task routing for different step types
- Use Redis persistence for task results
- Implement task result expiration
- Monitor memory usage for large document processing

## Troubleshooting

### Common Issues

1. **Redis Connection Error**
   - Ensure Redis server is running
   - Check Redis connection settings in config
   - **Windows:** Run Command Prompt as Administrator when starting Redis
   - **Windows:** Check Windows Defender/firewall settings

2. **Database Connection Error**
   - Verify database credentials in `.env`
   - Ensure database is accessible

3. **Celery Worker Not Starting**
   - Check if Redis is running
   - Verify Celery configuration
   - Check for import errors in task modules
   - **Windows:** Use `--pool=solo` flag to avoid multiprocessing issues
   - **Windows:** "Access is denied" errors usually require running as Administrator

4. **Task Failures**
   - Check task logs for specific error messages
   - Verify input data format
   - Ensure all required services are available

### Debug Mode
Enable debug logging by setting:
```python
CELERY_WORKER_LOG_LEVEL = 'DEBUG'
```

## Security Considerations

- Secure Redis with authentication
- Use HTTPS for API endpoints in production
- Implement API rate limiting
- Validate file uploads
- Sanitize user inputs

## Future Enhancements

- **Scheduling**: Add cron-like scheduling for periodic processing
- **Notifications**: Email/SMS notifications for task completion
- **Dashboard**: Web-based monitoring dashboard
- **Batch Processing**: Optimize for large batch operations
- **Caching**: Implement result caching for repeated queries 