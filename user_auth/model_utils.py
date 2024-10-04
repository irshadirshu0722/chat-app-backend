# user_auth/models_utils.py
from django.db import models
from cloudinary.models import CloudinaryField

class CreatedUpdatedAtModel():
    _created_at = models.DateTimeField(auto_now_add=True)
    _updated_at = models.DateTimeField(auto_now=True)
class ProfileMedia(models.Model):
  profile = CloudinaryField("image", folder="user/profile",transformation={"quality": "auto:eco"},null=True,blank=True)
  @property
  def profile_url(self):
    return self.image.url
