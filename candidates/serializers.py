from rest_framework import serializers
from .models import Candidate

class CandidateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Candidate
        fields = ['telegram_id', 'username', 'first_name', 'last_name', 'gender', 'phone']
        extra_kwargs = {
            'telegram_id': {'required': False},
        }
