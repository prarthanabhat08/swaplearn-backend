from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

# USERS
class User(models.Model):
    user_id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=100)
    full_name = models.CharField(max_length=200)
    email = models.EmailField()
    password = models.CharField(max_length=100)

    def __str__(self):
        return self.username


# USER PROFILE
class UserProfile(models.Model):
    profile_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    username = models.CharField(max_length=100)
    credit = models.IntegerField(default=10)
    skills_learn_count = models.IntegerField(default=0)
    skills_teach_count = models.IntegerField(default=0)

# SKILLS
class Skill(models.Model):
    skill_id = models.AutoField(primary_key=True)
    skill_name = models.CharField(max_length=100)
    category = models.CharField(max_length=100)
    language = models.CharField(max_length=100)


# USER SKILLS
class UserSkill(models.Model):
    user_skill_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE)
    skill_type = models.CharField(max_length=50)


# SKILL REQUEST
class SkillRequest(models.Model):
    request_id = models.AutoField(primary_key=True)
    sender = models.ForeignKey(User, related_name="sender", on_delete=models.CASCADE)
    receiver = models.ForeignKey(User, related_name="receiver", on_delete=models.CASCADE)
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE)
    status = models.CharField(max_length=50)


# SESSIONS
class Session(models.Model):
    session_id = models.AutoField(primary_key=True)
    skill_request = models.ForeignKey(SkillRequest, on_delete=models.CASCADE)
    session_link = models.CharField(max_length=200)
    session_time = models.DateTimeField()
    status = models.CharField(max_length=50)

import uuid

class ChatRoom(models.Model):
    id = models.CharField(primary_key=True, max_length=100, default=uuid.uuid4, editable=False)
    users = models.ManyToManyField(User)


# MESSAGE
class Message(models.Model):
    message_id = models.AutoField(primary_key=True)
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, null=True, blank=True)
    text = models.TextField()
    type = models.CharField(max_length=20, default="text")

    # 🔥 ADD THIS
    status = models.CharField(max_length=20, default="sent")

    timestamp = models.DateTimeField(auto_now_add=True)

# REVIEW
class Review(models.Model):
    review_id = models.AutoField(primary_key=True)
    session = models.ForeignKey(Session, on_delete=models.CASCADE)
    comment = models.TextField()
    ranking = models.IntegerField()
    
class UserFullData(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    username = models.CharField(max_length=100)
    full_name = models.CharField(max_length=200)
    email = models.EmailField()
    password = models.CharField(max_length=100)

    teach_skills = models.JSONField()
    learn_skills = models.JSONField()
    
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(
            user=instance,
            username=instance.username,
            credit=10,
            skills_learn_count=0,
            skills_teach_count=0
        )