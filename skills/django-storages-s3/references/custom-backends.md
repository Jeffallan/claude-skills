# Custom Storage Backends

Split storage by access level: public images served over the CDN, private
documents accessed only through presigned URLs. There are two idiomatic ways to
do this.

## Option A — Named entries in the `STORAGES` dict (Django 4.2+)

Preferred on modern Django. Each named backend is just another key:

```python
STORAGES = {
    "default": { ... },      # media uploads
    "staticfiles": { ... },  # static files
    "public_images": {
        "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
        "OPTIONS": {
            "bucket_name": "mybucket-public",
            "region_name": AWS_S3_REGION_NAME,
            "default_acl": None,        # public access via bucket policy, not ACLs
            "querystring_auth": False,  # clean, unsigned URLs
            "file_overwrite": False,
            "location": "media/public",
        },
    },
    "private_files": {
        "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
        "OPTIONS": {
            "bucket_name": "mybucket-private",
            "region_name": AWS_S3_REGION_NAME,
            "default_acl": None,        # access controlled by presigning, not ACLs
            "querystring_auth": True,   # .url() returns presigned URLs automatically
            "custom_domain": None,      # MUST be None for presigning to work
            "file_overwrite": False,
            "location": "media/private",
        },
    },
}
```

> **Do not use `default_acl="public-read"` / `"private"` here.** Since April 2023,
> new S3 buckets ship with Object Ownership = *Bucket owner enforced*, which
> **disables ACLs** — any `default_acl` value other than `None` raises
> `AccessControlListNotSupported` at upload time. Make the *public* bucket public
> with a bucket policy (`s3:GetObject` on `media/public/*`) and keep the *private*
> bucket locked down, gating access through presigned URLs (`querystring_auth=True`).
> ACL string values only work on legacy buckets that explicitly re-enable ACLs
> (Object Ownership = *ACLs enabled*).

Reference a named backend on a model field:

```python
from django.core.files.storage import storages
from django.db import models

class Document(models.Model):
    image = models.ImageField(storage=storages["public_images"])
    contract = models.FileField(storage=storages["private_files"])
```

`storages["..."]` is the Django 4.2+ accessor; it resolves lazily, so it is
safe to reference at class-definition time.

## Option B — Manual helper (all Django versions)

Useful on Django < 4.2 or when you want a single source of truth that is not the
`STORAGES` dict. Define backends as plain dicts:

```python
# settings.py
PUBLIC_IMAGE_BACKEND = {
    "class": "storages.backends.s3boto3.S3Boto3Storage",
    "options": {
        "bucket_name": "mybucket-public",
        "region_name": AWS_S3_REGION_NAME,
        "default_acl": None,        # public access via bucket policy, not ACLs
        "querystring_auth": False,
        "file_overwrite": False,
        "location": "media/public",
    },
}

PRIVATE_FILE_BACKEND = {
    "class": "storages.backends.s3boto3.S3Boto3Storage",
    "options": {
        "bucket_name": "mybucket-private",
        "region_name": AWS_S3_REGION_NAME,
        "default_acl": None,        # access controlled by presigning, not ACLs
        "querystring_auth": True,   # .url() returns presigned URLs automatically
        "custom_domain": None,      # Must be None for presigned URLs to work
        "file_overwrite": False,
        "location": "media/private",
    },
}
```

Instantiate a backend from a settings dict:

```python
# myapp/storages.py
from django.conf import settings
from django.utils.module_loading import import_string

def get_storage(setting_name):
    config = getattr(settings, setting_name)
    storage_class = import_string(config["class"])
    return storage_class(**config.get("options", {}))
```

```python
# models.py
from myapp.storages import get_storage

class Document(models.Model):
    image = models.ImageField(storage=get_storage("PUBLIC_IMAGE_BACKEND"))
    contract = models.FileField(storage=get_storage("PRIVATE_FILE_BACKEND"))
```

## When to use which

| Situation | Use |
|-----------|-----|
| Django 4.2+, backend is a fixed config | Option A (`STORAGES` dict) |
| Django < 4.2 | Option B (manual helper) |
| Backend chosen dynamically at runtime | Option B |

## File Upload in Views

Saving a model with a populated file field uploads to S3 automatically — no
explicit boto3 call:

```python
# forms.py
from django import forms

class UploadForm(forms.Form):
    file = forms.FileField()

# views.py
from django.shortcuts import render, redirect

def upload_view(request):
    if request.method == "POST":
        form = UploadForm(request.POST, request.FILES)
        if form.is_valid():
            instance = Document(contract=form.cleaned_data["file"])
            instance.save()  # uploads to S3 via the field's storage backend
            return redirect("success")
    else:
        form = UploadForm()
    return render(request, "upload.html", {"form": form})
```

For large files (> 100 MB), prefer direct browser-to-S3 uploads with a
presigned POST so the file never transits your Django server — see
`presigned-urls.md`.
