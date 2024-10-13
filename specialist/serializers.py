from rest_framework import serializers

from specialist.models import Candidates, Specialist


class SpecialistSerializer(serializers.ModelSerializer):
    class Meta:
        model = Specialist
        fields = "__all__"
        read_only_fields = ["user", 'is_active']


class CandidatesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Candidates
        fields = "__all__"
        read_only_fields = ["status", "created_at", "user", "rejection_text"]

    def validate(self, data):
        user = self.context["request"].user
        user_candidates = Candidates.objects.filter(user=user)

        if self.instance is None:
            if user_candidates.exists():
                raise serializers.ValidationError({'user': 'Заявка уже отправлена.'})

        return data

    def validate_status_transition(self, instance):
        if instance.status != 'In processing':
            raise serializers.ValidationError({
                'status': f'Заявка уже имеет статус {instance.status} и не может быть изменена.'
            })

    def validate_rejection_text(self, rejection_text):
        if not rejection_text:
            raise serializers.ValidationError({
                'rejection_text': 'Причина отказа, обязательна для заполнения.'
            })

    def validate_reapplication_description(self, reapplication_text):
        if not reapplication_text:
            raise serializers.ValidationError({
                'description': 'Описание, обязательна для заполнения.'
            })

    def validate_reapplication_status(self, reapplication_status):
        if reapplication_status != "Cancelled":
            raise serializers.ValidationError({
                'status': 'Нельзя подать повторную заявку, если предыдущая находится в процессе обработки или уже была принята.',
            })
