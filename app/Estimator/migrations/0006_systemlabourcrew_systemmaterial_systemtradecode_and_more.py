"""Rename 6 models to System* (state-only, tables unchanged via db_table)
and create 6 new Project* tables."""

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Project', '0046_alter_projectdocument_category'),
        ('estimator', '0005_boqitem_project_boqitem_source_line_item_and_more'),
    ]

    operations = [
        # ── Step 1: Rename old models → System* (state only) ──────────
        # RenameModel auto-updates all FK references across Django state.
        # No DB operations because the tables keep their original names
        # via db_table Meta option.
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.RenameModel('TradeCode', 'SystemTradeCode'),
                migrations.RenameModel('Material', 'SystemMaterial'),
                migrations.RenameModel('LabourCrew', 'SystemLabourCrew'),
            ],
            database_operations=[],
        ),
        # LabourSpecification depends on LabourCrew rename above
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.RenameModel('LabourSpecification', 'SystemLabourSpecification'),
            ],
            database_operations=[],
        ),
        # Specification depends on TradeCode rename above
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.RenameModel('Specification', 'SystemSpecification'),
            ],
            database_operations=[],
        ),
        # SpecificationComponent depends on Specification + Material renames
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.RenameModel('SpecificationComponent', 'SystemSpecificationComponent'),
            ],
            database_operations=[],
        ),

        # ── Step 2: Set db_table so Django knows the tables didn't move ──
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AlterModelTable('SystemTradeCode', 'estimator_tradecode'),
                migrations.AlterModelTable('SystemMaterial', 'estimator_material'),
                migrations.AlterModelTable('SystemLabourCrew', 'estimator_labourcrew'),
                migrations.AlterModelTable('SystemLabourSpecification', 'estimator_labourspecification'),
                migrations.AlterModelTable('SystemSpecification', 'estimator_specification'),
                migrations.AlterModelTable('SystemSpecificationComponent', 'estimator_specificationcomponent'),
            ],
            database_operations=[],
        ),

        # ── Step 3: Update verbose_names on renamed models ────────────
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AlterModelOptions(
                    name='SystemLabourCrew',
                    options={'verbose_name': 'System Labour Crew', 'ordering': ['crew_type']},
                ),
                migrations.AlterModelOptions(
                    name='SystemLabourSpecification',
                    options={'verbose_name': 'System Labour Specification', 'ordering': ['section', 'name']},
                ),
            ],
            database_operations=[],
        ),

        # ── Step 4: Update SystemMaterialSpecComponent FK target ──────
        # Was pointing to 'estimator.material', now should be 'estimator.systemmaterial'
        # RenameModel already updated the state reference, but we need to
        # update the related_name from 'system_spec_components' explicitly.
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AlterField(
                    model_name='SystemMaterialSpecComponent',
                    name='material',
                    field=models.ForeignKey(
                        blank=True, null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name='system_spec_components',
                        to='estimator.systemmaterial',
                    ),
                ),
            ],
            database_operations=[],
        ),

        # ── Step 5: Create Project* tables (real DB operations) ───────
        migrations.CreateModel(
            name='ProjectTradeCode',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('prefix', models.CharField(max_length=20)),
                ('trade_name', models.CharField(max_length=100)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='estimator_trade_codes', to='Project.project')),
                ('source', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='project_copies', to='estimator.systemtradecode')),
            ],
            options={
                'ordering': ['prefix'],
                'unique_together': {('project', 'prefix')},
            },
        ),
        migrations.CreateModel(
            name='ProjectMaterial',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('trade_name', models.CharField(blank=True, max_length=200)),
                ('material_code', models.CharField(max_length=100)),
                ('unit', models.CharField(blank=True, max_length=20)),
                ('market_rate', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('material_variety', models.CharField(blank=True, max_length=100)),
                ('market_spec', models.CharField(blank=True, max_length=100)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='estimator_materials', to='Project.project')),
                ('source', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='project_copies', to='estimator.systemmaterial')),
            ],
            options={
                'ordering': ['material_code'],
                'unique_together': {('project', 'material_code')},
            },
        ),
        migrations.CreateModel(
            name='ProjectLabourCrew',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('crew_type', models.CharField(max_length=100)),
                ('crew_size', models.IntegerField(default=0)),
                ('skilled', models.IntegerField(default=0)),
                ('semi_skilled', models.IntegerField(default=0)),
                ('general', models.IntegerField(default=0)),
                ('daily_production', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('skilled_rate', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('semi_skilled_rate', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('general_rate', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='estimator_labour_crews', to='Project.project')),
                ('source', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='project_copies', to='estimator.systemlabourcrew')),
            ],
            options={
                'verbose_name': 'Project Labour Crew',
                'ordering': ['crew_type'],
                'unique_together': {('project', 'crew_type')},
            },
        ),
        migrations.CreateModel(
            name='ProjectLabourSpecification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('section', models.CharField(blank=True, max_length=100)),
                ('trade_name', models.CharField(blank=True, max_length=200)),
                ('name', models.CharField(max_length=200)),
                ('unit', models.CharField(blank=True, max_length=20)),
                ('daily_production', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('team_mix', models.DecimalField(decimal_places=4, default=1, max_digits=6)),
                ('site_factor', models.DecimalField(decimal_places=4, default=1, max_digits=6)),
                ('tools_factor', models.DecimalField(decimal_places=4, default=1, max_digits=6)),
                ('leadership_factor', models.DecimalField(decimal_places=4, default=1, max_digits=6)),
                ('crew', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='labour_specs', to='estimator.projectlabourcrew')),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='estimator_labour_specs', to='Project.project')),
                ('source', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='project_copies', to='estimator.systemlabourspecification')),
            ],
            options={
                'verbose_name': 'Project Labour Specification',
                'ordering': ['section', 'name'],
                'unique_together': {('project', 'name')},
            },
        ),
        migrations.CreateModel(
            name='ProjectSpecification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('section', models.CharField(blank=True, max_length=100)),
                ('unit_label', models.CharField(default='m3', max_length=20)),
                ('name', models.CharField(max_length=100)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='estimator_specifications', to='Project.project')),
                ('source', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='project_specification_copies', to='estimator.systemmaterialspec')),
                ('trade_code', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='specifications', to='estimator.projecttradecode')),
            ],
            options={
                'ordering': ['section', 'name'],
                'unique_together': {('project', 'name')},
            },
        ),
        migrations.CreateModel(
            name='ProjectSpecificationComponent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('label', models.CharField(max_length=100)),
                ('qty_per_unit', models.DecimalField(decimal_places=4, default=0, max_digits=10)),
                ('sort_order', models.IntegerField(default=0)),
                ('material', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='spec_components', to='estimator.projectmaterial')),
                ('specification', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='spec_components', to='estimator.projectspecification')),
            ],
            options={
                'ordering': ['sort_order'],
            },
        ),
    ]
