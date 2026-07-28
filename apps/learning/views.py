from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response


@api_view(["GET"])
def health_check(request):
    return Response(
        {
            "success": True,
            "status": "healthy",
            "message": "English Learning Tracker API is running.",
        }
    )
