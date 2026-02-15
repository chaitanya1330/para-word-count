import re
from celery import shared_task
from .models import Paragraph, WordOccurrence
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count


@shared_task
def tokenize_paragraph(paragraph_id):
    """
    Tokenize a paragraph and store word occurrences.
    Called asynchronously after a paragraph is created.
    """
    try:
        paragraph = Paragraph.objects.get(id=paragraph_id)
        
        # Simple tokenization: split by whitespace and remove punctuation
        # Convert to lowercase for case-insensitive search
        text = paragraph.raw_text.lower()
        
        # Split by whitespace and punctuation
        words = re.findall(r'\b\w+\b', text)
        
        # Count word occurrences
        word_count = {}
        for word in words:
            if len(word) > 1:  # Ignore single character words
                word_count[word] = word_count.get(word, 0) + 1
        
        # Store in database
        for word, count in word_count.items():
            WordOccurrence.objects.get_or_create(
                paragraph=paragraph,
                word=word,
                defaults={'count': count}
            )
        
        return {
            'status': 'success',
            'paragraph_id': paragraph_id,
            'unique_words': len(word_count),
            'total_words': len(words)
        }
    except Paragraph.DoesNotExist:
        return {'status': 'error', 'message': 'Paragraph not found'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}


@shared_task
def cleanup_old_paragraphs():
    """
    Periodic task: Delete paragraphs older than 90 days.
    Runs daily at midnight.
    """
    try:
        cutoff_date = timezone.now() - timedelta(days=90)
        old_paragraphs = Paragraph.objects.filter(created_at__lt=cutoff_date)
        count = old_paragraphs.count()
        old_paragraphs.delete()
        
        return {
            'status': 'success',
            'message': f'Deleted {count} paragraphs older than 90 days'
        }
    except Exception as e:
        return {'status': 'error', 'message': str(e)}


@shared_task
def generate_daily_statistics():
    """
    Periodic task: Generate daily statistics about word usage.
    Runs daily at 1 AM.
    """
    try:
        total_paragraphs = Paragraph.objects.count()
        total_words = WordOccurrence.objects.count()
        
        # Get most used words today
        today = timezone.now().date()
        top_words = WordOccurrence.objects.filter(
            paragraph__created_at__date=today
        ).values('word').annotate(
            total_count=Count('word')
        ).order_by('-total_count')[:10]
        
        stats = {
            'timestamp': timezone.now().isoformat(),
            'total_paragraphs': total_paragraphs,
            'total_words': total_words,
            'top_words_today': list(top_words)
        }
        
        return {
            'status': 'success',
            'statistics': stats
        }
    except Exception as e:
        return {'status': 'error', 'message': str(e)}
