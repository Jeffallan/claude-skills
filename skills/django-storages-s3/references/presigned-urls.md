# Presigned URLs

Presigned URLs grant time-limited access to private S3 objects without making
the bucket public. Two directions: **download** (presigned GET) and **upload**
(presigned POST).

## Automatic download URLs (recommended)

For a backend with `querystring_auth=True` (e.g. the `private_files` backend in
`custom-backends.md`), calling `.url` on a file field returns a presigned URL —
no manual boto3 call:

```python
doc = Document.objects.get(pk=1)
download_link = doc.contract.url   # presigned GET URL, expires per AWS_QUERYSTRING_EXPIRE
```

`AWS_QUERYSTRING_EXPIRE` (default `3600` seconds) controls expiry. The backend
**must** have `custom_domain=None`, or presigning silently breaks.

## Manual download URL (custom expiry / non-model objects)

```python
import boto3
from django.conf import settings

def get_presigned_url(s3_key: str, expiry_seconds: int = 3600) -> str:
    """Generate a time-limited GET URL for a private S3 object."""
    client = boto3.client("s3", region_name=settings.AWS_S3_REGION_NAME)
    return client.generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.AWS_STORAGE_BUCKET_NAME, "Key": s3_key},
        ExpiresIn=expiry_seconds,
    )
```

On AWS infrastructure with an IAM role, `boto3.client("s3")` picks up
credentials automatically — do not pass keys explicitly.

## Presigned upload URL (direct browser-to-S3)

Let the client upload straight to S3, bypassing your Django server — essential
for large files and to avoid request timeouts:

```python
import boto3
from django.conf import settings

def get_presigned_upload_url(
    s3_key: str,
    content_type: str = "application/octet-stream",
    expiry: int = 3600,
) -> dict:
    """Generate a presigned POST for direct browser-to-S3 uploads.

    Returns {"url": ..., "fields": {...}} — POST these as multipart/form-data
    from the browser with the file appended last.
    """
    client = boto3.client("s3", region_name=settings.AWS_S3_REGION_NAME)
    return client.generate_presigned_post(
        Bucket=settings.AWS_STORAGE_BUCKET_NAME,
        Key=s3_key,
        Fields={"Content-Type": content_type},
        Conditions=[{"Content-Type": content_type}],
        ExpiresIn=expiry,
    )
```

### Returning it from a view

```python
from django.http import JsonResponse

def upload_url_view(request):
    key = f"uploads/{request.GET['filename']}"
    content_type = request.GET.get("type", "application/octet-stream")
    return JsonResponse(get_presigned_upload_url(key, content_type))
```

### Client-side upload (sketch)

```js
const { url, fields } = await fetch("/upload-url/?filename=report.pdf").then(r => r.json());
const form = new FormData();
Object.entries(fields).forEach(([k, v]) => form.append(k, v));
form.append("file", fileInput.files[0]);  // file MUST be appended last
await fetch(url, { method: "POST", body: form });
```

## Pitfalls

- **`querystring_auth=True` + `custom_domain` set** → presigning breaks. Set
  `custom_domain=None` on private backends.
- **Clock skew** → presigned URLs are time-sensitive; ensure server time (NTP)
  is correct or signatures fail with `403`.
- **Wrong region** → a URL signed for the wrong region returns
  `AuthorizationHeaderMalformed`. Pass the bucket's actual region. Set
  `region_name` in each backend's `OPTIONS` rather than relying only on the
  global `AWS_S3_REGION_NAME`, so per-backend signing always uses the right region.
- **Caching a presigned URL past its expiry** → a presigned GET is only valid for
  `AWS_QUERYSTRING_EXPIRE` seconds. Serializing `.url()` into a DRF/HTML response
  that is cached (CDN, `cache_page`, client) longer than that window means the
  embedded links silently start returning `403` once they expire. Generate the URL
  per request, or keep the response TTL shorter than the signature lifetime.
