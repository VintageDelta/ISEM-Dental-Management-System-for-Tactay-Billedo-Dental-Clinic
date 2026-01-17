from django.db import models
from django.utils import timezone
# Create your models here.

class InventoryItem(models.Model):
    STATUS_CHOICES = (
        ('available', 'Available'),
        ('low_stock', 'Low Stock'),
        ('out_of_stock', 'Out of Stock'),
        ('expired', 'Expired'),
    )

    CATEGORY_CHOICES = (
        ('consumable', 'Consumable'),
        ('equipment', 'Equipment'),
        # ('medicine', 'Medicine'),
        ('other', 'Other'),
    )
    item_name = models.CharField(max_length=200)
    category = models.CharField(max_length=100, choices=CATEGORY_CHOICES)
    description = models.TextField()
    stock = models.PositiveIntegerField()
    expiry_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return f"{self.item_name}  ({self.stock})"
    
    def is_expired(self):
        if not self.expiry_date:
            return False
        return self.expiry_date < timezone.now().date()

    def update_status(self):
        """
        Update the status of the inventory item based on its stock and expiry date.
        """
        if self.is_expired():
            self.status = 'expired'
        elif self.stock == 0:
            self.status = 'out_of_stock'
        elif self.stock < 5:
            self.status = 'low_stock'
        else:
            self.status = 'available'
    
    def save(self, *args, **kwargs):
        self.update_status()
        super().save(*args, **kwargs)