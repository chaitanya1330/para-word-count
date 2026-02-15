from django.contrib import admin
from .models import User, Paragraph, WordOccurrence

admin.site.register(User)
admin.site.register(Paragraph)
admin.site.register(WordOccurrence)
