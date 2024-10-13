
from rest_framework import serializers

from django.utils import timezone

from consultations.models import Consultation, Booked
from specialist.models import Specialist
from .models import User


class SignUpSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'username', 'email', 'password']
        read_only_fields = ['id', ]

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = User(**validated_data)
        if password:
            user.set_password(password)
        user.save()
        return user


class EmailVerificationSerializer(serializers.ModelSerializer):
    token = serializers.CharField(max_length=555)

    class Meta:
        model = User
        fields = ['token']


class AccountSerializer(serializers.ModelSerializer):
    specialist = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'is_verified', 'specialist']

    def get_specialist(self, obj) -> dict | bool:
        try:
            specialist = Specialist.objects.get(user=obj)
            if specialist.is_active:
                return {
                    'id': specialist.id,
                    'description': specialist.description,
                }
        except Specialist.DoesNotExist:
            return False


class ConsultationAccountSerializer(serializers.ModelSerializer):
    application = serializers.SerializerMethodField()
    datetime = serializers.SerializerMethodField()

    class Meta:
        model = Consultation
        fields = ['id', 'time_selection', 'datetime', 'booking',
                  'price', 'description', 'application']

    def get_datetime(self, obj):
        local_tz = timezone.get_current_timezone()
        return {
            "start": obj.datetime.lower.astimezone(local_tz).strftime('%Y-%m-%d %H:%M'),
            "end": obj.datetime.upper.astimezone(local_tz).strftime('%Y-%m-%d %H:%M')
        }

    def get_application(self, obj):
        return Booked.objects.filter(consultation=obj).values('id', 'status', 'user', 'description')


class BookedAccountSerializer(serializers.ModelSerializer):
    consultation = serializers.SerializerMethodField()

    class Meta:
        model = Booked
        fields = ['id', 'consultation', 'status', 'description']

    def get_consultation(self, obj):
        local_tz = timezone.get_current_timezone()
        consultation = Consultation.objects.get(pk=obj.consultation.id)
        datetime = {
            "start": consultation.datetime.lower.astimezone(local_tz).strftime('%Y-%m-%d %H:%M'),
            "end": consultation.datetime.upper.astimezone(local_tz).strftime('%Y-%m-%d %H:%M')
        }
        return {
            'id': consultation.id,
            'user': consultation.user.id,
            'description': consultation.description,
            'price': consultation.price,
            'datetime': datetime,
            'time_selection': consultation.time_selection,
        }

