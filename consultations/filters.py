from django_filters import rest_framework as filters

from .models import Booked, Consultation


class ConsultationFilter(filters.FilterSet):
    user_id = filters.CharFilter(field_name="user__id", lookup_expr='icontains')
    user_username = filters.CharFilter(field_name="user__username", lookup_expr='icontains')
    archive = filters.BooleanFilter(field_name="archive")
    booking = filters.BooleanFilter(field_name="booking")
    price = filters.RangeFilter()
    time_selection = filters.ChoiceFilter(choices=Consultation.POSITIONS_TIME_SELECTION)
    datetime = filters.DateTimeFromToRangeFilter(field_name="datetime")

    class Meta:
        model = Consultation
        fields = ['user_id', 'user_username',
                  'archive', 'booking',
                  'price', 'time_selection',
                  'datetime']


class BookedFilter(filters.FilterSet):
    user_id = filters.CharFilter(field_name="id", lookup_expr='icontains')
    user_username = filters.CharFilter(field_name="user__username", lookup_expr='icontains')
    consultation_id = filters.CharFilter(field_name="consultation__id", lookup_expr='icontains')
    consultation_owner_id = filters.CharFilter(field_name="consultation__user__id", lookup_expr='icontains')
    consultation_owner_name = filters.CharFilter(field_name="consultation__user__username", lookup_expr='icontains')
    status = filters.ChoiceFilter(choices=Booked.POSITIONS_STATUS)
    archive = filters.BooleanFilter(field_name="archive")
    consultation_datetime = filters.DateTimeFromToRangeFilter(field_name="consultation__datetime")

    class Meta:
        model = Booked
        fields = ['user_id', 'user_username',
                  'status', 'archive',
                  'consultation_id', 'consultation_owner_id',
                  'consultation_owner_name', 'consultation_datetime']
