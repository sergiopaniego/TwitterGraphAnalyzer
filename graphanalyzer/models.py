from django.db import models

class Tweet(models.Model):
    username = models.CharField(max_length=50)
    name = models.CharField(max_length=50)
    tweet = models.CharField(max_length=280) # Links, pictures and so count as chars?
    time = models.DateTimeField('date published')
    location = models.CharField(max_length=50)

    def __str__(self):
        return self.username + ": " + self.tweet


'''
    DOUBTS
        Links, pictures and so count as chars?
        Should I store connections like following, followed_by?
        Should I store user info?
'''