from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from .models import Order


def manage_orders(request):
    # Обработка быстрого обновления статуса через JavaScript
    if request.method == "POST" and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        order_id = request.POST.get("order_id")
        new_status = request.POST.get("status")

        try:
            order = get_object_or_404(Order, id=order_id)
            order.status = new_status
            order.save()
            return JsonResponse({"status": "success", "message": "Статус обновлен"})
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)

    # Обычный рендеринг страницы
    orders = Order.objects.all().order_by("-created_at")

    # Замени этот список на свои реальные статусы из модели (например, Order.STATUS_CHOICES)
    status_choices = ["pending", "processing", "completed", "cancelled"]

    return render(request, "manage_orders.html", {
        "orders": orders,
        "status_choices": status_choices
    })