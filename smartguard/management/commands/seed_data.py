from django.core.management.base import BaseCommand
from django.db import transaction
from smartguard.models import (
    Role, User, BuildingType, Building, BuildingUser,
    SensorType, Sensor, Appliance,
    EnergyReading, AnomalyType, Anomaly, Alert
)
import random
from django.utils import timezone
from datetime import timedelta


class Command(BaseCommand):
    help = 'Seed database with realistic random data'

    @transaction.atomic
    def handle(self, *args, **kwargs):
        self.stdout.write("Seeding data...")

        # =========================
        # ROLES
        # =========================
        admin_role, _ = Role.objects.get_or_create(
            name="admin",
            defaults={"description": "Administrator role"}
        )
        homeowner_role, _ = Role.objects.get_or_create(
            name="homeowner",
            defaults={"description": "Homeowner role"}
        )
        technician_role, _ = Role.objects.get_or_create(
            name="technician",
            defaults={"description": "Technician role"}
        )

        # =========================
        # USERS
        # =========================
        usernames = ["apollo", "zeus", "hera", "ares", "athena", "poseidon"]
        roles = [admin_role, homeowner_role, technician_role]
        users = []

        for name in usernames:
            user, created = User.objects.get_or_create(
                username=name,
                defaults={
                    "email": f"{name}@test.com",
                    "password": "test123",
                    "role": random.choice(roles),
                }
            )
            users.append(user)

        # =========================
        # BUILDING TYPES
        # =========================
        residential, _ = BuildingType.objects.get_or_create(
            name="Residential",
            defaults={"description": "Homes and apartments"}
        )
        commercial, _ = BuildingType.objects.get_or_create(
            name="Commercial",
            defaults={"description": "Business establishments"}
        )

        # =========================
        # SENSOR TYPES
        # =========================
        panel_type, _ = SensorType.objects.get_or_create(
            name="Panel Sensor",
            defaults={"description": "Monitors electrical panels"}
        )
        appliance_type, _ = SensorType.objects.get_or_create(
            name="Appliance Sensor",
            defaults={"description": "Monitors appliances"}
        )

        # =========================
        # ANOMALY TYPES
        # =========================
        overload, _ = AnomalyType.objects.get_or_create(
            name="Overload",
            defaults={"description": "Excessive power usage"}
        )
        spike, _ = AnomalyType.objects.get_or_create(
            name="Power Spike",
            defaults={"description": "Sudden surge in power"}
        )

        # =========================
        # BUILDINGS AND USERS
        # =========================
        buildings = []
        for i in range(3):
            building = Building.objects.create(
                name=f"Building {i+1}",
                building_type=random.choice([residential, commercial]),
                location=f"Location {i+1}"
            )
            buildings.append(building)

            # Assign a random user to building
            BuildingUser.objects.create(
                user=random.choice(users),
                building=building
            )

        # =========================
        # SENSORS AND APPLIANCES
        # =========================
        sensors = []
        for building in buildings:
            for i in range(2):
                sensor = Sensor.objects.create(
                    building=building,
                    sensor_type=random.choice([panel_type, appliance_type]),
                    status="Active"
                )
                sensors.append(sensor)

                # Create appliances for sensor
                for j in range(random.randint(1, 3)):
                    Appliance.objects.create(
                        sensor=sensor,
                        name=f"Appliance {j+1}"
                    )

        # =========================
        # ENERGY READINGS
        # =========================
        readings = []
        base_time = timezone.now()

        for sensor in sensors:
            for i in range(100):
                voltage = random.uniform(210, 240)
                current = random.uniform(5, 20)
                power = voltage * current

                # simulate spikes
                if random.random() < 0.1:
                    power *= random.uniform(1.5, 2.5)

                reading = EnergyReading.objects.create(
                    sensor=sensor,
                    timestamp=base_time - timedelta(minutes=i),
                    voltage=voltage,
                    current=current,
                    power=power,
                    power_factor=random.uniform(0.7, 1.0)
                )
                readings.append(reading)

        # =========================
        # ANOMALIES AND ALERTS
        # =========================
        for i in range(10):
            reading = random.choice(readings)
            anomaly = Anomaly.objects.create(
                energy_reading=reading,
                anomaly_type=random.choice([overload, spike]),
                timestamp=reading.timestamp,
                severity=random.randint(1, 5),
                description="Simulated anomaly detected"
            )

            Alert.objects.create(
                anomaly=anomaly,
                status=random.choice(["Active", "Resolved"]),
                message="System detected abnormal energy usage"
            )

        self.stdout.write(self.style.SUCCESS("✅ Seeding completed successfully!"))