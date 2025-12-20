from django.contrib.auth.models import Group
from django.dispatch import receiver
from django.db.models.signals import post_migrate


@receiver(post_migrate)
def create_manager_group(sender, **kwargs):
    if sender.label != 'task_api':
        return
    manager_group,created = Group.objects.get_or_create(name='Manager')
    if created:
        print('manager group created')

