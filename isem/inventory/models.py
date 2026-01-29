from django.db import models
from django.utils import timezone

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
        ('other', 'Other'),
    )
    
    item_name = models.CharField(max_length=200)
    category = models.CharField(max_length=100, choices=CATEGORY_CHOICES)
    description = models.TextField(blank=True)  # Allow empty descriptions
    stock = models.PositiveIntegerField()
    low_stock_threshold = models.IntegerField(default=10) 
    expiry_date = models.DateField(null=True, blank=True)  # Allow empty expiry dates
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.item_name} ({self.stock})"
    
    def is_expired(self):
        if not self.expiry_date:
            return False
        return self.expiry_date < timezone.now().date()

    def update_status(self):  # ← Properly indented inside the class
        """
        Update the status of the inventory item based on its stock and expiry date.
        Priority: Expired > Out of Stock > Low Stock > Available
        """
        # Priority 1: Check if expired
        if self.is_expired():
            self.status = 'expired'
        # Priority 2: Check if out of stock
        elif self.stock == 0:
            self.status = 'out_of_stock'
        # Priority 3: Check if low stock (using threshold)
        elif self.stock <= self.low_stock_threshold:
            self.status = 'low_stock'
        # Otherwise: Available
        else:
            self.status = 'available'
        
        # Debug print
        print(f"[UPDATE_STATUS] {self.item_name}: stock={self.stock}, threshold={self.low_stock_threshold}, status={self.status}")
    
    def save(self, *args, **kwargs):  # ← Properly indented inside the class
        self.update_status()
        super().save(*args, **kwargs)
    
    class Meta:
        ordering = ['-created_at']
