from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User,AuthToken,UserChannel
from .tokenAuthentication import JWTAuthentication
@receiver(post_save,sender=User)
def create_token(sender, instance, created, **kwargs):
  if created:
    payload = {
      'id':instance.id,
      'email':instance.email
    }
    jwt_token = JWTAuthentication().generate_token(payload)
    AuthToken.objects.create(user=instance,token=jwt_token)
    UserChannel.objects.create(user=instance)
    # Profile.objects.create(user=instance)

