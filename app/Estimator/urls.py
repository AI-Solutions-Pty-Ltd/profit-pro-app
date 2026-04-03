from django.urls import path

from . import views

app_name = "estimator"

urlpatterns = [
    path("project/<int:project_pk>/", views.DashboardView.as_view(), name="dashboard"),
    path(
        "project/<int:project_pk>/assumptions/",
        views.ProjectAssumptionsView.as_view(),
        name="project_assumptions",
    ),
    path(
        "project/<int:project_pk>/baseline/",
        views.BaselineBoqView.as_view(),
        name="baseline",
    ),
    path(
        "project/<int:project_pk>/sync/", views.SyncBoqView.as_view(), name="sync_boq"
    ),
    path(
        "project/<int:project_pk>/initialize/",
        views.InitializeEstimatorView.as_view(),
        name="initialize_estimator",
    ),
    # Material Specs (simple definition)
    path(
        "project/<int:project_pk>/material-specs/",
        views.MaterialSpecListView.as_view(),
        name="material_specs",
    ),
    path(
        "project/<int:project_pk>/material-specs/upload/",
        views.MaterialSpecUploadView.as_view(),
        name="material_spec_upload",
    ),
    path(
        "project/<int:project_pk>/material-specs/download-template/",
        views.DownloadMaterialSpecTemplateView.as_view(),
        name="download_material_spec_template",
    ),
    # Material Estimator (calculator)
    path(
        "project/<int:project_pk>/specifications/",
        views.SpecificationListView.as_view(),
        name="specifications",
    ),
    # Material Costs
    path(
        "project/<int:project_pk>/materials/",
        views.MaterialsListView.as_view(),
        name="materials",
    ),
    path(
        "project/<int:project_pk>/materials/upload/",
        views.MaterialCostUploadView.as_view(),
        name="material_cost_upload",
    ),
    path(
        "project/<int:project_pk>/materials/download-template/",
        views.DownloadMaterialCostTemplateView.as_view(),
        name="download_material_cost_template",
    ),
    # Labour Specs (simple definition)
    path(
        "project/<int:project_pk>/labour-spec-defs/",
        views.LabourSpecDefListView.as_view(),
        name="labour_spec_defs",
    ),
    path(
        "project/<int:project_pk>/labour-spec-defs/upload/",
        views.LabourSpecUploadView.as_view(),
        name="labour_spec_upload",
    ),
    path(
        "project/<int:project_pk>/labour-spec-defs/download-template/",
        views.DownloadLabourSpecTemplateView.as_view(),
        name="download_labour_spec_template",
    ),
    # Labour Estimator (calculator — previously "Labour Specs")
    path(
        "project/<int:project_pk>/labour-specs/",
        views.LabourSpecificationListView.as_view(),
        name="labour_specs",
    ),
    # Labour Costs
    path(
        "project/<int:project_pk>/labour-costs/",
        views.LabourCostListView.as_view(),
        name="labour_costs",
    ),
    path(
        "project/<int:project_pk>/labour-costs/upload/",
        views.LabourCostUploadView.as_view(),
        name="labour_cost_upload",
    ),
    path(
        "project/<int:project_pk>/labour-costs/download-template/",
        views.DownloadLabourCostTemplateView.as_view(),
        name="download_labour_cost_template",
    ),
    # Trade Codes
    path(
        "project/<int:project_pk>/trade-codes/",
        views.TradeCodeListView.as_view(),
        name="trade_codes",
    ),
    path(
        "project/<int:project_pk>/trade-codes/upload/",
        views.TradeCodeUploadView.as_view(),
        name="trade_code_upload",
    ),
    path(
        "project/<int:project_pk>/trade-codes/download-template/",
        views.DownloadTradeCodeTemplateView.as_view(),
        name="download_trade_code_template",
    ),
    path(
        "project/<int:project_pk>/import/",
        views.ExcelImportView.as_view(),
        name="import_excel",
    ),
    # System specs
    path(
        "project/<int:project_pk>/system-specs/",
        views.SystemMaterialSpecListView.as_view(),
        name="system_specs",
    ),
    path(
        "project/<int:project_pk>/system-specs/upload/",
        views.SystemSpecUploadView.as_view(),
        name="system_spec_upload",
    ),
    path(
        "project/<int:project_pk>/system-specs/download-template/",
        views.DownloadSystemSpecTemplateView.as_view(),
        name="download_system_spec_template",
    ),
    # AJAX
    path(
        "project/<int:project_pk>/api/boq-item/<int:pk>/update/",
        views.UpdateBoqItemView.as_view(),
        name="update_boq_item",
    ),
    path(
        "project/<int:project_pk>/api/material/<int:pk>/update/",
        views.UpdateMaterialView.as_view(),
        name="update_material",
    ),
    path(
        "project/<int:project_pk>/api/spec-component/<int:pk>/update/",
        views.UpdateSpecComponentView.as_view(),
        name="update_spec_component",
    ),
    path(
        "project/<int:project_pk>/api/labour-spec/<int:pk>/update/",
        views.UpdateLabourSpecView.as_view(),
        name="update_labour_spec",
    ),
    path(
        "project/<int:project_pk>/api/labour-crew/<int:pk>/update/",
        views.UpdateLabourCrewView.as_view(),
        name="update_labour_crew",
    ),
    path(
        "project/<int:project_pk>/api/system-spec-component/<int:pk>/update/",
        views.UpdateSystemSpecComponentView.as_view(),
        name="update_system_spec_component",
    ),
    path(
        "project/<int:project_pk>/api/bulk-markup/",
        views.BulkMarkupUpdateView.as_view(),
        name="bulk_markup_update",
    ),
    # Reports
    path(
        "project/<int:project_pk>/reports/",
        views.ReportsIndexView.as_view(),
        name="reports_index",
    ),
    path(
        "project/<int:project_pk>/reports/baseline-assessment/",
        views.PricedBoqReportView.as_view(),
        kwargs={"report_type": "baseline_assessment"},
        name="report_baseline_assessment",
    ),
    path(
        "project/<int:project_pk>/reports/progress-assessment/",
        views.PricedBoqReportView.as_view(),
        kwargs={"report_type": "progress_assessment"},
        name="report_progress_assessment",
    ),
    path(
        "project/<int:project_pk>/reports/forecast-assessment/",
        views.PricedBoqReportView.as_view(),
        kwargs={"report_type": "forecast_assessment"},
        name="report_forecast_assessment",
    ),
    path(
        "project/<int:project_pk>/reports/key-rates-assessment/",
        views.PricedBoqReportView.as_view(),
        kwargs={"report_type": "key_rates_assessment"},
        name="report_key_rates_assessment",
    ),
    path(
        "project/<int:project_pk>/reports/material-list-baseline/",
        views.MaterialListReportView.as_view(),
        kwargs={"variant": "baseline"},
        name="report_material_list_baseline",
    ),
    path(
        "project/<int:project_pk>/reports/material-list-progress/",
        views.MaterialListReportView.as_view(),
        kwargs={"variant": "progress"},
        name="report_material_list_progress",
    ),
    path(
        "project/<int:project_pk>/reports/material-list-forecast/",
        views.MaterialListReportView.as_view(),
        kwargs={"variant": "forecast"},
        name="report_material_list_forecast",
    ),
    path(
        "project/<int:project_pk>/reports/labour-list-baseline/",
        views.LabourListReportView.as_view(),
        kwargs={"variant": "baseline"},
        name="report_labour_list_baseline",
    ),
    path(
        "project/<int:project_pk>/reports/labour-list-progress/",
        views.LabourListReportView.as_view(),
        kwargs={"variant": "progress"},
        name="report_labour_list_progress",
    ),
    path(
        "project/<int:project_pk>/reports/labour-list-forecast/",
        views.LabourListReportView.as_view(),
        kwargs={"variant": "forecast"},
        name="report_labour_list_forecast",
    ),
    # Baseline Estimator (contract-rate) reports
    path(
        "project/<int:project_pk>/reports/material-list-baseline/contract/",
        views.MaterialListReportView.as_view(),
        kwargs={"variant": "baseline", "rate_type": "contract"},
        name="report_material_list_baseline_contract",
    ),
    path(
        "project/<int:project_pk>/reports/material-list-progress/contract/",
        views.MaterialListReportView.as_view(),
        kwargs={"variant": "progress", "rate_type": "contract"},
        name="report_material_list_progress_contract",
    ),
    path(
        "project/<int:project_pk>/reports/material-list-forecast/contract/",
        views.MaterialListReportView.as_view(),
        kwargs={"variant": "forecast", "rate_type": "contract"},
        name="report_material_list_forecast_contract",
    ),
    path(
        "project/<int:project_pk>/reports/labour-list-baseline/contract/",
        views.LabourListReportView.as_view(),
        kwargs={"variant": "baseline", "rate_type": "contract"},
        name="report_labour_list_baseline_contract",
    ),
    path(
        "project/<int:project_pk>/reports/labour-list-progress/contract/",
        views.LabourListReportView.as_view(),
        kwargs={"variant": "progress", "rate_type": "contract"},
        name="report_labour_list_progress_contract",
    ),
    path(
        "project/<int:project_pk>/reports/labour-list-forecast/contract/",
        views.LabourListReportView.as_view(),
        kwargs={"variant": "forecast", "rate_type": "contract"},
        name="report_labour_list_forecast_contract",
    ),
    # ── System Library ────────────────────────────────────────────
    path("system/", views.SystemTradeCodeListView.as_view(), name="sys_trade_codes"),
    # System Trade Codes
    path(
        "system/trade-codes/",
        views.SystemTradeCodeListView.as_view(),
        name="sys_trade_codes",
    ),
    path(
        "system/trade-codes/upload/",
        views.SystemTradeCodeUploadView.as_view(),
        name="sys_trade_code_upload",
    ),
    path(
        "system/trade-codes/download-template/",
        views.DownloadSystemTradeCodeTemplateView.as_view(),
        name="sys_download_trade_code_template",
    ),
    # System Materials
    path(
        "system/materials/",
        views.SystemMaterialListView.as_view(),
        name="sys_materials",
    ),
    path(
        "system/materials/upload/",
        views.SystemMaterialUploadView.as_view(),
        name="sys_material_upload",
    ),
    path(
        "system/materials/download-template/",
        views.DownloadSystemMaterialTemplateView.as_view(),
        name="sys_download_material_template",
    ),
    # System Material Specs
    path(
        "system/material-specs/",
        views.SysMaterialSpecListView.as_view(),
        name="sys_material_specs",
    ),
    path(
        "system/material-specs/upload/",
        views.SystemMaterialSpecUploadView.as_view(),
        name="sys_material_spec_upload",
    ),
    path(
        "system/material-specs/download-template/",
        views.DownloadSystemMaterialSpecTemplateView.as_view(),
        name="sys_download_material_spec_template",
    ),
    # System Labour Crews
    path(
        "system/labour-crews/",
        views.SystemLabourCrewListView.as_view(),
        name="sys_labour_crews",
    ),
    path(
        "system/labour-crews/upload/",
        views.SystemLabourCrewUploadView.as_view(),
        name="sys_labour_crew_upload",
    ),
    path(
        "system/labour-crews/download-template/",
        views.DownloadSystemLabourCrewTemplateView.as_view(),
        name="sys_download_labour_crew_template",
    ),
    # System Labour Specs
    path(
        "system/labour-specs/",
        views.SystemLabourSpecListView.as_view(),
        name="sys_labour_specs",
    ),
    path(
        "system/labour-specs/upload/",
        views.SystemLabourSpecUploadView.as_view(),
        name="sys_labour_spec_upload",
    ),
    path(
        "system/labour-specs/download-template/",
        views.DownloadSystemLabourSpecTemplateView.as_view(),
        name="sys_download_labour_spec_template",
    ),
    # System AJAX
    path(
        "system/api/material/<int:pk>/update/",
        views.UpdateSystemMaterialView.as_view(),
        name="sys_update_material",
    ),
    path(
        "system/api/spec-component/<int:pk>/update/",
        views.UpdateSysSpecComponentView.as_view(),
        name="sys_update_spec_component",
    ),
    path(
        "system/api/labour-crew/<int:pk>/update/",
        views.UpdateSystemLabourCrewView.as_view(),
        name="sys_update_labour_crew",
    ),
    path(
        "system/api/labour-spec/<int:pk>/update/",
        views.UpdateSystemLabourSpecView.as_view(),
        name="sys_update_labour_spec",
    ),
]
