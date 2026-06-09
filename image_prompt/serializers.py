from rest_framework import serializers


class AnalyzeSeriesCharactersRequestSerializer(serializers.Serializer):
    source_text = serializers.CharField(
        allow_blank=False,
        max_length=8000,
        trim_whitespace=True,
    )
    series_name = serializers.CharField(
        allow_blank=True,
        default="",
        max_length=120,
        required=False,
        trim_whitespace=True,
    )


class CharacterCandidateSerializer(serializers.Serializer):
    character_name = serializers.CharField(max_length=80, trim_whitespace=True)
    series_role = serializers.CharField(max_length=80, trim_whitespace=True)
    core_identity = serializers.CharField(max_length=300, trim_whitespace=True)
    visual_profile = serializers.CharField(max_length=300, trim_whitespace=True)
    personality_profile = serializers.CharField(max_length=300, trim_whitespace=True)
    speech_style = serializers.CharField(max_length=200, trim_whitespace=True)
    relationship_to_others = serializers.CharField(
        allow_blank=True,
        default="",
        required=False,
        trim_whitespace=True,
    )
    signature_elements = serializers.ListField(
        child=serializers.CharField(trim_whitespace=True),
        default=list,
        required=False,
    )
    character_prompt = serializers.CharField(max_length=1000, trim_whitespace=True)
    confidence_reason = serializers.CharField(max_length=300, trim_whitespace=True)


class JokeToComicRequestSerializer(serializers.Serializer):
    joke = serializers.CharField(
        allow_blank=False,
        max_length=2000,
        trim_whitespace=True,
    )
    confirmed_characters = CharacterCandidateSerializer(
        many=True,
        default=list,
        required=False,
    )
