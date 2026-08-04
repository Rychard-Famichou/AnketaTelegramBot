from rest_framework import serializers

from .models import Candidate


class CandidateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Candidate
        fields = ["first_name", "last_name", "gender", "phone"]
        read_only_fields = ["telegram_id", "username"]
        extra_kwargs = {
            "telegram_id": {"required": False},
        }
