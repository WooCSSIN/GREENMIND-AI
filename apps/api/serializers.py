"""
GreenMind Public API - v1
Module: Serializers (Định dạng dữ liệu đầu ra / đầu vào)
"""

from rest_framework import serializers
from django.contrib.auth.models import User, Group


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer cho thông tin người dùng (đã lọc các trường nhạy cảm)."""
    role = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name", "date_joined", "role"]
        read_only_fields = ["id", "date_joined", "role"]

    def get_role(self, obj):
        """Lấy tên group đầu tiên (vai trò) của user."""
        group = obj.groups.first()
        return group.name if group else "Viewer"


class UserRegisterSerializer(serializers.ModelSerializer):
    """Serializer để đăng ký tài khoản mới qua API."""
    password = serializers.CharField(write_only=True, min_length=6, style={"input_type": "password"})
    password_confirm = serializers.CharField(write_only=True, style={"input_type": "password"})
    role = serializers.ChoiceField(choices=["Admin", "Manager", "Viewer"], default="Viewer", write_only=True)

    class Meta:
        model = User
        fields = ["username", "email", "first_name", "last_name", "password", "password_confirm", "role"]

    def validate(self, attrs):
        if attrs["password"] != attrs.pop("password_confirm"):
            raise serializers.ValidationError({"password_confirm": "Mật khẩu xác nhận không khớp."})
        return attrs

    def create(self, validated_data):
        role_name = validated_data.pop("role", "Viewer")
        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data.get("email", ""),
            first_name=validated_data.get("first_name", ""),
            last_name=validated_data.get("last_name", ""),
            password=validated_data["password"],
        )
        # Gán Group (Role) cho user mới
        group, _ = Group.objects.get_or_create(name=role_name)
        user.groups.add(group)
        return user


class ForecastRequestSerializer(serializers.Serializer):
    """Serializer cho request dự báo."""
    item_id = serializers.FloatField(help_text="Mã SKU sản phẩm (ItemID trong SQL Server)")
    days = serializers.IntegerField(default=30, min_value=1, max_value=90, help_text="Số ngày dự báo (1-90)")


class ForecastResultSerializer(serializers.Serializer):
    """Serializer cho kết quả dự báo trả về."""
    item_id = serializers.FloatField()
    model_used = serializers.CharField()
    forecast_dates = serializers.ListField(child=serializers.CharField())
    forecast_values = serializers.ListField(child=serializers.FloatField())
    avg_discount_used = serializers.FloatField()


class ModelBattleResultSerializer(serializers.Serializer):
    """Serializer cho kết quả so sánh các mô hình AI."""
    Model = serializers.CharField()
    MAE = serializers.FloatField()
    RMSE = serializers.FloatField()


class ForecastCompareSerializer(serializers.Serializer):
    """Serializer đầy đủ cho endpoint so sánh mô hình."""
    item_id = serializers.FloatField()
    champion = serializers.CharField()
    battle_results = ModelBattleResultSerializer(many=True)
    green_impact = serializers.DictField()


class DSS_RecommendationSerializer(serializers.Serializer):
    """Serializer cho các gợi ý DSS (Decision Support System)."""
    champion = serializers.CharField()
    safety_stock_optimized = serializers.FloatField()
    reorder_point = serializers.FloatField()
    lead_time_demand = serializers.FloatField()
    mae_error = serializers.FloatField()
    green_saving = serializers.FloatField()


class InventoryTransactionSerializer(serializers.Serializer):
    """Serializer cho giao dịch nhập/xuất kho qua API."""
    item_id = serializers.IntegerField()
    transaction_type = serializers.ChoiceField(choices=["inbound", "outbound"])
    quantity = serializers.FloatField(min_value=0.01)
    price = serializers.FloatField(min_value=0)
