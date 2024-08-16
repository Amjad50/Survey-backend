from django.contrib import admin
from .models import (
    Survey,
    Section,
    Field,
    SurveyResponse,
    SectionResponse,
    FieldResponse,
    FieldAnalytics,
    SectionAnalytics,
    SurveyAnalytics,
)


class SectionInline(admin.StackedInline):
    model = Section
    extra = 1


class FieldInline(admin.StackedInline):
    model = Field
    extra = 1


@admin.register(Survey)
class SurveyAdmin(admin.ModelAdmin):
    list_display = ("title", "description")
    inlines = [SectionInline]


@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ("title", "survey")
    inlines = [FieldInline]


@admin.register(Field)
class FieldAdmin(admin.ModelAdmin):
    list_display = ("label", "field_type", "required", "section")


class SectionResponseInline(admin.StackedInline):
    model = SectionResponse
    extra = 0


@admin.register(SurveyResponse)
class SurveyResponseAdmin(admin.ModelAdmin):
    list_display = ("survey", "user", "completed", "submitted_at", "last_saved_at")
    inlines = [SectionResponseInline]


class FieldResponseInline(admin.StackedInline):
    model = FieldResponse
    extra = 0


@admin.register(SectionResponse)
class SectionResponseAdmin(admin.ModelAdmin):
    list_display = ("survey_response", "section", "completed")
    inlines = [FieldResponseInline]


@admin.register(FieldResponse)
class FieldResponseAdmin(admin.ModelAdmin):
    list_display = ("section_response", "field", "value")


class FieldAnalyticsInline(admin.StackedInline):
    model = FieldAnalytics
    extra = 0


@admin.register(FieldAnalytics)
class FieldAnalyticsAdmin(admin.ModelAdmin):
    list_display = ("field", "number_of_responses", "common_responses", "for_number")


@admin.register(SectionAnalytics)
class SectionAnalyticsAdmin(admin.ModelAdmin):
    list_display = ["section"]
    inlines = [FieldAnalyticsInline]


class SectionAnalyticsInline(admin.StackedInline):
    model = SectionAnalytics
    extra = 0


@admin.register(SurveyAnalytics)
class SurveyAnalyticsAdmin(admin.ModelAdmin):
    list_display = (
        "survey",
        "total_responses",
        "completed_responses",
        "unique_users",
        "max_responses",
        "max_responses_user",
        "average_responses_per_user",
    )
    inlines = [SectionAnalyticsInline]
