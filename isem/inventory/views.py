import datetime
from pyexpat.errors import messages
from urllib import request
from django.shortcuts import render, get_object_or_404, redirect
from .models import InventoryItem
from .forms import InventoryItemForm
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.shortcuts import render
from django.contrib import messages
from django.db.models import Q

# LIST
def inventory_list(request):
    for item in InventoryItem.objects.all():
        item.save()
    qs = InventoryItem.objects.all().order_by('-created_at')
    

    paginator = Paginator(qs, 5)  # Show 5 items per page
    page_number = request.GET.get('page')
    items = paginator.get_page(page_number)
    page_obj = items

     # Form for adding new items
    form = InventoryItemForm()  # Empty form for adding new items

    today = datetime.date.today()
    upcoming = today + datetime.timedelta(days=7)

    expiring_items = InventoryItem.objects.filter(expiry_date__gte=today,
                                                  expiry_date__lte=upcoming,
                                                  ).exclude(expiry_date= None).exclude(status='expired').exclude(status='out_of_stock')
    

    expired_items = InventoryItem.objects.filter(status='expired').order_by('-expiry_date')

    out_of_stock_items = InventoryItem.objects.filter(status='out_of_stock').order_by('-updated_at')

    return render(request, 'inventory/inventory.html', {
                                                        'items': page_obj.object_list,
                                                        'page_obj': page_obj,
                                                        'form': form,
                                                        'expiring_list': expiring_items,
                                                        'has_expiring_items': expiring_items.exists(),
                                                        'expired_items': expired_items,
                                                        'out_of_stock_items': out_of_stock_items,
                                                        'has_out_of_stock_items': out_of_stock_items.exists(),})


def inventory_add(request):
    if request.method == 'POST':
        
        form = InventoryItemForm(request.POST)
        if form.is_valid():
            
            item = form.save(commit=False)
            item.update_status()
            item.save()
            messages.success(request, "Item added successfully.")
            return redirect('inventory:list')
        else:
            print("FORM ERRORS:", form.errors)  
            
    return redirect('inventory:list')

# EDIT
def inventory_edit(request, pk):
    item = get_object_or_404(InventoryItem, pk=pk)

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({
            "id": item.id,
            "item_name": item.item_name,
            "category": item.category,
            "description": item.description,
            "stock": item.stock,
            "low_stock_threshold": getattr(item, 'low_stock_threshold', 10),  # Safe access
            "expiry_date": item.expiry_date.strftime("%Y-%m-%d") if item.expiry_date else "",
            "status": item.status,
        })

    if request.method == "POST":
        item.item_name = request.POST.get("item_name")
        item.category = request.POST.get("category")
        item.description = request.POST.get("description")
        
        stock = request.POST.get("stock")
        if stock:
            item.stock = int(stock)
        
        threshold = request.POST.get("low_stock_threshold")
        if threshold:
            item.low_stock_threshold = int(threshold)
        else:
            item.low_stock_threshold = 10
        
        expiry = request.POST.get("expiry_date")
        if expiry:
            item.expiry_date = datetime.datetime.strptime(expiry, "%Y-%m-%d").date()
        else:
            item.expiry_date = None
        
        item.save()
        messages.success(request, "Item updated successfully.")
        return redirect("inventory:list")

    return render(request, "inventory/edit.html", {"item": item})

# DELETE
def inventory_delete(request, pk):
    """Delete an inventory item"""
    if request.method == "POST":
        item = get_object_or_404(InventoryItem, pk=pk)
        item.delete()
        messages.success(request, "Inventory item deleted successfully!")
        return JsonResponse({"status": "ok"})
    return JsonResponse({"status": "error"}, status=400)


def inventory_view(request, pk):
    item = get_object_or_404(InventoryItem, pk=pk)
    return JsonResponse({
        "id": item.id,
        "item_name": item.item_name,
        "category": item.category,
        "description": item.description,
        "stock": item.stock,
        "low_stock_threshold": item.low_stock_threshold,  # Add this line
        "expiry_date": item.expiry_date.strftime("%Y-%m-%d") if item.expiry_date else "",
        "status": item.status,
    })


def search_inventory(request):
    """AJAX endpoint for live inventory search"""
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        search_query = request.GET.get('search', '').strip()
        
        if search_query:
            # Search by item_name, category, or description
            items = InventoryItem.objects.filter(
                Q(item_name__icontains=search_query) |
                Q(category__icontains=search_query) |
                Q(description__icontains=search_query)
            )[:10]  # Limit to 10 results
            
            items_data = []
            for item in items:
                items_data.append({
                    'id': item.id,
                    'item_name': item.item_name,
                    'category': item.category,
                    'stock': item.stock,
                    'status': item.status,
                })
            
            return JsonResponse({'items': items_data})
        else:
            return JsonResponse({'items': []})
    
    return JsonResponse({'error': 'Invalid request'}, status=400)
