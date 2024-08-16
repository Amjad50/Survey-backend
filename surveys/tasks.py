from celery import shared_task
from django.db.models import Avg, Count, Max, Min, StdDev, FloatField
from django.db.models.functions import Cast, Coalesce
from .models import (
    SurveyAnalytics,
    SectionAnalytics,
    FieldAnalytics,
    SurveyResponse,
    FieldResponse,
    Survey,
)
from statistics import stdev


@shared_task
def update_survey_analytics(survey_id):
    survey = Survey.objects.get(id=survey_id)
    assert survey, f"Survey with id {survey_id} does not exist"

    # Retrieve survey analytics
    survey_analytics, _created = SurveyAnalytics.objects.get_or_create(
        survey_id=survey_id,
        defaults={
            "total_responses": 0,
            "completed_responses": 0,
            "unique_users": 0,
            "max_responses": 0,
            "max_responses_user_id": None,
            "average_responses_per_user": 0,
        },
    )

    # Calculate total and completed responses
    total_responses_count = SurveyResponse.objects.filter(survey_id=survey_id).count()
    completed_responses = SurveyResponse.objects.filter(
        survey_id=survey_id, completed=True
    )
    survey_analytics.total_responses = total_responses_count
    survey_analytics.completed_responses = completed_responses.count()

    # User engagement calculations
    users = completed_responses.values("user")
    survey_analytics.unique_users = users.distinct().count()
    user_responses = users.annotate(responses_count=Count("id"))
    max_user_response = max(
        user_responses,
        key=lambda x: x["responses_count"],
        default={"responses_count": 0, "user": None},
    )
    survey_analytics.max_responses = max_user_response["responses_count"]
    survey_analytics.max_responses_user_id = max_user_response["user"]
    survey_analytics.average_responses_per_user = (
        survey_analytics.completed_responses / survey_analytics.unique_users
        if survey_analytics.unique_users > 0
        else 0
    )

    survey_analytics.save()

    for section in survey.sections.all():
        section_analytics, _created = SectionAnalytics.objects.get_or_create(
            survey_analytics=survey_analytics, section=section
        )
        section_analytics.save()

        for field in section.fields.all():
            field_analytics, _created = FieldAnalytics.objects.get_or_create(
                section_analytics=section_analytics,
                field=field,
                defaults={
                    "number_of_responses": 0,
                    "common_responses": [],
                    "for_number": None,
                },
            )
            # Calculate the number of responses for the field
            field_responses = FieldResponse.objects.filter(
                field=field, section_response__survey_response__completed=True
            )
            field_analytics.number_of_responses = field_responses.count()

            # Common responses calculation
            common_responses = (
                field_responses.values("value")
                .annotate(count=Count("id"))
                .order_by("-count")[:100]
            )
            field_analytics.common_responses = [
                {"value": response["value"], "count": response["count"]}
                for response in common_responses
            ]

            # Numerical field statistics
            if field.field_type == "number":
                numeric_values = field_responses.filter(
                    value__isnull=False
                ).values_list("value", flat=True)
                if numeric_values.exists():
                    values = sorted(
                        numeric_values.annotate(
                            val=Coalesce(Cast("value", FloatField()), float(0.0))
                        ).all()
                    )
                    field_analytics.for_number = {
                        "min": min(values),
                        "max": max(values),
                        "mean": sum(values) / len(values),
                        "median": values[len(values) // 2],
                        "mode": max(set(values), key=values.count),
                        "stddev": stdev(values),
                    }

            field_analytics.save()
