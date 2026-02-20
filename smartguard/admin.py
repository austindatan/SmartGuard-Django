from django.contrib import admin
from .models import *

# =========================
# ROLE
# =========================
@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('role_id', 'name', 'description')
    search_fields = ('name',)
    list_filter = ('name',)

# =========================
# USER
# =========================
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'username', 'email', 'role', 'created_at')
    search_fields = ('username', 'email')
    list_filter = ('role',)

# =========================
# BUILDING TYPE
# =========================
@admin.register(BuildingType)
class BuildingTypeAdmin(admin.ModelAdmin):
    list_display = ('building_type_id', 'name', 'description')
    search_fields = ('name',)

# =========================
# BUILDING
# =========================
@admin.register(Building)
class BuildingAdmin(admin.ModelAdmin):
    list_display = ('building_id', 'name', 'building_type', 'location', 'created_at')
    search_fields = ('name',)
    list_filter = ('building_type',)

# =========================
# BUILDING USER
# =========================
@admin.register(BuildingUser)
class BuildingUserAdmin(admin.ModelAdmin):
    list_display = ('building_user_id', 'user', 'building')
    search_fields = ('user__username', 'building__name')
    list_filter = ('building',)

# =========================
# SENSOR TYPE
# =========================
@admin.register(SensorType)
class SensorTypeAdmin(admin.ModelAdmin):
    list_display = ('sensortype_id', 'name', 'description')
    search_fields = ('name',)

# =========================
# SENSOR
# =========================
@admin.register(Sensor)
class SensorAdmin(admin.ModelAdmin):
    list_display = ('sensor_id', 'building', 'sensor_type', 'installed_at', 'status')
    search_fields = ('building__name',)
    list_filter = ('sensor_type', 'status')

# =========================
# APPLIANCE
# =========================
@admin.register(Appliance)
class ApplianceAdmin(admin.ModelAdmin):
    list_display = ('appliance_id', 'name', 'sensor')
    search_fields = ('name', 'sensor__sensor_id')
    list_filter = ('sensor__sensor_type',)

# =========================
# ENERGY READING
# =========================
@admin.register(EnergyReading)
class EnergyReadingAdmin(admin.ModelAdmin):
    list_display = ('energyreading_id', 'sensor', 'timestamp', 'voltage', 'current', 'power', 'power_factor')
    search_fields = ('sensor__sensor_id',)
    list_filter = ('sensor__sensor_type',)

# =========================
# ANOMALY TYPE
# =========================
@admin.register(AnomalyType)
class AnomalyTypeAdmin(admin.ModelAdmin):
    list_display = ('anomalytype_id', 'name', 'description')
    search_fields = ('name',)

# =========================
# ANOMALY
# =========================
@admin.register(Anomaly)
class AnomalyAdmin(admin.ModelAdmin):
    list_display = ('anomaly_id', 'energy_reading', 'anomaly_type', 'timestamp', 'severity', 'description')
    search_fields = ('energy_reading__energyreading_id',)
    list_filter = ('anomaly_type', 'severity')

# =========================
# ALERT
# =========================
@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ('alert_id', 'anomaly', 'created_at', 'status', 'message')
    search_fields = ('anomaly__anomaly_id',)
    list_filter = ('status',)