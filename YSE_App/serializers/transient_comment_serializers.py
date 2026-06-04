from rest_framework import serializers

from YSE_App.models import Log


class TransientCommentSerializer(serializers.ModelSerializer):
    created_by = serializers.StringRelatedField(read_only=True)
    modified_by = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Log
        fields = (
            "id",
            "comment",
            "transient",
            "created_by",
            "modified_by",
            "created_date",
            "modified_date",
        )
        read_only_fields = (
            "id",
            "created_by",
            "modified_by",
            "created_date",
            "modified_date",
        )
