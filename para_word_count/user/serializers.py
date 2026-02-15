from rest_framework import serializers
from .models import Paragraph, WordOccurrence


class WordOccurrenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = WordOccurrence
        fields = ['word', 'count']


class ParagraphSerializer(serializers.ModelSerializer):
    word_occurrences = WordOccurrenceSerializer(many=True, read_only=True)
    user_name = serializers.SerializerMethodField()

    class Meta:
        model = Paragraph
        fields = ['id', 'user_name', 'raw_text', 'created_at', 'word_occurrences']
        read_only_fields = ['id', 'created_at', 'word_occurrences']

    def get_user_name(self, obj):
        return obj.user.username


class ParagraphCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Paragraph
        fields = ['raw_text']


class SearchResultSerializer(serializers.Serializer):
    paragraph_id = serializers.IntegerField()
    user_name = serializers.CharField()
    raw_text = serializers.CharField()
    word_count = serializers.IntegerField()
    created_at = serializers.DateTimeField()
