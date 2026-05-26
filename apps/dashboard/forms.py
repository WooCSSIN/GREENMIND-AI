"""
GreenMind Dashboard - Forms
Form validation cho authentication và các operations khác
"""

from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
import re


class RegisterForm(forms.Form):
    """Form đăng ký với validation tự động"""
    
    username = forms.CharField(
        max_length=50,
        required=True,
        label="Tên đăng nhập",
        widget=forms.TextInput(attrs={
            'class': 'w-full bg-dark-950/50 border border-white/5 rounded-xl text-white px-4 py-3 font-mono text-xs focus:border-brand-500/50 outline-none transition-all',
            'placeholder': 'username'
        })
    )
    
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full bg-dark-950/50 border border-white/5 rounded-xl text-white px-4 py-3 font-mono text-xs focus:border-brand-500/50 outline-none transition-all',
            'placeholder': '••••••••'
        }),
        min_length=6,
        label="Mật khẩu",
        help_text="Mật khẩu phải có ít nhất 6 ký tự"
    )
    
    password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full bg-dark-950/50 border border-white/5 rounded-xl text-white px-4 py-3 font-mono text-xs focus:border-brand-500/50 outline-none transition-all',
            'placeholder': '••••••••'
        }),
        label="Xác nhận mật khẩu"
    )
    
    email = forms.EmailField(
        required=True,
        label="Email",
        widget=forms.EmailInput(attrs={
            'class': 'w-full bg-dark-950/50 border border-white/5 rounded-xl text-white px-4 py-3 font-mono text-xs focus:border-brand-500/50 outline-none transition-all',
            'placeholder': 'email@gmail.com'
        })
    )
    
    fullname = forms.CharField(
        max_length=100,
        required=True,
        label="Họ và tên",
        widget=forms.TextInput(attrs={
            'class': 'w-full bg-dark-950/50 border border-white/5 rounded-xl text-white px-4 py-3 font-mono text-xs focus:border-brand-500/50 outline-none transition-all',
            'placeholder': 'Trần Văn A'
        })
    )
    
    phone = forms.CharField(
        max_length=20,
        required=True,
        label="Số điện thoại",
        widget=forms.TextInput(attrs={
            'class': 'w-full bg-dark-950/50 border border-white/5 rounded-xl text-white px-4 py-3 font-mono text-xs focus:border-brand-500/50 outline-none transition-all',
            'placeholder': '090...'
        })
    )
    
    date_of_birth = forms.DateField(
        required=True,
        label="Ngày sinh",
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'w-full bg-dark-950/50 border border-white/5 rounded-xl text-white px-4 py-3 font-mono text-xs focus:border-brand-500/50 outline-none transition-all'
        })
    )
    
    def clean_username(self):
        """Validate username không trùng và hợp lệ"""
        username = self.cleaned_data.get('username')
        
        # Check format (chỉ cho phép chữ, số, underscore)
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            raise ValidationError("Tên đăng nhập chỉ được chứa chữ cái, số và dấu gạch dưới.")
        
        # Check duplicate
        if User.objects.filter(username=username).exists():
            raise ValidationError(f"Tên đăng nhập '{username}' đã tồn tại trong hệ thống.")
        
        return username
    
    def clean_email(self):
        """Validate email không trùng"""
        email = self.cleaned_data.get('email')
        
        if User.objects.filter(email=email).exists():
            raise ValidationError(f"Email '{email}' đã được sử dụng.")
        
        return email
    
    def clean_phone(self):
        """Validate phone number format"""
        phone = self.cleaned_data.get('phone')
        
        # Remove spaces and dashes
        phone = phone.replace(' ', '').replace('-', '')
        
        # Check if it's all digits and has valid length
        if not phone.isdigit() or len(phone) < 10 or len(phone) > 11:
            raise ValidationError("Số điện thoại không hợp lệ (phải có 10-11 chữ số).")
        
        return phone
    
    def clean(self):
        """Validate password match"""
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        
        if password and password_confirm and password != password_confirm:
            raise ValidationError({
                'password_confirm': "Mật khẩu xác nhận không trùng khớp."
            })
        
        return cleaned_data


class LoginForm(forms.Form):
    """Form đăng nhập đơn giản"""
    
    username = forms.CharField(
        max_length=50,
        label="Tên đăng nhập",
        widget=forms.TextInput(attrs={
            'class': 'w-full bg-dark-950/50 border border-white/5 group-hover:border-white/10 rounded-2xl text-white px-6 py-5 font-mono text-xs focus:ring-1 focus:ring-brand-500/50 focus:border-brand-500/50 outline-none transition-all placeholder-gray-800',
            'placeholder': 'Nhập tên đăng nhập...'
        })
    )
    
    password = forms.CharField(
        label="Mật khẩu",
        widget=forms.PasswordInput(attrs={
            'class': 'w-full bg-dark-950/50 border border-white/5 group-hover:border-white/10 rounded-2xl text-white px-6 py-5 font-mono text-xs focus:ring-1 focus:ring-brand-500/50 focus:border-brand-500/50 outline-none transition-all placeholder-gray-800',
            'placeholder': '••••••••'
        })
    )


class TransactionForm(forms.Form):
    """Form cho giao dịch nhập/xuất kho"""
    
    TRANSACTION_TYPES = [
        ('inbound', 'Nhập kho'),
        ('outbound', 'Xuất kho')
    ]
    
    sku = forms.CharField(
        max_length=100,
        required=True,
        label="Mã SKU"
    )
    
    type = forms.ChoiceField(
        choices=TRANSACTION_TYPES,
        required=True,
        label="Loại giao dịch"
    )
    
    quantity = forms.FloatField(
        min_value=0.01,
        required=True,
        label="Số lượng"
    )
    
    price = forms.FloatField(
        min_value=0,
        required=True,
        label="Đơn giá"
    )
    
    def clean_quantity(self):
        """Validate quantity > 0"""
        qty = self.cleaned_data['quantity']
        if qty <= 0:
            raise ValidationError("Số lượng phải lớn hơn 0")
        return qty
    
    def clean_price(self):
        """Validate price >= 0"""
        price = self.cleaned_data['price']
        if price < 0:
            raise ValidationError("Đơn giá không được âm")
        return price
