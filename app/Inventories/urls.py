from django.urls import path

import app.Inventories.views
import app.Inventories.views_inventories

app_name = "inventories"

urlpatterns = [
    path(
        "warehouse/list/",
        app.Inventories.views_inventories.WarehouseListView.as_view(),
        name="warehouse_list_view",
    ),
    path(
        "inventory/list/",
        app.Inventories.views_inventories.InventoryListView.as_view(),
        name="inventory_list_view",
    ),
    path(
        "inventory/transaction/list/",
        app.Inventories.views_inventories.InventoryTransactionListView.as_view(),
        name="inventory_tx_list_view",
    ),
    path(
        "inventory/create/",
        app.Inventories.views_inventories.InventoryCreateView.as_view(),
        name="inventory_create_view",
    ),
    path(
        "inventory/order/",
        app.Inventories.views.OrderPlaceView.as_view(),
        name="order_place_view",
    ),
    path(
        "inventory/order/placed/",
        app.Inventories.views.OrderListView.as_view(),
        name="order_list_view",
    ),
    path(
        "inventory/order/detailed/",
        app.Inventories.views.OrderCompositionListView.as_view(),
        name="order_composition_list_view",
    ),
    path(
        "inventory/order/deliveries/",
        app.Inventories.views.OrderDeliveryListView.as_view(),
        name="order_delivery_list_view",
    ),
    path(
        "inventory/order/delivery_note/<int:id>/",
        app.Inventories.views.DeliveryNoteFileServeView.as_view(),
        name="order_delivery_note_view",
    ),
    path(
        "inventory/order/quote/<int:id>/",
        app.Inventories.views.QuoteFileServeView.as_view(),
        name="order_quote_view",
    ),
    path(
        "inventory/order/composition/<int:order>/",
        app.Inventories.views.OrderDetailView.as_view(),
        name="order_composition_view",
    ),
    path(
        "inventory/order/update/<int:order>/",
        app.Inventories.views.OrderUpdateView.as_view(),
        name="order_update_view",
    ),
    # storeman
    path(
        "inventory/order/receive/",
        app.Inventories.views.OrderReceiveView.as_view(),
        name="order_receive_view",
    ),
    path(
        "inventory/order/receive/<int:order>/",
        app.Inventories.views.OrderReceiveView.as_view(),
        name="order_receive_view",
    ),
]
