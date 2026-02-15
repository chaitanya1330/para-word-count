import re
from celery import shared_task
from .models import Paragraph, WordOccurrence


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
