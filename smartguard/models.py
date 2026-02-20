from django.db import models


class Role(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('homeowner', 'Homeowner'),
        ('technician', 'Technician'),
    ]
    role_id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=20, choices=ROLE_CHOICES)
    description = models.TextField()

    def __str__(self):
        return self.name


class User(models.Model):
    user_id = models.BigAutoField(primary_key=True)
    username = models.CharField(max_length=20)
    email = models.CharField(max_length=30)
    password = models.CharField(max_length=128)
    created_at = models.DateField(auto_now_add=True)
    role = models.ForeignKey(Role, on_delete=models.CASCADE)

    def __str__(self):
        return self.username

class BuildingType(models.Model):
    building_type_id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=20)
    description = models.TextField()

    def __str__(self):
        return self.name

class Building(models.Model):
    building_id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=20)
    building_type = models.ForeignKey(BuildingType, on_delete=models.CASCADE)
    location = models.CharField(max_length=30)
    created_at = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.name

class BuildingUser(models.Model):
    building_user_id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    building = models.ForeignKey(Building, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.user} - {self.building}"

class SensorType(models.Model):
    sensortype_id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=20)
    description = models.TextField()

    def __str__(self):
        return self.name

class Sensor(models.Model):
    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Inactive', 'Inactive'),
    ]

    sensor_id = models.BigAutoField(primary_key=True)
    building = models.ForeignKey(Building, on_delete=models.CASCADE)
    sensor_type = models.ForeignKey(SensorType, on_delete=models.CASCADE)
    installed_at = models.DateField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)

    def __str__(self):
        return f"Sensor {self.sensor_id} ({self.building.location})"

class Appliance(models.Model):
    appliance_id = models.BigAutoField(primary_key=True)
    sensor = models.ForeignKey(Sensor, on_delete=models.CASCADE)
    name = models.CharField(max_length=20)

    def __str__(self):
        return self.name

class EnergyReading(models.Model):
    energyreading_id = models.BigAutoField(primary_key=True)
    sensor = models.ForeignKey(Sensor, on_delete=models.CASCADE)
    timestamp = models.DateTimeField()
    voltage = models.FloatField()
    current = models.FloatField()
    power = models.FloatField()
    power_factor = models.FloatField()

    def __str__(self):
        return f"Reading {self.energyreading_id} - {self.timestamp}"

class AnomalyType(models.Model):
    anomalytype_id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=20)
    description = models.TextField()

    def __str__(self):
        return self.name


class Anomaly(models.Model):
    anomaly_id = models.BigAutoField(primary_key=True)
    energy_reading = models.ForeignKey(EnergyReading, on_delete=models.CASCADE)
    anomaly_type = models.ForeignKey(AnomalyType, on_delete=models.CASCADE)
    timestamp = models.DateTimeField()
    severity = models.IntegerField()
    description = models.TextField()

    def __str__(self):
        return f"Anomaly {self.anomaly_id}"


class Alert(models.Model):
    alert_id = models.BigAutoField(primary_key=True)
    anomaly = models.ForeignKey(Anomaly, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20)
    message = models.TextField()

    def __str__(self):
        return f"Alert {self.alert_id}"