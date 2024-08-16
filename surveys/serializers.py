from rest_framework import serializers
from .models import (
    Survey,
    Section,
    Field,
    SurveyResponse,
    SectionResponse,
    FieldResponse,
)


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
        return data

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
            if section_serializer.is_valid():
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
                    if section_serializer.is_valid():
                        section_serializer.save(survey=instance)
            else:
                section_serializer = SectionSerializer(data=section_data)
                if section_serializer.is_valid():
                    section_serializer.save(survey=instance)

        return instance


class FieldResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = FieldResponse
        exclude = ["section_response"]


class SectionResponseSerializer(serializers.ModelSerializer):
    field_responses = FieldResponseSerializer(many=True)

    class Meta:
        model = SectionResponse
        exclude = ["survey_response"]


class SurveyResponseSerializer(serializers.ModelSerializer):
    section_responses = SectionResponseSerializer(many=True)

    class Meta:
        model = SurveyResponse
        fields = "__all__"
