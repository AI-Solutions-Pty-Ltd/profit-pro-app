def repair_production_hierarchy():
    """
    Backfills is_leaf and node_type for existing ProductionPlan records.
    """
    from django.db.models import Q

    from app.Project.production_progress.production_models import ProductionPlan

    print("Starting hierarchy repair...")

    # 1. Activities (Leaf nodes)
    # They have either a labour_activity or a plant_specification
    activities = ProductionPlan.objects.filter(
        Q(labour_activity__isnull=False) | Q(plant_specification__isnull=False)
    )
    count = activities.update(is_leaf=True, node_type="ACTIVITY")
    print(f"Updated {count} activities as leaf nodes.")

    # 2. Bills (Non-leaf structural nodes)
    # They have a bill_no but no specification
    bills = ProductionPlan.objects.filter(
        labour_activity__isnull=True, plant_specification__isnull=True, bill_no__gt=""
    ).exclude(bill_no="")
    count = bills.update(is_leaf=False, node_type="BILL")
    print(f"Updated {count} Bill headers.")

    # 3. Sections (Non-leaf structural nodes)
    # They have a section but no bill_no and no specification
    sections = ProductionPlan.objects.filter(
        labour_activity__isnull=True, plant_specification__isnull=True, section__gt=""
    ).filter(Q(bill_no="") | Q(bill_no__isnull=True))
    count = sections.update(is_leaf=False, node_type="SECTION")
    print(f"Updated {count} Section headers.")

    # 4. Trigger date synchronization for all top-level parents
    print("Synchronizing parent dates...")
    top_parents = ProductionPlan.objects.filter(node_type="SECTION", deleted=False)
    for section in top_parents:
        # Syncing from the bottom up is handled by our recursive method if we call it on the children
        # But here we want to trigger it once for the whole tree.
        # We'll trigger it on all Bills first, then Sections.
        bills = ProductionPlan.objects.filter(
            parent=section, node_type="BILL", deleted=False
        )
        for bill in bills:
            bill.sync_parent_dates()
        section.sync_parent_dates()

    print("Hierarchy repair complete.")


if __name__ == "__main__":
    import os

    import django

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings.local")
    django.setup()
    repair_production_hierarchy()
