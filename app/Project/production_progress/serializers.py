from django.db import transaction
from rest_framework import serializers

from .production_models import (
    DailyActivityEntry,
    DailyActivityReport,
    DailyLabourUsage,
    DailyPlantUsage,
    ProductionResource,
)


class DailyLogPlantUsageSerializer(serializers.ModelSerializer):
    """Serializer for individual plant usage in a daily log."""

    resource_id = serializers.IntegerField(required=False, allow_null=True)
    plant_name = serializers.CharField(required=True)

    class Meta:
        model = DailyPlantUsage
        fields = ["id", "resource_id", "plant_name", "number", "hours", "quantity"]


class DailyLogLabourUsageSerializer(serializers.ModelSerializer):
    """Serializer for labour category usage (Skilled, Semi-Skilled, General)."""

    category = serializers.CharField(write_only=True)

    class Meta:
        model = DailyLabourUsage
        fields = ["id", "category", "number", "hours"]


class DailyLogEntrySerializer(serializers.ModelSerializer):
    """Serializer for an activity entry in a daily log."""

    production_plan_id = serializers.IntegerField()
    labour_details = serializers.JSONField(
        write_only=True
    )  # Skilled, Semi-Skilled, General
    plant_usage = DailyLogPlantUsageSerializer(many=True, required=False)

    class Meta:
        model = DailyActivityEntry
        fields = [
            "id",
            "production_plan_id",
            "quantity",
            "labour_details",
            "plant_usage",
        ]


class DailyLogReportSerializer(serializers.ModelSerializer):
    """Top-level serializer for the Daily Activity Report."""

    project_id = serializers.IntegerField()
    entries = DailyLogEntrySerializer(many=True)

    class Meta:
        model = DailyActivityReport
        fields = ["id", "project_id", "date", "notes", "entries"]

    @transaction.atomic
    def create(self, validated_data):
        entries_data = validated_data.pop("entries")
        project_id = validated_data.pop("project_id")
        report = DailyActivityReport.objects.create(
            project_id=project_id, **validated_data
        )

        self._process_entries(report, project_id, entries_data)
        return report

    @transaction.atomic
    def update(self, instance, validated_data):
        entries_data = validated_data.pop("entries", None)
        project_id = validated_data.pop("project_id", instance.project_id)

        # Update report fields
        instance.date = validated_data.get("date", instance.date)
        instance.notes = validated_data.get("notes", instance.notes)
        instance.save()

        if entries_data is not None:
            # Simple sync: Clear and recreate entries
            # This is safer since the frontend doesn't track entry IDs
            instance.entries.all().delete()
            self._process_entries(instance, project_id, entries_data)

        return instance

    def _process_entries(self, report, project_id, entries_data):
        """Helper to create entries and associated usage from validated data."""
        for entry_data in entries_data:
            plan_id = entry_data.pop("production_plan_id")
            labour_details = entry_data.pop("labour_details")
            plant_usage_data = entry_data.pop("plant_usage", [])

            entry = DailyActivityEntry.objects.create(
                report=report,
                production_plan_id=plan_id,
                quantity=entry_data.get("quantity", 0),
                hours_on_activity=entry_data.get("hours_on_activity", 0),
            )

            # Handle Labour (Skilled, Semi-Skilled, General)
            self._handle_labour_usage(entry, plan_id, project_id, labour_details)

            # Handle Plants
            self._handle_plant_usage(entry, plan_id, plant_usage_data)

    def _handle_labour_usage(self, entry, plan_id, project_id, labour_details):
        """
        Maps Skilled, Semi-Skilled, and General to DailyLabourUsage.
        Creates ProductionResource if missing.
        """
        categories = ["Skilled", "Semi-Skilled", "General"]
        for cat in categories:
            data = labour_details.get(cat)
            if not data or (not data.get("number") and not data.get("hours")):
                continue

            # Find or create ProductionResource for this plan/category
            resource, _ = ProductionResource.objects.get_or_create(
                production_plan_id=plan_id,
                resource_type="LABOUR",
                name=cat,
                defaults={"rate": 0},  # Default rate 0 if created on the fly
            )

            DailyLabourUsage.objects.create(
                entry=entry,
                resource=resource,
                number=int(data.get("number", 1) or 1),
                hours=float(data.get("hours", 0) or 0),
            )

    def _handle_plant_usage(self, entry, plan_id, plant_usage_data):
        """Processes plant usage entries."""
        for plant_data in plant_usage_data:
            # Plant usage requires a name and hours
            name = plant_data.get("plant_name")
            if not name:
                continue

            # Find or create ProductionResource for this plant on this plan
            resource, _ = ProductionResource.objects.get_or_create(
                production_plan_id=plan_id,
                resource_type="PLANT",
                name=name,
                defaults={"rate": 0},
            )

            DailyPlantUsage.objects.create(
                entry=entry,
                resource=resource,
                number=plant_data.get("number", 1),
                hours=plant_data.get("hours", 0),
                quantity=plant_data.get("quantity", 0),
            )
