from pyexpat.errors import messages
from urllib import request
from django.shortcuts import render, get_object_or_404, redirect
from .models import InventoryItem
from .forms import InventoryItemForm
from django.http import JsonResponse, HttpResponse

# LIST
def inventory_list(request):
    items = InventoryItem.objects.all().order_by('-created_at')
    form = InventoryItemForm()  # Empty form for adding new items
    return render(request, 'inventory/inventory.html', {'items': items,
                                                        'form': form})

def inventory_add(request):
    if request.method == 'POST':
        print("POST DATA:", request.POST)  # <-- debug
        form = InventoryItemForm(request.POST)
        if form.is_valid():
            print("FORM IS VALID")  # <-- debug
            item = form.save(commit=False)
            item.update_status()
            item.save()
            print("ITEM SAVED:", item)  # <-- debug
            return redirect('inventory:list')
        else:
            print("FORM ERRORS:", form.errors)  # <-- debug

    return redirect('inventory:list')

# EDIT
def inventory_edit(request, pk):

    item = get_object_or_404(InventoryItem, pk=pk)

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        # AJAX request → return JSON
        return JsonResponse({
            "id": item.id,
            "item_name": item.item_name,
            "category": item.category,
            "description": item.description,
            "stock": item.stock,
            "expiry_date": item.expiry_date.strftime("%Y-%m-%d") if item.expiry_date else "",
            "status": item.status,
        })

    if request.method == "POST":
        # handle form submission (update the item)
        item.item_name = request.POST.get("item_name")
        item.category = request.POST.get("category")
        item.description = request.POST.get("description")
        item.stock = request.POST.get("stock")
        item.expiry_date = request.POST.get("expiry_date")
        item.status = request.POST.get("status")
        item.save()

        return redirect("inventory:list")  # adjust to your inventory list URL name

    # fallback if someone goes directly to /edit/
    return render(request, "inventory/edit.html", {"item": item})
# DELETE
def inventory_delete(request, pk):
    if request.method == "POST":
        try:
            item = InventoryItem.objects.get(pk=pk)
            item.delete()
            return JsonResponse({"success": True, "message": "Item deleted successfully."})
        except InventoryItem.DoesNotExist:
            return JsonResponse({"success": False, "message": "Item already deleted."}, status=404)
    return JsonResponse({"success": False, "message": "Invalid request"}, status=400)

