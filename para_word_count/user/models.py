from django.db import models
from django.contrib.auth.models import User as AuthUser


class User(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True, max_length=254)
    date_of_birth = models.DateField(help_text="Please use the format YYYY-MM-DD")
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)


class Paragraph(models.Model):
    user = models.ForeignKey(AuthUser, on_delete=models.CASCADE, related_name='paragraphs')
    raw_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Paragraph by {self.user.username} - {self.created_at}"


class WordOccurrence(models.Model):
    paragraph = models.ForeignKey(Paragraph, on_delete=models.CASCADE, related_name='word_occurrences')
    word = models.CharField(max_length=255, db_index=True)
    count = models.IntegerField(default=1)
    
    class Meta:
        unique_together = ('paragraph', 'word')
        indexes = [
            models.Index(fields=['word', '-count']),
        ]

    def __str__(self):
        return f"{self.word}: {self.count} times"
