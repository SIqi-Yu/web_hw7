# socialnetwork/models.py

from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model):
    # One-to-one link to User model
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    # Bio text and profile picture
    bio = models.CharField(max_length=500, blank=True)
    picture = models.ImageField(upload_to='images/', blank=True)

    # Many-to-Many relationship so that each profile can follow multiple other profiles
    following = models.ManyToManyField(
        'self',
        symmetrical=False,
        related_name='followers',
        blank=True
    )

    def __str__(self):
        return f'Profile for {self.user.username}'


class Post(models.Model):
    # Author of the post
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    # The text of the post
    text = models.CharField(max_length=280)

    # When the post was created
    creation_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Post by {self.user.username} at {self.creation_time}'
    

class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    text = models.CharField(max_length=280)
    creation_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Comment by {self.user.username} on Post {self.post.id}'