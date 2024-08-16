from django.db import models
from auditlog.registry import auditlog


class Survey(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)


class Section(models.Model):
    survey = models.ForeignKey(
        Survey, related_name="sections", on_delete=models.CASCADE
    )
    title = models.CharField(max_length=255)


class Field(models.Model):
    FIELD_TYPES = [
        ("text", "Text"),
        ("number", "Number"),
        ("date", "Date"),
        ("dropdown", "Dropdown"),
        ("checkbox", "Checkbox"),
        ("radio", "Radio"),
    ]
    section = models.ForeignKey(
        Section, related_name="fields", on_delete=models.CASCADE
    )
    label = models.CharField(max_length=255)
    field_type = models.CharField(max_length=50, choices=FIELD_TYPES)
    required = models.BooleanField(default=False)
    options = models.JSONField(
        blank=True, null=True
    )  # Used for dropdown, radio, checkbox options


class SurveyResponse(models.Model):
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE)
    user = models.ForeignKey("auth.User", on_delete=models.CASCADE)
    completed = models.BooleanField(default=False)
    submitted_at = models.DateTimeField(null=True, blank=True)
    last_saved_at = models.DateTimeField(auto_now=True)


class SectionResponse(models.Model):
    survey_response = models.ForeignKey(
        SurveyResponse, related_name="section_responses", on_delete=models.CASCADE
    )
    section = models.ForeignKey(Section, on_delete=models.CASCADE)
    completed = models.BooleanField(default=False)


class FieldResponse(models.Model):
    section_response = models.ForeignKey(
        SectionResponse, related_name="field_responses", on_delete=models.CASCADE
    )
    field = models.ForeignKey(Field, on_delete=models.CASCADE)
    value = models.JSONField(blank=True, null=False)


class SurveyAnalytics(models.Model):
    survey = models.OneToOneField(
        Survey,
        on_delete=models.CASCADE,
        primary_key=True,
        unique=True,
    )
    total_responses = models.PositiveIntegerField()
    completed_responses = models.PositiveIntegerField()

    unique_users = models.PositiveIntegerField()
    max_responses = models.PositiveIntegerField()
    max_responses_user = models.ForeignKey(
        "auth.User", on_delete=models.CASCADE, null=True
    )
    average_responses_per_user = models.FloatField()


class SectionAnalytics(models.Model):
    survey_analytics = models.ForeignKey(
        SurveyAnalytics, related_name="section_analytics", on_delete=models.CASCADE
    )
    section = models.ForeignKey(Section, on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["survey_analytics", "section"],
                name="unique_survey_analytics_section",
            )
        ]


class FieldAnalytics(models.Model):
    section_analytics = models.ForeignKey(
        SectionAnalytics, related_name="field_analytics", on_delete=models.CASCADE
    )
    field = models.ForeignKey(Field, on_delete=models.CASCADE)

    number_of_responses = models.PositiveIntegerField()

    # List of dictionaries with "value" and "count"
    common_responses = models.JSONField(default=list)

    # JSON with min, max, mean, median, mode, stddev
    # null for non-number fields
    for_number = models.JSONField(
        default=dict,
        null=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["section_analytics", "field"],
                name="unique_section_analytics_field",
            )
        ]


auditlog.register(Survey)
auditlog.register(Section)
auditlog.register(Field)
auditlog.register(SurveyResponse)
auditlog.register(SectionResponse)
auditlog.register(FieldResponse)
