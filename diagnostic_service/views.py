from rest_framework import viewsets, serializers
from .models import Inspection
from django.http import JsonResponse
import requests

class InspectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Inspection
        fields = '__all__'

class InspectionViewSet(viewsets.ModelViewSet):
    queryset = Inspection.objects.all()
    serializer_class = InspectionSerializer

def run_diagnostic_api(request):
    """
    API interne appelée par Location Service.
    Envoie l'image à l'AI_SERVICE et enregistre l'inspection.
    """
    if request.method == 'POST':
        car_id = request.POST.get('car_id')
        image = request.FILES.get('image')
        
        # 1. Appel au microservice AI (Port 8000)
        # Simulation pour le TP
        ai_data = {"status": "success", "damage_detected": "Rayure détectée", "confidence": 0.85}
        
        # 2. Sauvegarde locale dans diagnostic_db
        inspection = Inspection.objects.create(
            car_id=car_id,
            image_input=image,
            result_json=ai_data
        )
        
        return JsonResponse({
            "id": inspection.id,
            "status": "completed",
            "result": ai_data
        })
    return JsonResponse({"error": "POST request required"}, status=400)
