from django import forms
from .models import InventoryItem

class InventoryItemForm(forms.ModelForm):
    class Meta:
        model = InventoryItem
        fields = ['item_name', 'category', 'description', 'stock', 'low_stock_threshold', 'expiry_date']
        widgets = {
            'item_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter item name'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter description'}),
            'stock': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'placeholder': 'Enter stock quantity'}),
            'low_stock_threshold': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'placeholder': 'Enter low stock threshold (default: 10)'}),
            'expiry_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }
        labels = {
            'item_name': 'Item Name',
            'category': 'Category',
            'description': 'Description',
            'stock': 'Stock Quantity',
            'low_stock_threshold': 'Low Stock Threshold',
            'expiry_date': 'Expiry Date',
        }