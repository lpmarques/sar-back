# Simulador Agroflorestal Regenera (SAR)
# Copyright (C) 2026  Lucas Marques and Regenera Mata Atlântica

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses>.

from django.urls import include, path
from rest_framework.exceptions import server_error
from . import views

handler500 = server_error
urlpatterns = [
    path('user', views.OwnUserView.as_view()),
	path('user/token', views.UserTokenView.as_view()),
	path('user/endorsements', views.UserContentEndorsementListView.as_view()),
    path('users', views.UserView.as_view()),
    path('users/<int:user_id>', views.UserView.as_view()),
    path('contents', views.ContentPreviewListView().as_view()),
    path('contents/<int:content_id>', views.ContentPreviewView().as_view()),
    path('endorsements', views.ContentEndorsementListView.as_view()),
    path('endorsements/<int:endorsement_id>', views.ContentEndorsementView.as_view()),
    path('sources', views.SourceListView.as_view()),
    path('sources/<int:source_id>', views.SourceView.as_view()),
    path('source-types', views.SourceTypeListView.as_view()),
    path('source-types/<int:type_id>/subtypes', views.SourceTypeListView.as_view()),
]