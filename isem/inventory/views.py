from django.shortcuts import render, get_object_or_404, redirect
from .models import InventoryItem
from .forms import InventoryItemForm

# LIST
def inventory_list(request):
    items = InventoryItem.objects.all().order_by('-created_at')
    form = InventoryItemForm()  # Empty form for adding new items
    return render(request, 'inventory/inventory.html', {'items': items,
                                                        'form': form})

# ADD ITEM
# def inventory_add(request):
#     if request.method == 'POST':
#         form = InventoryItemForm(request.POST)
#         if form.is_valid():
#             item = form.save(commit=False)
#             item.update_status()
#             item.save()  
#             print("✅ Item saved:", item) 
#             return redirect('inventory:list') 
#     else: print("❌ Form errors:", form.errors)  # <---- debug
#     return redirect('inventory:list')

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
    if request.method == 'POST':
        form = InventoryItemForm(request.POST, instance=item)
        if form.is_valid():
            item = form.save(commit=False)
            item.update_status()
            item.save()  # <--- missing in your code
            return redirect('inventory:list')
    else:
        form = InventoryItemForm(instance=item)
    return render('inventory: list')

# DELETE
def inventory_delete(request, pk):
    item = get_object_or_404(InventoryItem, pk=pk)
    if request.method == 'POST':
        item.delete()
        return redirect('inventory:list')
    return render(request, 'inventory/inventory_delete.html', {'item': item})
