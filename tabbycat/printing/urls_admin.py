from django.urls import path

from . import views

urlpatterns = [

    # Traditional sheets
    path('round/<int:round_seq>/scoresheets/',
        views.AdminPrintScoresheetsView.as_view(),
        name='printing-scoresheets'),
    path('round/<int:round_seq>/feedback/',
        views.AdminPrintFeedbackFormsView.as_view(),
        name='printing-feedback'),

    # Private URL distribution
    path('urls_sheets/',
        views.PrintableRandomisedURLs.as_view(),
        name='printing-urls'),

    # WADL sheets
    path('round/<int:round_seq>/master_sheets/list/',
        views.MasterSheetsListView.as_view(),
        name='printing-master-sheets-list'),
    path('round/<int:round_seq>/master_sheets/venue_category/<int:venue_category_id>/',
        views.MasterSheetsView.as_view(),
        name='printing-master-sheets-view'),
    path('round/<int:round_seq>/room_sheets_view/venue_category/<int:venue_category_id>/',
        views.RoomSheetsView.as_view(),
        name='printing-room-sheets-view'),


]
