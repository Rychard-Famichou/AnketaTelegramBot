from django.urls import path

from candidates.views import AnketaFormView, CandidateCreateAPIView, CandidateDetailAPIView

urlpatterns = [
    path("form/", AnketaFormView.as_view(), name="anketa_form"),
    path("api/candidates/", CandidateCreateAPIView.as_view(), name="candidate_create"),
    path("api/candidates/me/", CandidateDetailAPIView.as_view(), name="candidate_detail"),
]
