from django.contrib import admin

from candidates.models import Candidate


# Register your models here.
@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    list_display = ('telegram_id', 'username', 'first_name', 'last_name', 'created_at')
    readonly_fields = ('telegram_id', 'username', 'first_name', 'last_name', 'created_at', 'phone', 'gender')
