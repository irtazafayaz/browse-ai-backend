from rest_framework import serializers


class ProductSerializer(serializers.Serializer):
    """Serializes a MongoDB product document into the shape the frontend expects."""
    id = serializers.CharField(source='_id_str', read_only=True)
    brand = serializers.CharField()
    name = serializers.CharField()
    imageUrl = serializers.CharField()
    price = serializers.FloatField()
    originalPrice = serializers.FloatField(required=False, allow_null=True)
    tags = serializers.ListField(child=serializers.CharField())
    isBookmarked = serializers.BooleanField(default=False)


class SearchRequestSerializer(serializers.Serializer):
    query = serializers.CharField(max_length=500)
    history = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        default=list,
    )


class SearchResponseSerializer(serializers.Serializer):
    products = ProductSerializer(many=True)
    displayText = serializers.CharField()
    suggestedFilters = serializers.ListField(child=serializers.CharField())
