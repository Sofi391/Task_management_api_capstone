from rest_framework import serializers
from .models import OtpCode
from django.contrib.auth.models import User
from random import randint
from django.utils import timezone
from datetime import timedelta


class SignupSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=True)
    password2 = serializers.CharField( write_only=True)
    class Meta:
        model = User
        fields = ('username', 'email', 'password','password2')
        extra_kwargs = {'password': {'write_only': True}}

    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError('Passwords must match')
        return data
    def validate_email(self, email):
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError('Email already registered')
        return email

    def create(self, validated_data):
        validated_data.pop('password2')
        user = User(is_active=False,**validated_data)
        user.set_password(validated_data['password'])
        user.save()
        ran_otp = randint(100000, 999999)
        otp = OtpCode.objects.create(
            user=user,
            code=ran_otp,
            purpose='signup',
            used=False,
        )
        return otp


class OtpVerificationSerializer(serializers.Serializer):
    otp = serializers.IntegerField()
    def validate(self, data):
        otp_obj = OtpCode.objects.filter(code=data['otp'],used=False,purpose='signup').select_related('user').first()
        if not otp_obj:
            raise serializers.ValidationError('Invalid or Used OTP')
        if timezone.now()-otp_obj.created_at > timedelta(minutes=5):
            raise serializers.ValidationError('The verification code has expired. Please request a new one.')
        self.user = otp_obj.user
        return data

    def create(self, validated_data):
        user = self.user
        user.is_active = True
        user.save()
        OtpCode.objects.filter(user=user,code=validated_data['otp']).update(used=True)
        return user


class OtpResendSerializer(serializers.Serializer):
    email = serializers.EmailField()
    def validate(self, data):
        user = User.objects.filter(email=data['email']).first()
        if not user:
            raise serializers.ValidationError('User not found')
        if user.is_active != False:
            raise serializers.ValidationError('User is already active')
        self.user = user
        return data
    def create(self, validated_data):
        ran_otp = randint(100000, 999999)
        otp, created = OtpCode.objects.update_or_create(
            user=self.user,
            purpose='signup',
            defaults = {'code': ran_otp,'created_at': timezone.now(),'used':False}
        )
        return otp



class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()
    def validate(self, data):
        if not data['password'] or not data['email']:
            raise serializers.ValidationError('Email or password is required')
        user = User.objects.filter(email=data['email']).first()
        if not user:
            raise serializers.ValidationError('User not found')
        if not user.is_active:
            raise serializers.ValidationError('Account is not verified')
        if not user.check_password(data['password']):
            raise serializers.ValidationError('Invalid password')
        data['user'] = user
        return data



class OtpCodeSerializer(serializers.ModelSerializer):
    email = serializers.EmailField()

    class Meta:
        model = OtpCode
        fields = ('email',)
    def validate(self, data):
        email = data.get('email')
        if not email:
            raise serializers.ValidationError('Email cannot be empty')
        user = User.objects.filter(email=email).first()
        if not user:
            raise serializers.ValidationError('User not found')
        return data

    def create(self, validated_data):
        user = User.objects.filter(email=validated_data['email']).first()
        ran_otp = randint(100000,999999)
        otp, created = OtpCode.objects.update_or_create(
            user=user,
            purpose='reset',
            defaults = {'code': ran_otp,'created_at': timezone.now(),'used':False}
        )
        return otp


class PassResetSerializer(serializers.Serializer):
    password = serializers.CharField()
    password2 = serializers.CharField()
    otp = serializers.IntegerField()

    def validate(self, data):
        if not data['otp']:
            raise serializers.ValidationError('OTP cannot be empty')
        otp_obj = OtpCode.objects.filter(code=data['otp'],used=False,purpose='reset').select_related('user').first()
        if not otp_obj:
            raise serializers.ValidationError('Invalid or Used OTP')
        if timezone.now()-otp_obj.created_at > timedelta(minutes=5):
            raise serializers.ValidationError('The verification code has expired. Please request a new one.')
        if not data['password'] or not data['password2']:
            raise serializers.ValidationError('Password field is required')
        if data['password'] != data['password2']:
            raise serializers.ValidationError('Passwords must match')
        user = otp_obj.user
        if user.check_password(data['password']):
            raise serializers.ValidationError('You cannot reuse your current password')
        self.user = user
        return data

    def create(self, validated_data):
        user = self.user
        user.set_password(validated_data['password'])
        user.save()
        OtpCode.objects.filter(user=user,code=validated_data['otp'],purpose='reset').update(used=True)
        return user
