from django_filters import rest_framework as filters
from .models import UserProfile, User


class UserProfileFilter(filters.FilterSet):
    min_age = filters.NumberFilter(field_name="user__birth_date", lookup_expr='year__lte', method='filter_by_age')
    max_age = filters.NumberFilter(field_name="user__birth_date", lookup_expr='year__gte', method='filter_by_age')
    gender = filters.CharFilter(field_name='user__gender')

    class Meta:
        model = UserProfile
        fields = ['city', 'status', 'gender']

    def filter_by_age(self, queryset, name, value):
        from django.utils import timezone
        today = timezone.now().date()

        if name == 'min_age':
            # People born before or on this year
            birth_year = today.year - int(value)
            return queryset.filter(user__birth_date__year__lte=birth_year)
        if name == 'max_age':
            # People born after or on this year
            birth_year = today.year - int(value)
            return queryset.filter(user__birth_date__year__gte=birth_year)
        return queryset