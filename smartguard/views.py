from django.shortcuts import render
from django.db.models import Avg, Max, Min, Count, Sum, FloatField, F, Q
from django.db.models.functions import ExtractHour, TruncDay
from django.utils import timezone
from datetime import timedelta
import json

from .models import (
    Building, BuildingType, Sensor, Appliance,
    EnergyReading, Anomaly, AnomalyType, Alert, User, Role
)


def analytics(request):
    # ─── KPI SUMMARY CARDS ─────────────────────────────────────────────────────
    total_buildings   = Building.objects.count()
    total_sensors     = Sensor.objects.count()
    total_appliances  = Appliance.objects.count()
    total_readings    = EnergyReading.objects.count()
    total_anomalies   = Anomaly.objects.count()
    total_alerts      = Alert.objects.count()
    active_alerts     = Alert.objects.filter(status="Active").count()
    resolved_alerts   = Alert.objects.filter(status="Resolved").count()
    avg_power         = EnergyReading.objects.aggregate(avg=Avg('power'))['avg'] or 0
    avg_power_factor  = EnergyReading.objects.aggregate(avg=Avg('power_factor'))['avg'] or 0
    max_power         = EnergyReading.objects.aggregate(max=Max('power'))['max'] or 0

    # ─── 1. ENERGY SPIKES PER BUILDING ─────────────────────────────────────────
    spike_threshold = avg_power * 1.5

    spikes_per_building = []
    for building in Building.objects.all():
        sensors = Sensor.objects.filter(building=building)
        for sensor in sensors:
            spike_readings = EnergyReading.objects.filter(
                sensor=sensor, power__gt=spike_threshold
            ).count()
            appliances = list(Appliance.objects.filter(sensor=sensor).values_list('name', flat=True))
            if spike_readings > 0:
                spikes_per_building.append({
                    'building': building.name,
                    'sensor_id': sensor.sensor_id,
                    'appliances': ', '.join(appliances) if appliances else 'None',
                    'spike_count': spike_readings,
                    'max_power': EnergyReading.objects.filter(
                        sensor=sensor, power__gt=spike_threshold
                    ).aggregate(max=Max('power'))['max'] or 0,
                })

    spikes_per_building_sorted = sorted(spikes_per_building, key=lambda x: x['spike_count'], reverse=True)[:8]
    chart_spike_labels    = [f"{s['building']} / S{s['sensor_id']}" for s in spikes_per_building_sorted]
    chart_spike_counts    = [s['spike_count'] for s in spikes_per_building_sorted]
    chart_spike_max_power = [round(s['max_power'], 2) for s in spikes_per_building_sorted]

    # ─── 2. HOURLY OVERLOAD RISK ────────────────────────────────────────────────
    hourly_data = (
        EnergyReading.objects
        .annotate(hour=ExtractHour('timestamp'))
        .values('hour')
        .annotate(
            avg_power=Avg('power'),
            max_power=Max('power'),
            reading_count=Count('energyreading_id'),
        )
        .order_by('hour')
    )

    hours_range = list(range(24))
    hourly_map = {row['hour']: row for row in hourly_data}
    chart_hourly_labels    = [f"{h:02d}:00" for h in hours_range]
    chart_hourly_avg_power = [round(hourly_map[h]['avg_power'], 2) if h in hourly_map else 0 for h in hours_range]
    chart_hourly_max_power = [round(hourly_map[h]['max_power'], 2) if h in hourly_map else 0 for h in hours_range]
    chart_hourly_count     = [hourly_map[h]['reading_count'] if h in hourly_map else 0 for h in hours_range]

    # ─── 3. ANOMALIES BY BUILDING TYPE ─────────────────────────────────────────
    anomaly_by_btype = (
        Anomaly.objects
        .values(btype_name=F('energy_reading__sensor__building__building_type__name'))
        .annotate(count=Count('anomaly_id'), avg_severity=Avg('severity'))
        .order_by('-count')
    )
    chart_btype_labels   = [r['btype_name'] for r in anomaly_by_btype]
    chart_btype_counts   = [r['count'] for r in anomaly_by_btype]
    chart_btype_severity = [round(r['avg_severity'], 2) for r in anomaly_by_btype]

    anomaly_by_type = (
        Anomaly.objects
        .values(atype=F('anomaly_type__name'))
        .annotate(count=Count('anomaly_id'))
        .order_by('-count')
    )
    chart_atype_labels = [r['atype'] for r in anomaly_by_type]
    chart_atype_counts = [r['count'] for r in anomaly_by_type]

    # ─── 4. POWER FACTOR vs FAULT OCCURRENCE ────────────────────────────────────
    pf_buckets = [
        (0.0,  0.70, 'Critical (<0.70)'),
        (0.70, 0.80, 'Poor (0.70–0.80)'),
        (0.80, 0.90, 'Moderate (0.80–0.90)'),
        (0.90, 0.95, 'Good (0.90–0.95)'),
        (0.95, 1.01, 'Excellent (>0.95)'),
    ]

    anomaly_reading_ids = set(Anomaly.objects.values_list('energy_reading_id', flat=True))

    pf_labels, pf_fault_counts, pf_total_counts, pf_fault_rates = [], [], [], []
    for lo, hi, label in pf_buckets:
        total  = EnergyReading.objects.filter(power_factor__gte=lo, power_factor__lt=hi).count()
        faults = EnergyReading.objects.filter(
            power_factor__gte=lo, power_factor__lt=hi,
            energyreading_id__in=anomaly_reading_ids
        ).count()
        pf_labels.append(label)
        pf_fault_counts.append(faults)
        pf_total_counts.append(total)
        pf_fault_rates.append(round((faults / total * 100) if total > 0 else 0, 2))

    # ─── 5. ALERT EFFECTIVENESS ─────────────────────────────────────────────────
    resolved_severity = (
        Anomaly.objects.filter(alert__status='Resolved').aggregate(avg=Avg('severity'))['avg'] or 0
    )
    active_severity = (
        Anomaly.objects.filter(alert__status='Active').aggregate(avg=Avg('severity'))['avg'] or 0
    )
    resolved_power = (
        EnergyReading.objects.filter(anomaly__alert__status='Resolved').aggregate(avg=Avg('power'))['avg'] or 0
    )
    active_power = (
        EnergyReading.objects.filter(anomaly__alert__status='Active').aggregate(avg=Avg('power'))['avg'] or 0
    )

    alert_effectiveness = {
        'resolved_severity': round(resolved_severity, 2),
        'active_severity':   round(active_severity, 2),
        'resolved_power':    round(resolved_power, 2),
        'active_power':      round(active_power, 2),
        'resolution_rate':   round((resolved_alerts / total_alerts * 100) if total_alerts > 0 else 0, 1),
    }

    # ─── 6. ENERGY TREND ────────────────────────────────────────────────────────
    trend_readings = (
        EnergyReading.objects
        .order_by('timestamp')
        .values('timestamp', 'power', 'power_factor', 'voltage', 'current')[:100]
    )
    chart_trend_labels  = [r['timestamp'].strftime('%H:%M') for r in trend_readings]
    chart_trend_power   = [round(r['power'], 2) for r in trend_readings]
    chart_trend_pf      = [round(r['power_factor'], 4) for r in trend_readings]
    chart_trend_voltage = [round(r['voltage'], 2) for r in trend_readings]
    chart_trend_current = [round(r['current'], 2) for r in trend_readings]

    # ─── 7. SENSOR STATUS ────────────────────────────────────────────────────────
    sensor_status = Sensor.objects.values('status').annotate(count=Count('sensor_id'))
    chart_sensor_status_labels = [r['status'] for r in sensor_status]
    chart_sensor_status_counts = [r['count'] for r in sensor_status]

    # ─── 8. ANOMALY SEVERITY DISTRIBUTION ───────────────────────────────────────
    severity_dist = (
        Anomaly.objects.values('severity').annotate(count=Count('anomaly_id')).order_by('severity')
    )
    chart_severity_labels = [f"Level {r['severity']}" for r in severity_dist]
    chart_severity_counts = [r['count'] for r in severity_dist]

    # ─── 9. RECENT ANOMALIES TABLE ───────────────────────────────────────────────
    recent_anomalies = (
        Anomaly.objects
        .select_related('anomaly_type', 'energy_reading__sensor__building')
        .order_by('-timestamp')[:10]
    )

    # ─── 10. BUILDING ENERGY OVERVIEW ────────────────────────────────────────────
    building_energy = []
    for building in Building.objects.select_related('building_type').all():
        sensors = Sensor.objects.filter(building=building)
        reading_data = EnergyReading.objects.filter(sensor__in=sensors).aggregate(
            avg_power=Avg('power'),
            max_power=Max('power'),
            avg_pf=Avg('power_factor'),
            count=Count('energyreading_id'),
        )
        anomaly_count = Anomaly.objects.filter(energy_reading__sensor__building=building).count()
        building_energy.append({
            'name':          building.name,
            'type':          building.building_type.name,
            'location':      building.location,
            'avg_power':     round(reading_data['avg_power'] or 0, 2),
            'max_power':     round(reading_data['max_power'] or 0, 2),
            'avg_pf':        round(reading_data['avg_pf'] or 0, 3),
            'reading_count': reading_data['count'],
            'anomaly_count': anomaly_count,
        })

    chart_building_labels    = [b['name'] for b in building_energy]
    chart_building_avg_pwr   = [b['avg_power'] for b in building_energy]
    chart_building_max_pwr   = [b['max_power'] for b in building_energy]
    chart_building_anomalies = [b['anomaly_count'] for b in building_energy]

    context = {
        'kpi': {
            'total_buildings':  total_buildings,
            'total_sensors':    total_sensors,
            'total_appliances': total_appliances,
            'total_readings':   total_readings,
            'total_anomalies':  total_anomalies,
            'total_alerts':     total_alerts,
            'active_alerts':    active_alerts,
            'resolved_alerts':  resolved_alerts,
            'avg_power':        round(avg_power, 2),
            'avg_power_factor': round(avg_power_factor, 3),
            'max_power':        round(max_power, 2),
        },
        'chart_spike_labels':         json.dumps(chart_spike_labels),
        'chart_spike_counts':         json.dumps(chart_spike_counts),
        'chart_spike_max_power':      json.dumps(chart_spike_max_power),

        'chart_hourly_labels':        json.dumps(chart_hourly_labels),
        'chart_hourly_avg_power':     json.dumps(chart_hourly_avg_power),
        'chart_hourly_max_power':     json.dumps(chart_hourly_max_power),
        'chart_hourly_count':         json.dumps(chart_hourly_count),

        'chart_btype_labels':         json.dumps(chart_btype_labels),
        'chart_btype_counts':         json.dumps(chart_btype_counts),
        'chart_btype_severity':       json.dumps(chart_btype_severity),

        'chart_atype_labels':         json.dumps(chart_atype_labels),
        'chart_atype_counts':         json.dumps(chart_atype_counts),

        'pf_labels':                  json.dumps(pf_labels),
        'pf_fault_counts':            json.dumps(pf_fault_counts),
        'pf_total_counts':            json.dumps(pf_total_counts),
        'pf_fault_rates':             json.dumps(pf_fault_rates),

        'alert_effectiveness':        alert_effectiveness,

        'chart_trend_labels':         json.dumps(chart_trend_labels),
        'chart_trend_power':          json.dumps(chart_trend_power),
        'chart_trend_pf':             json.dumps(chart_trend_pf),
        'chart_trend_voltage':        json.dumps(chart_trend_voltage),
        'chart_trend_current':        json.dumps(chart_trend_current),

        'chart_sensor_status_labels': json.dumps(chart_sensor_status_labels),
        'chart_sensor_status_counts': json.dumps(chart_sensor_status_counts),

        'chart_severity_labels':      json.dumps(chart_severity_labels),
        'chart_severity_counts':      json.dumps(chart_severity_counts),

        'chart_building_labels':      json.dumps(chart_building_labels),
        'chart_building_avg_pwr':     json.dumps(chart_building_avg_pwr),
        'chart_building_max_pwr':     json.dumps(chart_building_max_pwr),
        'chart_building_anomalies':   json.dumps(chart_building_anomalies),

        'recent_anomalies': recent_anomalies,
        'building_energy':  building_energy,
        'spikes_table':     spikes_per_building_sorted,
    }

    return render(request, 'smartguard/analytics.html', context)
