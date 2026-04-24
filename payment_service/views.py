from django.http import JsonResponse
from .models import Transaction
import uuid

def process_payment(request):
    """
    API Microservice : Simule le traitement d'un paiement.
    """
    if request.method == 'POST':
        booking_id = request.POST.get('booking_id')
        amount = request.POST.get('amount')
        
        # Simulation de transaction bancaire
        transaction = Transaction.objects.create(
            booking_id=booking_id,
            amount=amount,
            status='completed',
            transaction_id=str(uuid.uuid4())
        )
        
        return JsonResponse({
            "status": "success",
            "transaction_id": transaction.transaction_id,
            "message": "Paiement validé avec succès"
        })
    return JsonResponse({"error": "POST required"}, status=400)
