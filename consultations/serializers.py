from psycopg2.extras import DateTimeTZRange
from datetime import timedelta, datetime as dt

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from .models import Consultation, Booked


class BaseResponseSerializer(serializers.Serializer):
    status = serializers.CharField()
    data = serializers.JSONField()  # Универсальное поле для подстановки данных
    errors = serializers.DictField(allow_null=True, required=False)


class ConsultationSerializer(serializers.ModelSerializer):
    datetime = serializers.SerializerMethodField()

    class Meta:
        model = Consultation
        fields = ['id', 'user', 'time_selection', 'datetime', 'booking', 'price', 'description', 'archive']
        read_only_fields = ['id', "user", "datetime", "archive", "booking"]

    def get_datetime(self, obj):
        return {
            "start": obj.datetime.lower.strftime('%Y-%m-%d %H:%M'),
            "end": obj.datetime.upper.strftime('%Y-%m-%d %H:%M')
        }

    def validate_rejection_text(self, rejection_text):
        if not rejection_text:
            raise ValidationError({'rejection_text': 'Причина отказа обязательна для заполнения.'})

    def validate(self, data):
        request_method = self.context['request'].method
        user = self.context['request'].user

        if request_method == 'PATCH' and not self.initial_data:
            raise ValidationError({'data': 'Никакие данные не были переданы.'})

        if request_method == 'POST' or 'datetime' in self.initial_data or 'time_selection' in data:
            if self.instance and 'datetime' not in self.initial_data:
                start_time = self.instance.datetime.lower.replace(tzinfo=None)
            else:
                try:
                    start_time = dt.strptime(self.initial_data['datetime'], '%Y-%m-%d %H:%M')
                except (KeyError, ValueError):
                    raise ValidationError({'datetime': 'Ошибка с датой и временем.'})

            if self.instance and 'time_selection' not in data:
                time_selection = self.instance.time_selection
            else:
                time_selection = data.get('time_selection', '1')

            current_time = dt.now()

            # Проверка на создание записи в будущем
            if start_time < current_time:
                raise ValidationError({'datetime': 'Нельзя создавать запись на прошедшую дату.'})

            end_time = start_time + timedelta(hours=int(time_selection))
            datetime_range = DateTimeTZRange(start_time, end_time)

            calendar_item_id = self.instance.id if self.instance else None

            overlapping_items = Consultation.objects.filter(
                user=user,
                datetime__overlap=datetime_range,
                archive=False,
            )
            if calendar_item_id:
                overlapping_items = overlapping_items.exclude(id=calendar_item_id)

            if overlapping_items.exists():
                raise ValidationError({'datetime': 'Запись пересекается с существующей записью.'})

            data['datetime'] = datetime_range

        return data

    def validate_price(self, value):
        if value < 0:
            raise ValidationError('Цена не может быть отрицательной.')
        return value


class BookedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booked
        fields = '__all__'
        read_only_fields = ["user", "archive", 'status']

    def validate(self, data):
        user = self.context['request'].user

        if self.context['request'].method == 'PATCH' and 'description' not in self.initial_data:
            raise ValidationError({'description': 'Изменить можно только описание.'})

        if self.context['request'].method == 'POST':
            consultation = data['consultation']

            bookeds = Booked.objects.filter(user=user, consultation=consultation)

            if any(booked.status != 'Cancelled' for booked in bookeds):
                raise ValidationError({'consultation': 'Вы уже отправили заявку бронирования на эту консультацию.'})

            if consultation.user == user:
                raise ValidationError({'consultation': 'Вы не можете записаться на собственную консультацию.'})

            if consultation.booking:
                raise ValidationError({'consultation': 'Консультация уже забронирована.'})

        return data

    def validate_rejection_text(self, rejection_text):
        if not rejection_text:
            raise ValidationError({'rejection_text': 'Причина отказа обязательна для заполнения.'})
