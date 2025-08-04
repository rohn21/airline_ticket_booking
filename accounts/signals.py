from django.db.models.signals import post_save
from django.dispatch import receiver
from allauth.account.signals import email_confirmed
from .models import User, Profile

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    else:
        instance.profile.save()

@receiver(email_confirmed)
def update_email_verified_status(request, email_address, **kwargs):
    user = email_address.user
    user.is_email_verified = True
    user.save()