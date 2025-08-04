from django.db import models
from django.utils import timezone
import uuid


class BaseModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    # soft-delete
    def delete(self, using=None, keep_parents=False):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()

    # restore
    def restore(self):
        self.is_deleted = False
        self.deleted_at = None
        self.save()

    # def hard_delete(self):
    #     super(User, self).delete()

    class Meta:
        abstract = True
