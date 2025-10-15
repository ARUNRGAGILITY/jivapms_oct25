from django.db import models
from django.utils import timezone


class SoftDeleteQuerySet(models.QuerySet):
    def delete(self):
        return super().update(deleted=True, active=False, updated_at=timezone.now())

    def hard_delete(self):
        return super().delete()

    def alive(self):
        return self.filter(deleted=False)

    def dead(self):
        return self.filter(deleted=True)


class SoftDeleteManager(models.Manager):
    def get_queryset(self):
        return SoftDeleteQuerySet(self.model, using=self._db).filter(deleted=False)

    def hard_delete(self):
        return SoftDeleteQuerySet(self.model, using=self._db).delete()


class BaseModelImpl(models.Model):
    name = models.CharField(max_length=100, null=True, blank=True)
    description = models.CharField(max_length=200, null=True, blank=True)
    text = models.TextField(null=True, blank=True)

    # position for sequence
    position = models.PositiveIntegerField(default=1000)

    # date details
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    # active or deleted
    active = models.BooleanField(default=True)
    deleted = models.BooleanField(default=False)

    # blocked
    blocked = models.BooleanField(default=False)
    blocked_count = models.PositiveIntegerField(default=0)

    # done and at time
    done = models.BooleanField(default=False)
    done_at = models.DateTimeField(null=True, blank=True)

    approved = models.BooleanField(default=False)

    objects = SoftDeleteManager()
    all_objects = SoftDeleteQuerySet.as_manager()

    class Meta:
        ordering = ['position']
        abstract = True

    def __str__(self):
        return self.name or ''

    def delete(self, using=None, keep_parents=False):
        self.deleted = True
        self.active = False
        self.updated_at = timezone.now()
        self.save(update_fields=['deleted', 'active', 'updated_at'])

    def hard_delete(self, using=None, keep_parents=False):
        return super().delete(using=using, keep_parents=keep_parents)
