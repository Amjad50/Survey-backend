from rest_framework import serializers
from .models import (
    Survey,
    Section,
    Field,
    SurveyResponse,
    SectionResponse,
    FieldResponse,
    SurveyAnalytics,
    SectionAnalytics,
    FieldAnalytics,
)

from .tasks import update_survey_analytics


class FieldSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = Field
        exclude = ["section"]

    def validate(self, data):
        need_options = data["field_type"] in ["dropdown", "radio", "checkbox"]

        if need_options and not data.get("options"):
            raise serializers.ValidationError(
                {
                    "options": "This field is required for dropdown, radio, or checkbox fields."
                }
            )
        elif not need_options and data.get("options"):
            raise serializers.ValidationError(
                {
                    "options": "This field is only required for dropdown, radio, or checkbox fields."
                }
            )
        return super().validate(data)

    def create(self, validated_data):
        fields_data = validated_data.pop("fields", [])
        section = Section.objects.create(**validated_data)
        for field_data in fields_data:
            Field.objects.create(section=section, **field_data)
        return section


class SectionSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    fields = FieldSerializer(many=True)

    class Meta:
        model = Section
        exclude = ["survey"]

    def create(self, validated_data):
        fields_data = validated_data.pop("fields", [])
        section = Section.objects.create(**validated_data)
        for field_data in fields_data:
            Field.objects.create(section=section, **field_data)
        return section

    def update(self, instance, validated_data):
        fields_data = validated_data.pop("fields", [])
        instance.title = validated_data.get("title", instance.title)
        instance.save()

        # Handle nested fields
        for field_data in fields_data:
            field_id = field_data.get("id", None)
            if field_id:
                field_instance = instance.fields.filter(id=field_id).first()
                if field_instance:
                    FieldSerializer().update(field_instance, field_data)
                else:
                    Field.objects.create(section=instance, **field_data)
            else:
                Field.objects.create(section=instance, **field_data)

        return instance


class SurveySerializer(serializers.ModelSerializer):
    sections = SectionSerializer(many=True)

    class Meta:
        model = Survey
        fields = "__all__"

    def create(self, validated_data):
        sections_data = validated_data.pop("sections", [])
        survey = Survey.objects.create(**validated_data)
        for section_data in sections_data:
            section_serializer = SectionSerializer(data=section_data)
            if section_serializer.is_valid(raise_exception=True):
                section_serializer.save(survey=survey)
        return survey

    def update(self, instance, validated_data):
        sections_data = validated_data.pop("sections", [])
        instance.title = validated_data.get("title", instance.title)
        instance.description = validated_data.get("description", instance.description)
        instance.save()

        # Handle nested sections
        for section_data in sections_data:
            section_id = section_data.get("id", None)
            if section_id:
                section_instance = instance.sections.filter(id=section_id).first()
                if section_instance:
                    SectionSerializer().update(section_instance, section_data)
                else:
                    section_serializer = SectionSerializer(data=section_data)
                    if section_serializer.is_valid(raise_exception=True):
                        section_serializer.save(survey=instance)
            else:
                section_serializer = SectionSerializer(data=section_data)
                if section_serializer.is_valid(raise_exception=True):
                    section_serializer.save(survey=instance)

        return instance


class FieldResponseSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = FieldResponse
        exclude = ["section_response"]

    def to_internal_value(self, data):
        if isinstance(data.get("field"), Field):
            data["field"] = data["field"].id
        return super().to_internal_value(data)

    def validate(self, attrs):
        field = attrs.get("field")
        value = attrs.get("value")

        # Check if the field is required and if the value is missing
        if field.required and not value:
            raise serializers.ValidationError({"value": "This field is required."})

        field_type = field.field_type
        options = field.options or []

        if field_type == "text":
            if not isinstance(value, str):
                raise serializers.ValidationError(
                    "Expected a string for text field type."
                )
        elif field_type == "number":
            if not isinstance(value, (int, float)):
                raise serializers.ValidationError(
                    "Expected a number for number field type."
                )

        elif field_type == "date":
            try:
                # Assuming the date is provided as a string in 'YYYY-MM-DD' format
                from datetime import datetime

                datetime.strptime(value, "%Y-%m-%d")
            except (TypeError, ValueError):
                raise serializers.ValidationError(
                    "Expected a date in 'YYYY-MM-DD' format for date field type."
                )

        elif field_type in ["dropdown", "radio"]:
            if not isinstance(value, str):
                raise serializers.ValidationError(
                    f"Expected a single string value for {field_type} field type."
                )
            if value not in options:
                raise serializers.ValidationError(
                    f"Value '{value}' is not a valid option for {field_type} field type."
                )

        elif field_type == "checkbox":
            if not isinstance(value, list):
                raise serializers.ValidationError(
                    "Expected a list of values for checkbox field type."
                )
            invalid_options = [v for v in value if v not in options]
            if invalid_options:
                raise serializers.ValidationError(
                    f"Invalid options {invalid_options} for checkbox field type."
                )

        else:
            raise serializers.ValidationError("Unsupported field type.")

        return super().validate(attrs)


class SectionResponseSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    field_responses = FieldResponseSerializer(many=True)

    class Meta:
        model = SectionResponse
        exclude = ["survey_response"]

    def to_internal_value(self, data):
        if isinstance(data.get("section"), Section):
            data["section"] = data["section"].id
        return super().to_internal_value(data)

    def validate(self, data):
        section = data["section"]
        field_responses_data = data.get("field_responses", [])
        field_responses_ids = {
            response["field"].id for response in field_responses_data
        }
        all_fields = set(section.fields.values_list("id", flat=True))
        required_fields = set(
            section.fields.filter(required=True).values_list("id", flat=True)
        )

        invalid_fields = field_responses_ids - all_fields

        if invalid_fields:
            raise serializers.ValidationError(
                f"The following fields are not part of the section: {', '.join(map(str, invalid_fields))}"
            )

        if data.get("completed", False):
            # Ensure all required fields are filled out
            missing_required_fields = required_fields - field_responses_ids

            if missing_required_fields:
                raise serializers.ValidationError(
                    f"The following required fields are missing in the response: {', '.join(map(str, missing_required_fields))}"
                )

        return super().validate(data)

    def create(self, validated_data):
        field_responses_data = validated_data.pop("field_responses", [])
        section_response = SectionResponse.objects.create(**validated_data)
        for field_response_data in field_responses_data:
            FieldResponse.objects.create(
                section_response=section_response, **field_response_data
            )

        return section_response

    def update(self, instance, validated_data):
        field_responses_data = validated_data.pop("field_responses", [])
        instance.completed = validated_data.get("completed", instance.completed)
        instance.save()

        # Handle nested field responses
        for field_response_data in field_responses_data:
            field_response_instance = instance.field_responses.filter(
                id=field_response_data.get("id")
            ).first()
            if field_response_instance:
                FieldResponseSerializer().update(
                    field_response_instance, field_response_data
                )
            else:
                FieldResponse.objects.create(
                    section_response=instance, **field_response_data
                )

        return instance


class SurveyResponseSerializer(serializers.ModelSerializer):
    section_responses = SectionResponseSerializer(many=True)

    class Meta:
        model = SurveyResponse
        fields = "__all__"

    def validate(self, data):
        survey = data["survey"]
        section_responses_data = data.get("section_responses", [])
        section_responses_ids = {
            response["section"].id for response in section_responses_data
        }

        # Get all section IDs for the given survey
        valid_section_ids = set(survey.sections.values_list("id", flat=True))

        # Check for any section in the responses that is not part of the survey
        invalid_sections = section_responses_ids - valid_section_ids

        if invalid_sections:
            raise serializers.ValidationError(
                f"Some sections in the response do not belong to the survey: {', '.join(map(str, invalid_sections))}"
            )

        if data.get("completed", False):
            section_responses_dict = {
                response["section"].id: response for response in section_responses_data
            }

            for section_id in valid_section_ids:
                if section_id not in section_responses_dict:
                    raise serializers.ValidationError(
                        f"Section with ID {section_id} is missing in the response."
                    )
                # Validate that the section response is completed
                if not section_responses_dict[section_id].get("completed", False):
                    raise serializers.ValidationError(
                        f"Section with ID {section_id} must be completed before marking the survey as completed."
                    )

        return super().validate(data)

    def create(self, validated_data):
        section_responses_data = validated_data.pop("section_responses", [])
        survey_response = SurveyResponse.objects.create(**validated_data)

        for section_response_data in section_responses_data:
            section_response_serializer = SectionResponseSerializer(
                data=section_response_data
            )
            if section_response_serializer.is_valid(raise_exception=True):
                section_response_serializer.save(survey_response=survey_response)

        update_survey_analytics.delay_on_commit(survey_response.survey.id)

        return survey_response

    def update(self, instance, validated_data):
        section_responses_data = validated_data.pop("section_responses", [])
        instance.completed = validated_data.get("completed", instance.completed)
        instance.save()

        for section_response_data in section_responses_data:
            section_response_instance = instance.section_responses.filter(
                id=section_response_data.get("id")
            ).first()
            if section_response_instance:
                SectionResponseSerializer().update(
                    section_response_instance, section_response_data
                )
            else:
                section_response_serializer = SectionResponseSerializer(
                    data=section_response_data
                )
                if section_response_serializer.is_valid(raise_exception=True):
                    section_response_serializer.save(survey_response=instance)

        update_survey_analytics.delay_on_commit(instance.survey.id)

        return instance


class FieldAnalyticsSerializer(serializers.ModelSerializer):
    class Meta:
        model = FieldAnalytics
        fields = ["field_id", "number_of_responses", "common_responses", "for_number"]


class SectionAnalyticsSerializer(serializers.ModelSerializer):
    field_analytics = FieldAnalyticsSerializer(many=True)

    class Meta:
        model = SectionAnalytics
        fields = ["section_id", "field_analytics"]


class SurveyAnalyticsSerializer(serializers.ModelSerializer):
    section_analytics = SectionAnalyticsSerializer(many=True)

    class Meta:
        model = SurveyAnalytics
        fields = [
            "survey_id",
            "total_responses",
            "completed_responses",
            "section_analytics",
            "unique_users",
            "max_responses",
            "max_responses_user",
            "average_responses_per_user",
        ]
