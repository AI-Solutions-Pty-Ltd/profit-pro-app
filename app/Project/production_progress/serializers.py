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

    plant_type_id = serializers.IntegerField(required=False, allow_null=True)
    resource_id = serializers.IntegerField(required=False, allow_null=True)
    plant_name = serializers.CharField(required=True)

    class Meta:
        model = DailyPlantUsage
        fields = [
            "id",
            "plant_type_id",
            "resource_id",
            "plant_name",
            "number",
            "hours",
            "quantity",
        ]


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
            "hours_on_activity",
            "labour_details",
            "plant_usage",
        ]

    @transaction.atomic
    def create(self, validated_data):
        plan_id = validated_data.pop("production_plan_id")
        labour_details = validated_data.pop("labour_details")
        plant_usage_data = validated_data.pop("plant_usage", [])
        report = validated_data.get("report")
        project_id = report.project_id if report else None

        entry = DailyActivityEntry.objects.create(
            production_plan_id=plan_id, **validated_data
        )

        # Handle Labour (Skilled, Semi-Skilled, General)
        if project_id:
            self._handle_labour_usage(entry, plan_id, project_id, labour_details)

        # Handle Plants
        self._handle_plant_usage(entry, plan_id, plant_usage_data)

        return entry

    @transaction.atomic
    def update(self, instance, validated_data):
        plan_id = validated_data.pop("production_plan_id", instance.production_plan_id)
        labour_details = validated_data.pop("labour_details", None)
        plant_usage_data = validated_data.pop("plant_usage", None)
        project_id = instance.report.project_id

        instance.quantity = validated_data.get("quantity", instance.quantity)
        instance.hours_on_activity = validated_data.get(
            "hours_on_activity", instance.hours_on_activity
        )
        instance.save()

        if labour_details is not None:
            instance.labour_usage.all().delete()
            self._handle_labour_usage(instance, plan_id, project_id, labour_details)

        if plant_usage_data is not None:
            instance.plant_usage.all().delete()
            self._handle_plant_usage(instance, plan_id, plant_usage_data)

        return instance

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
        """Processes plant usage entries, linking to specific plant types from specification."""
        from app.Estimator.models import ProjectPlantCost

        for plant_data in plant_usage_data:
            plant_type_id = plant_data.get("plant_type_id")
            resource_id = plant_data.get("resource_id")
            name = plant_data.get("plant_name")

            if not plant_type_id and not resource_id and not name:
                continue

            plant_type = None
            if plant_type_id:
                plant_type = ProjectPlantCost.objects.filter(id=plant_type_id).first()

            resource = None
            if not plant_type and resource_id:
                resource = ProductionResource.objects.filter(
                    id=resource_id, production_plan_id=plan_id, resource_type="PLANT"
                ).first()

            if not plant_type and not resource and name:
                # Fallback to finding by name in project plant costs
                plant_type = ProjectPlantCost.objects.filter(
                    project_id=entry.report.project_id, name=name
                ).first()

            # Create usage record if we have either a spec plant type or a legacy resource
            if plant_type or resource:
                DailyPlantUsage.objects.create(
                    entry=entry,
                    plant_type=plant_type,
                    resource=resource,
                    number=plant_data.get("number", 1) or 1,
                    hours=plant_data.get("hours", 0) or 0,
                    quantity=plant_data.get("quantity", 0) or 0,
                )


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
            serializer = DailyLogEntrySerializer(data=entry_data)
            if serializer.is_valid(raise_exception=True):
                serializer.save(report=report)
