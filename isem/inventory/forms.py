from django import forms
from .models import InventoryItem

class InventoryItemForm(forms.ModelForm):

    expiry_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        input_formats=['%Y-%m-%d']
    )
    class Meta:
        model = InventoryItem
        fields = ['item_name', 'category', 'description', 'stock', 'expiry_date', 'status']
        widgets = {
            'item_name': forms.TextInput(attrs={
                'class': 'w-full border border-gray-300 rounded-md p-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'Item Name'
            }),
            'category': forms.TextInput(attrs={
                'class': 'w-full border border-gray-300 rounded-md p-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'Category'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full border border-gray-300 rounded-md p-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'rows': 3,
                'placeholder': 'Description'
            }),
            'stock': forms.NumberInput(attrs={
                'class': 'w-full border border-gray-300 rounded-md p-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'Stock'
            }),
            'expiry_date': forms.DateInput(attrs={
                'class': 'w-full border border-gray-300 rounded-md p-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'type': 'date'
            }),
            'status': forms.Select(attrs={
                'class': 'w-full border border-gray-300 rounded-md p-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
            }),
        }