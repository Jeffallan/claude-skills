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

The `STORAGES` dict is unchanged across Django 4.2, 5.x, and 6.0 — the same
config above is correct on every release from 4.2 onward. Nothing extra is
needed for Django 5.2 LTS or 6.0.

## Django < 4.2 (legacy)

```python
DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
STATICFILES_STORAGE = "storages.backends.s3boto3.S3StaticStorage"
MEDIA_URL = f"https://{AWS_S3_CUSTOM_DOMAIN}/media/"
STATIC_URL = f"https://{AWS_S3_CUSTOM_DOMAIN}/static/"
```

`DEFAULT_FILE_STORAGE` and `STATICFILES_STORAGE` were deprecated in Django 4.2
and **removed in Django 5.1**. They still function on 4.2 and 5.0 only — on 5.1,
5.2 LTS, and 6.0 they are gone and silently ignored, so the `STORAGES` dict is
mandatory there. Use `STORAGES` on any project running 4.2 or newer; only reach
for these settings on Django < 4.2.

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

### Signed CloudFront URLs (private distributions)

When `AWS_CLOUDFRONT_KEY_ID` and `AWS_CLOUDFRONT_KEY` are set and `custom_domain`
points at the CloudFront domain, django-storages signs URLs **automatically** —
`.url()` returns a signed CloudFront URL, no manual boto3 call:

```python
AWS_CLOUDFRONT_KEY_ID = os.environ["AWS_CLOUDFRONT_KEY_ID"]   # public key ID
AWS_CLOUDFRONT_KEY = os.environ["AWS_CLOUDFRONT_KEY"]         # PEM private key
AWS_QUERYSTRING_EXPIRE = 3600                                  # signature lifetime

doc.contract.url   # → https://d123.cloudfront.net/...?Expires=...&Signature=...&Key-Pair-Id=...
```

Signing requires the `cryptography` package (`pip install django-storages[cloudfront]`);
without it django-storages cannot build the signature and falls back to an
unsigned URL, so private objects return `403`.

If you do **not** need signed access (public distribution), omit both
`AWS_CLOUDFRONT_KEY*` vars entirely — setting them only matters for private
distributions. This is distinct from S3 presigning (`presigned-urls.md`), which
signs against S3 directly rather than CloudFront.

## Per-Environment Backends

Layer storage by environment so tests and local dev never touch S3. With
split settings modules, override `STORAGES` per environment.

**Every override must define _both_ `default` and `staticfiles`.** Django does
not merge your `STORAGES` with the defaults — it uses your dict verbatim
(`settings.STORAGES.copy()`), so omitting `staticfiles` makes the `{% static %}`
tag, `collectstatic`, and admin CSS raise
`InvalidStorageError: Could not find config for 'staticfiles'`.

```python
_STATIC = {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"}

# settings/dev.py — local filesystem
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": _STATIC,
}

# settings/test.py — in-memory, nothing persists
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.InMemoryStorage"},
    "staticfiles": _STATIC,
}

# settings/prod.py — S3 (the full STORAGES dict shown above, with both keys)
```

Keep the S3 backend confined to production (and staging); see
`testing-storages.md` for the `override_settings` equivalent in individual tests.
