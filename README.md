Audio Transcription Service

Tool Stack:

Production-oriented transcription pipeline using:

- FastAPI — API layer
- Faster-Whisper `large-v3` — speech-to-text
- Silero VAD — speech detection
- PyAV — audio decoding and normalization
- SHA-256 — audio identity/deduplication
- Pydantic Settings — configuration
- Structured logging and automated tests

The implementation focuses on audio validation, timestamps, long-audio handling, deduplication, guardrails, and a scalable production architecture.


Audio formats:

The service validates supported formats and file size before transcription. Current formats include WAV, MP3 and MPEG.

PyAV performs the actual decoding and normalizes audio to:

text
16 kHz
Mono
float32


This gives VAD and Whisper a consistent input representation.

Faster-Whisper:

The service loads `large-v3` once during application startup rather than loading the model for every request.

Current local configuration:


device=cpu
compute_type=int8
beam_size=5

Production deployments can use GPU workers and environment-based configuration.

VAD:

Silero VAD detects speech regions before Whisper inference. This avoids spending inference time on long silent portions of recordings.


Audio -> Silero VAD -> Speech Regions -> Chunks -> Whisper

Long audio:

Speech regions are split into configurable chunks:


CHUNK_DURATION_SECONDS=60


Each Whisper segment initially has chunk-relative timestamps. These are converted to absolute recording timestamps:


absolute_start = current_start + segment.start
absolute_end = current_start + segment.end


The current implementation decodes the complete audio into memory before VAD. For extremely long recordings, the production evolution would be streaming/windowed decoding so memory remains bounded.

Deduplication:

Audio is hashed with SHA-256. The hash can be used for idempotency and duplicate detection.

The current development implementation uses an in-memory set. In production this should be moved to a shared datastore such as DynamoDB, PostgreSQL or Redis.

Guardrails:

The transcript passes through a separate guardrail layer.

Current checks include:

- Empty transcription detection
- Email redaction
- 10-digit phone-number redaction

The separation allows additional governance policies without changing the Whisper implementation.

## Production API

### POST `/v1/transcriptions`

Request:


POST /v1/transcriptions
Authorization: Bearer <JWT>
Content-Type: multipart/form-data
Idempotency-Key: <unique-key>


The endpoint should:

1. Authenticate and authorize the caller.
2. Validate media type and file size.
3. Calculate an audio hash.
4. Store audio in private S3.
5. Create a durable job record.
6. Publish a lightweight job message to SQS.
7. Return `202 Accepted`.

Example response:


{
  "job_id": "job-123",
  "status": "QUEUED"
}


The API should not run long-running Whisper inference synchronously.

### GET `/v1/transcriptions/{job_id}`

Returns job state and, when complete, the transcript:


{
  "job_id": "job-123",
  "status": "COMPLETED",
  "language": "en",
  "duration": 301.2,
  "text": "Complete transcript...",
  "segments": [
    {
      "start": 0.2,
      "end": 4.8,
      "text": "Hello everyone."
    }
  ]
}


Typical states:


QUEUED
PROCESSING
RETRYING
COMPLETED
FAILED


### GET `/health/live`

Kubernetes liveness endpoint. Indicates whether the application process is alive.

### GET `/health/ready`

Kubernetes readiness endpoint. Can verify dependencies such as S3, SQS, the database and model availability before accepting traffic.

## Concurrent Uploads

The API should remain lightweight while workers handle inference:

Worker capacity can be scaled using queue depth, CPU/GPU utilization and processing latency.

For GPU inference, concurrency must be controlled according to available GPU memory.

## Storage

### Audio

Store original audio in a private S3 bucket:


s3://transcription-audio-prod/
    <tenant_id>/
        <year>/<month>/<day>/
            <job_id>/
                original.mp3


controls Needed:

- SSE-KMS encryption
- Block Public Access
- IAM policies
- Lifecycle policies
- CloudTrail auditing

### Transcript

Store structured metadata in DynamoDB or PostgreSQL:

{
  "job_id": "job-123",
  "status": "COMPLETED",
  "language": "en",
  "duration": 301.2,
  "audio_s3_key": "...",
  "text": "...",
  "segments": [],
  "model": "large-v3",
  "created_at": "..."
}


OpenSearch can be added as a secondary index when full-text transcript search is required.

## Retry and Recovery

Transient failures should be retried with exponential backoff.

Examples:
Temporary S3 error       -> Retry
Temporary worker error   -> Retry
GPU availability issue   -> Retry
Corrupt audio            -> Do not retry
Unsupported format       -> Do not retry


Jobs should have a persistent attempt count and status.

## Idempotency

Clients can provide:

http Idempotency-Key: abc123


The service stores the key against the `job_id`. A repeated request with the same key returns the existing job rather than creating another transcription.

The audio SHA-256 hash provides an additional mechanism for identifying identical files.

## Security

Production controls Needed:

- TLS
- OAuth2/JWT or API keys
- Authorization/RBAC
- Rate limiting
- File-size limits
- Content validation
- Private S3
- IAM roles
- KMS encryption
- Secret management
- Tenant isolation
- Audit logging

Sensitive audio, transcripts, tokens and credentials should never be written to application logs.

## Observability

Recommended metrics:


requests_total
transcriptions_total
failed_jobs_total
retry_count
queue_depth
transcription_latency
processing_duration
audio_duration
GPU_utilization
GPU_memory


This allows an individual transcription to be traced from API request through S3, SQS, worker inference and database persistence.


Internal implementation details should not be exposed to clients. Return a correlation ID for troubleshooting.

## Configuration

Configuration is externalized using Pydantic Settings.

Example:

```env
APP_NAME=Audio Transcription Service
APP_VERSION=1.0.0
DEBUG=False

HF_TOKEN=<token>

MODEL_NAME=large-v3
DEVICE=cpu
COMPUTE_TYPE=int8
BEAM_SIZE=5

MAX_FILE_SIZE_MB=100
CHUNK_DURATION_SECONDS=60
```

Secrets should not be committed to Git. Production secrets should be managed through a secret-management mechanism such as AWS Secrets Manager or Kubernetes Secrets.

## Testing

Tests cover:

- Audio validation
- Unsupported formats
- SHA-256 hashing
- Duplicate detection
- Guardrail behavior
- Empty transcription handling

Run:

```bash
python -m pytest -v
```

## Local Execution

Install:

```bash
pip install -r requirements.txt
```

Run:

```bash
python -m uvicorn app:app --reload
```

Swagger:

```text
http://127.0.0.1:8000/docs
```

Health:

```text
GET http://127.0.0.1:8000/health
```

## Engineering Trade-offs

**Faster-Whisper:** optimized Whisper inference and practical production deployment.

**Silero VAD:** reduces unnecessary inference over silence and enables speech-aware chunking.

**PyAV:** FFmpeg-backed decoding provides a consistent audio representation across supported formats.

**SQS:** decouples ingestion from expensive inference and provides buffering, retry and DLQ capabilities.

**DynamoDB/PostgreSQL:** durable job state and transcript metadata with fast lookup by `job_id`.

**Asynchronous processing:** prevents long-running Whisper inference from blocking API workers.

## Future Production Improvements

1. Streaming/windowed decoding for extremely long recordings.
2. GPU-backed transcription workers.
3. Kubernetes HPA/KEDA based on SQS queue depth.
4. Distributed idempotency using DynamoDB/Redis.
5. S3 lifecycle automation.
6. OpenTelemetry distributed tracing.
7. Prometheus/Grafana dashboards and alerts.
8. Multi-model routing based on latency/cost.
9. Tenant-level quotas and concurrency limits.
10. Automated transcription quality evaluation.
