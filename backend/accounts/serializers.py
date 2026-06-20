from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from .models import Role, UserProfile


class RoleSerializer(serializers.ModelSerializer):
    user_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Role
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')


class UserProfileSerializer(serializers.ModelSerializer):
    role = RoleSerializer(read_only=True)
    role_id = serializers.PrimaryKeyRelatedField(
        queryset=Role.objects.all(),
        source='role',
        write_only=True,
        required=False,
        allow_null=True
    )

    class Meta:
        model = UserProfile
        fields = ('role', 'role_id', 'phone')


class UserSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()
    role_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    phone = serializers.CharField(write_only=True, required=False, allow_blank=True, allow_null=True)
    profile_phone = serializers.CharField(source='profile.phone', read_only=True)
    role_code = serializers.SerializerMethodField()
    role_name = serializers.SerializerMethodField()
    display_name = serializers.SerializerMethodField()
    is_admin = serializers.SerializerMethodField()
    farmer_id = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 'is_active', 'is_staff',
            'role', 'role_id', 'role_code', 'role_name',
            'phone', 'profile_phone', 'display_name', 'is_admin',
            'date_joined', 'farmer_id'
        )
        read_only_fields = ('date_joined',)

    def get_role(self, obj):
        if hasattr(obj, 'profile') and obj.profile.role:
            return {'id': obj.profile.role.id, 'name': obj.profile.role.name, 'code': obj.profile.role.code}
        return None

    def get_role_code(self, obj):
        if hasattr(obj, 'profile') and obj.profile.role:
            return obj.profile.role.code
        return None

    def get_role_name(self, obj):
        if hasattr(obj, 'profile') and obj.profile.role:
            return obj.profile.role.name
        return None

    def get_display_name(self, obj):
        full = obj.get_full_name()
        if full:
            return full
        if hasattr(obj, 'profile') and obj.profile.phone:
            return f'{obj.username} ({obj.profile.phone})'
        return obj.username

    def get_is_admin(self, obj):
        if obj.is_superuser:
            return True
        if hasattr(obj, 'profile') and obj.profile.role and obj.profile.role.code == 'admin':
            return True
        return False

    def get_farmer_id(self, obj):
        farmer = getattr(obj, 'farmer_profile', None)
        if farmer:
            return farmer.id
        try:
            from core.models import Farmer
            return Farmer.objects.get(user=obj).id
        except Exception:
            return None


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)
    role_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    phone = serializers.CharField(write_only=True, required=False, allow_blank=True, allow_null=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password', 'password2', 'is_active', 'is_staff', 'role_id', 'phone')
        read_only_fields = ('id',)

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError('用户名已存在')
        return value

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({'password2': '两次输入的密码不一致'})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        role_id = validated_data.pop('role_id', None)
        phone = validated_data.pop('phone', '')
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password'],
            is_active=validated_data.get('is_active', True),
            is_staff=validated_data.get('is_staff', False),
        )
        profile, _ = UserProfile.objects.get_or_create(user=user)
        if role_id:
            try:
                profile.role = Role.objects.get(id=role_id)
            except Role.DoesNotExist:
                pass
        profile.phone = phone or None
        profile.save()
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    role_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    phone = serializers.CharField(write_only=True, required=False, allow_blank=True, allow_null=True)
    password = serializers.CharField(write_only=True, required=False, allow_blank=True, allow_null=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'is_active', 'is_staff', 'role_id', 'phone', 'password')
        read_only_fields = ('id',)

    def validate_username(self, value):
        qs = User.objects.filter(username=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError('用户名已存在')
        return value

    def update(self, instance, validated_data):
        role_id = validated_data.pop('role_id', None)
        phone = validated_data.pop('phone', None)
        password = validated_data.pop('password', None)

        instance.username = validated_data.get('username', instance.username)
        instance.email = validated_data.get('email', instance.email)
        instance.is_active = validated_data.get('is_active', instance.is_active)
        instance.is_staff = validated_data.get('is_staff', instance.is_staff)
        if password:
            instance.set_password(password)
        instance.save()

        profile, _ = UserProfile.objects.get_or_create(user=instance)
        if role_id is not None:
            if role_id:
                try:
                    profile.role = Role.objects.get(id=role_id)
                except Role.DoesNotExist:
                    profile.role = None
            else:
                profile.role = None
        if phone is not None:
            profile.phone = phone or None
        profile.save()
        return instance


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
