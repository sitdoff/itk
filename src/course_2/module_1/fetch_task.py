from django.db import models, transaction


class TaskQueue(models.Model):
    task_name = models.CharField(max_length=255)
    status = models.CharField(max_length=255, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.task_name


def fetch_task():
    with transaction.atomic():
        task = TaskQueue.objects.select_for_update().filter(status="pending").first()
        if task is None:
            return None
        task.status = "in_progress"
        task.save(fields=["status"])
        return task
