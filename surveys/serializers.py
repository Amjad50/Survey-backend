from rest_framework import serializers
from .models import Survey, Section, Field, SurveyResponse, SectionResponse, FieldResponse

class FieldSerializer(serializers.ModelSerializer):
    def validate(self, data):
        need_options = data['field_type'] in ['dropdown', 'radio', 'checkbox']

        if need_options and not data.get('options'):
            raise serializers.ValidationError({'options': 'This field is required for dropdown, radio, or checkbox fields.'})
        elif not need_options and data.get('options'):
            raise serializers.ValidationError({'options': 'This field is only required for dropdown, radio, or checkbox fields.'})
        return data

    class Meta:
        model = Field
        exclude = ('section', 'id')

class SectionSerializer(serializers.ModelSerializer):
    fields = FieldSerializer(many=True)

    class Meta:
        model = Section
        exclude = ('survey', 'id')

class SurveySerializer(serializers.ModelSerializer):
    sections = SectionSerializer(many=True)

    class Meta:
        model = Survey
        fields = '__all__'


class FieldResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = FieldResponse
        fields = '__all__'

class SectionResponseSerializer(serializers.ModelSerializer):
    field_responses = FieldResponseSerializer(many=True)

    class Meta:
        model = SectionResponse
        fields = '__all__'

class SurveyResponseSerializer(serializers.ModelSerializer):
    section_responses = SectionResponseSerializer(many=True)

    class Meta:
        model = SurveyResponse
        fields = '__all__'
