# Simulador Agroflorestal Regenera (SAR)
# Copyright (C) 2026  Lucas Marques and Regenera Mata Atlântica

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses>.

from authemail.admin import EmailUserAdmin
from django.contrib import admin
# from django.contrib.auth.admin import UserAdmin
from django.contrib.auth import get_user_model
# from .models import Users

# Register your models here.

class UserAdmin(EmailUserAdmin):
	fieldsets = (
		(None, {'fields': ('email', 'password')}),
		('Personal Info', {'fields': ('first_name', 'last_name')}),
		('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'is_verified')}), #, 'groups', 'user_permissions')}),
		('Important dates', {'fields': ('last_login', 'date_joined')}),
		# ('Custom info', {'fields': ('date_of_birth',)}),
	)

admin.site.unregister(get_user_model())
admin.site.register(get_user_model(), UserAdmin)
