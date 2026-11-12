"""Validated query filters; callers first scope querysets to their owner."""

from datetime import datetime, time, timedelta, timezone

from rest_framework import serializers

from .timezones import get_user_timezone


class DateRangeQuerySerializer(serializers.Serializer):
    date_from = serializers.DateField(required=False)
    date_to = serializers.DateField(required=False)

    def validate(self, attrs):
        if attrs.get("date_from") and attrs.get("date_to"):
            if attrs["date_from"] > attrs["date_to"]:
                raise serializers.ValidationError(
                    {"date_to": "Must be on or after date_from."}, code="invalid_date_range"
                )
        return attrs


def filter_dates(queryset, request, field, *, datetime_field=False):
    query = DateRangeQuerySerializer(data=request.query_params)
    query.is_valid(raise_exception=True)
    dates = query.validated_data
    if not datetime_field:
        if "date_from" in dates:
            queryset = queryset.filter(**{f"{field}__gte": dates["date_from"]})
        if "date_to" in dates:
            queryset = queryset.filter(**{f"{field}__lte": dates["date_to"]})
        return queryset
    user_timezone = get_user_timezone(request.user)
    if "date_from" in dates:
        try:
            start = datetime.combine(dates["date_from"], time.min, tzinfo=user_timezone).astimezone(
                timezone.utc
            )
        except (OverflowError, ValueError) as exc:
            raise serializers.ValidationError(
                {"date_from": "Date is outside the supported range."}
            ) from exc
        queryset = queryset.filter(**{f"{field}__gte": start})
    if "date_to" in dates:
        try:
            following_day = dates["date_to"] + timedelta(days=1)
        except OverflowError as exc:
            raise serializers.ValidationError(
                {"date_to": "Date is outside the supported range."}
            ) from exc
        try:
            end = datetime.combine(following_day, time.min, tzinfo=user_timezone).astimezone(
                timezone.utc
            )
        except (OverflowError, ValueError) as exc:
            raise serializers.ValidationError(
                {"date_to": "Date is outside the supported range."}
            ) from exc
        queryset = queryset.filter(**{f"{field}__lt": end})
    return queryset


def filter_choice(queryset, request, field, choices):
    value = request.query_params.get(field)
    if value is None:
        return queryset
    if value not in dict(choices):
        raise serializers.ValidationError({field: "Select a valid choice."}, code="invalid_filter")
    return queryset.filter(**{field: value})
