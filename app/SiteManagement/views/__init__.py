"""Site Management Views."""

from .daily_diary_views import (
    DailyDiaryCreateView,
    DailyDiaryDeleteView,
    DailyDiaryListView,
    DailyDiaryUpdateView,
)
from .delay_log_views import (
    DelayLogCreateView,
    DelayLogDeleteView,
    DelayLogListView,
    DelayLogUpdateView,
)
from .delivery_tracker_views import (
    DeliveryTrackerCreateView,
    DeliveryTrackerDeleteView,
    DeliveryTrackerListView,
    DeliveryTrackerUpdateView,
)
from .labour_log_views import (
    LabourLogCreateView,
    LabourLogDeleteView,
    LabourLogListView,
    LabourLogUpdateView,
)
from .management_views import SiteManagementView
from .materials_log_views import (
    MaterialsLogCreateView,
    MaterialsLogDeleteView,
    MaterialsLogListView,
    MaterialsLogUpdateView,
)
from .offsite_log_views import (
    OffsiteLogCreateView,
    OffsiteLogDeleteView,
    OffsiteLogListView,
    OffsiteLogUpdateView,
)
from .photo_log_views import (
    PhotoLogCreateView,
    PhotoLogDeleteView,
    PhotoLogListView,
    PhotoLogUpdateView,
)
from .plant_equipment_views import (
    PlantEquipmentCreateView,
    PlantEquipmentDeleteView,
    PlantEquipmentListView,
    PlantEquipmentUpdateView,
)
from .procurement_tracker_views import (
    ProcurementTrackerCreateView,
    ProcurementTrackerDeleteView,
    ProcurementTrackerListView,
    ProcurementTrackerUpdateView,
)
from .productivity_log_views import (
    ProductivityLogCreateView,
    ProductivityLogDeleteView,
    ProductivityLogListView,
    ProductivityLogUpdateView,
)
from .progress_tracker_views import (
    ProgressTrackerCreateView,
    ProgressTrackerDeleteView,
    ProgressTrackerListView,
    ProgressTrackerUpdateView,
)
from .quality_control_views import (
    QualityControlCreateView,
    QualityControlDeleteView,
    QualityControlListView,
    QualityControlUpdateView,
)
from .safety_observation_views import (
    SafetyObservationCreateView,
    SafetyObservationDeleteView,
    SafetyObservationListView,
    SafetyObservationUpdateView,
)
from .snag_list_views import (
    SnagListCreateView,
    SnagListDeleteView,
    SnagListListView,
    SnagListUpdateView,
)
from .subcontractor_log_views import (
    SubcontractorLogCreateView,
    SubcontractorLogDeleteView,
    SubcontractorLogListView,
    SubcontractorLogUpdateView,
)

__all__ = [
    "SiteManagementView",
    "MaterialsLogListView",
    "MaterialsLogCreateView",
    "MaterialsLogUpdateView",
    "MaterialsLogDeleteView",
    "DailyDiaryListView",
    "DailyDiaryCreateView",
    "DailyDiaryUpdateView",
    "DailyDiaryDeleteView",
    "ProductivityLogListView",
    "ProductivityLogCreateView",
    "ProductivityLogUpdateView",
    "ProductivityLogDeleteView",
    "SubcontractorLogListView",
    "SubcontractorLogCreateView",
    "SubcontractorLogUpdateView",
    "SubcontractorLogDeleteView",
    "SnagListListView",
    "SnagListCreateView",
    "SnagListUpdateView",
    "SnagListDeleteView",
    "ProgressTrackerListView",
    "ProgressTrackerCreateView",
    "ProgressTrackerUpdateView",
    "ProgressTrackerDeleteView",
    "DelayLogListView",
    "DelayLogCreateView",
    "DelayLogUpdateView",
    "DelayLogDeleteView",
    "PhotoLogListView",
    "PhotoLogCreateView",
    "PhotoLogUpdateView",
    "PhotoLogDeleteView",
    "ProcurementTrackerListView",
    "ProcurementTrackerCreateView",
    "ProcurementTrackerUpdateView",
    "ProcurementTrackerDeleteView",
    "DeliveryTrackerListView",
    "DeliveryTrackerCreateView",
    "DeliveryTrackerUpdateView",
    "DeliveryTrackerDeleteView",
    "PlantEquipmentListView",
    "PlantEquipmentCreateView",
    "PlantEquipmentUpdateView",
    "PlantEquipmentDeleteView",
    "QualityControlListView",
    "QualityControlCreateView",
    "QualityControlUpdateView",
    "QualityControlDeleteView",
    "LabourLogListView",
    "LabourLogCreateView",
    "LabourLogUpdateView",
    "LabourLogDeleteView",
    "OffsiteLogListView",
    "OffsiteLogCreateView",
    "OffsiteLogUpdateView",
    "OffsiteLogDeleteView",
    "SafetyObservationListView",
    "SafetyObservationCreateView",
    "SafetyObservationUpdateView",
    "SafetyObservationDeleteView",
]
