# Configuration & Settings

## Package Installation

```bash
pip install django-storages[s3] boto3
```

```python
# settings.py
INSTALLED_APPS = [
    # ...
    "storages",
]
```

## Credentials

Load credentials from environment variables (via `os.environ` or `django-environ`):

```python
import os

AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
AWS_STORAGE_BUCKET_NAME = os.environ.get("AWS_STORAGE_BUCKET_NAME")
AWS_S3_REGION_NAME = os.environ.get("AWS_S3_REGION_NAME", "us-east-1")

AWS_S3_CUSTOM_DOMAIN = f"{AWS_STORAGE_BUCKET_NAME}.s3.{AWS_S3_REGION_NAME}.amazonaws.com"
AWS_DEFAULT_ACL = None           # Recommended: let bucket policy control access
AWS_S3_FILE_OVERWRITE = False    # Avoid overwriting files with the same name
AWS_QUERYSTRING_AUTH = False     # Global default. Private backends must set
                                 # querystring_auth=True in their STORAGES
                                 # OPTIONS (below) to get presigned .url() links.
```

**When not to set keys:** On AWS infrastructure (EC2, ECS, Lambda), omit
`AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` entirely — boto3 picks up the
attached IAM role automatically. This is preferred over long-lived keys.

## Django 4.2+ — the `STORAGES` dict (recommended)

```python
STORAGES = {
    "default": {
        "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
        "OPTIONS": {
            "bucket_name": AWS_STORAGE_BUCKET_NAME,
            "location": "media",
            "file_overwrite": False,
        },
    },
    "staticfiles": {
        "BACKEND": "storages.backends.s3boto3.S3StaticStorage",
        "OPTIONS": {
            "bucket_name": AWS_STORAGE_BUCKET_NAME,
            "location": "static",
        },
    },
}

MEDIA_URL = f"https://{AWS_S3_CUSTOM_DOMAIN}/media/"
STATIC_URL = f"https://{AWS_S3_CUSTOM_DOMAIN}/static/"
```

## Django < 4.2 (legacy)

```python
DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
STATICFILES_STORAGE = "storages.backends.s3boto3.S3StaticStorage"
MEDIA_URL = f"https://{AWS_S3_CUSTOM_DOMAIN}/media/"
STATIC_URL = f"https://{AWS_S3_CUSTOM_DOMAIN}/static/"
```

`DEFAULT_FILE_STORAGE` and `STATICFILES_STORAGE` are deprecated in Django 4.2+.
Use the `STORAGES` dict on any project running 4.2 or newer.

**Always** use separate `location` prefixes (e.g. `media/` and `static/`) or
separate buckets so that static and media files are never mixed — otherwise
`collectstatic` can overwrite or collide with user uploads.

## CloudFront CDN Integration

For production, serve files via CloudFront instead of directly from S3:

```python
AWS_S3_CUSTOM_DOMAIN = os.environ.get("CLOUDFRONT_DOMAIN")  # e.g. "d1234abcdef.cloudfront.net"

# Only if using signed CloudFront URLs (private distribution):
AWS_CLOUDFRONT_KEY_ID = os.environ.get("AWS_CLOUDFRONT_KEY_ID")
AWS_CLOUDFRONT_KEY = os.environ.get("AWS_CLOUDFRONT_KEY")  # PEM private key string
```

Apply the custom domain per backend in the `STORAGES` dict:

```python
STORAGES = {
    "default": {
        "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
        "OPTIONS": {
            "bucket_name": AWS_STORAGE_BUCKET_NAME,
            "custom_domain": AWS_S3_CUSTOM_DOMAIN,
            "location": "media",
        },
    },
    "staticfiles": {
        "BACKEND": "storages.backends.s3boto3.S3StaticStorage",
        "OPTIONS": {
            "bucket_name": AWS_STORAGE_BUCKET_NAME,
            "custom_domain": AWS_S3_CUSTOM_DOMAIN,
            "location": "static",
        },
    },
}
```

> A backend that serves through CloudFront should **not** also set
> `querystring_auth=True` for plain presigned S3 URLs — see
> `presigned-urls.md` and the conflict note in `testing-storages.md`.
