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


auditlog.register(Survey)
auditlog.register(Section)
auditlog.register(Field)
auditlog.register(SurveyResponse)
auditlog.register(SectionResponse)
auditlog.register(FieldResponse)
