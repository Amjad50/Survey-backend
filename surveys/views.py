from rest_framework import viewsets, mixins
from .models import Survey, SurveyResponse, SurveyAnalytics
from .serializers import (
    SurveySerializer,
    SurveyResponseSerializer,
    SurveyAnalyticsSerializer,
)


class SurveyViewSet(viewsets.ModelViewSet):
    queryset = Survey.objects.all()
    serializer_class = SurveySerializer


class SurveyResponseViewSet(viewsets.ModelViewSet):
    queryset = SurveyResponse.objects.all()
    serializer_class = SurveyResponseSerializer


class SurveyAnalyticsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SurveyAnalytics.objects.all()
    serializer_class = SurveyAnalyticsSerializer
