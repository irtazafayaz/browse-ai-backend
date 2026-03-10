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
    page = serializers.IntegerField(required=False, default=1, min_value=1)


class SearchResponseSerializer(serializers.Serializer):
    products = ProductSerializer(many=True)
    displayText = serializers.CharField()
    suggestedFilters = serializers.ListField(child=serializers.CharField())
    total = serializers.IntegerField()
    page = serializers.IntegerField()
    page_size = serializers.IntegerField()
    has_next = serializers.BooleanField()
