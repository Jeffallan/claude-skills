# Testing, IAM & Pitfalls

## Testing without hitting S3

### `InMemoryStorage` (Django 4.2+)

Override the storage backend per test so nothing touches AWS:

```python
from django.test import TestCase, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile

@override_settings(
    STORAGES={
        "default": {"BACKEND": "django.core.files.storage.InMemoryStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }
)
class FileUploadTests(TestCase):
    def test_upload(self):
        f = SimpleUploadedFile("test.txt", b"hello", content_type="text/plain")
        obj = Document.objects.create(file=f)
        self.assertIn("test", obj.file.name)
```

The `override_settings(STORAGES=...)` form above works on Django 4.2 through 6.0.
For Django < 4.2 only, use
`@override_settings(DEFAULT_FILE_STORAGE="django.core.files.storage.FileSystemStorage")`
— that setting was removed in Django 5.1, so it has no effect on 5.1+.

### `moto` — mock the S3 API itself

Use when the code under test calls boto3 directly (e.g. presigned URLs):

```bash
pip install moto[s3]
```

```python
import boto3
from moto import mock_aws

@mock_aws
def test_presigned_url():
    conn = boto3.client("s3", region_name="us-east-1")
    conn.create_bucket(Bucket="test-bucket")
    conn.put_object(Bucket="test-bucket", Key="test.txt", Body=b"data")

    url = get_presigned_url("test.txt")
    assert "test.txt" in url
```

| Use | When |
|-----|------|
| `InMemoryStorage` / `override_settings` | Testing model/field/upload behavior |
| `moto` | Testing direct boto3 calls (presigned URLs, custom clients) |

## IAM Policy (minimum required)

Grant the app's IAM user/role only object-level access plus `ListBucket`:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["s3:GetObject", "s3:PutObject", "s3:DeleteObject"],
      "Resource": "arn:aws:s3:::your-bucket-name/*"
    },
    {
      "Effect": "Allow",
      "Action": ["s3:ListBucket"],
      "Resource": "arn:aws:s3:::your-bucket-name"
    }
  ]
}
```

Note the two different ARNs: object actions target `bucket/*`, while
`ListBucket` targets the bucket itself (`bucket`, no `/*`). Prefer attaching
this to a role over creating long-lived access keys.

## Common Pitfalls

- **`querystring_auth=True` + `custom_domain`** — These conflict. Presigned URLs
  require the default S3 domain, so set `custom_domain=None` on private backends.
- **ACL errors on ACL-disabled buckets** — Set `AWS_DEFAULT_ACL=None` and rely on
  bucket policies. Since April 2023, new S3 buckets have ACLs disabled by default,
  so `default_acl="public-read"` raises `AccessControlListNotSupported`.
- **`collectstatic` uploading to the wrong location** — Ensure the `staticfiles`
  backend has `location="static"` so it never mixes with media.
- **Credentials in `settings.py`** — Always load via env vars or IAM roles; never
  hardcode or commit secrets.
- **Removed storage settings** — `DEFAULT_FILE_STORAGE` and `STATICFILES_STORAGE`
  were deprecated in Django 4.2 and **removed in Django 5.1**. They are silently
  ignored on 5.1, 5.2 LTS, and 6.0. Use the `STORAGES` dict on 4.2+.
- **Large uploads timing out** — For files > 100 MB, use presigned upload URLs for
  direct browser-to-S3 uploads to bypass the Django server.
- **`file_overwrite=False` orphans replaced files** — With overwrite disabled, a
  re-upload to the same field writes a *new* suffixed key (`avatar_a1b2c3.png`)
  and the previous object is **not** deleted — S3 grows unbounded. You own the
  cleanup: capture the old name before saving and delete it after, e.g.
  `old = instance.avatar.name; ...; instance.avatar.storage.delete(old)`. This
  is a silent storage-cost leak, not an error.
- **Missing `Content-Type`** — S3 may default to `binary/octet-stream`.
  django-storages detects content type automatically by default; only override
  via `AWS_S3_OBJECT_PARAMETERS` if you need to force it.
