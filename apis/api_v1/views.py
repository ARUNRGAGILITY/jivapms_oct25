from django.http import JsonResponse


def ping(_request):
    return JsonResponse({"status": "ok"})


def info(_request):
    return JsonResponse({
        "name": "JIVAPMS API",
        "version": "v1",
    })
