from django.urls import include, path
from . import views

urlpatterns = [
    path('user', views.OwnUserView.as_view()),
	path('user/token', views.UserTokenView.as_view()),
	path('user/endorsements', views.UserContentEndorsementListView.as_view()),
    path('users/<int:user_id>', views.UserView.as_view()),
    path('endorsement', views.ContentEndorsementView.as_view()),
    path('endorsements', views.ContentEndorsementListView.as_view()),
    path('endorsements/<int:endorsement_id>', views.ContentEndorsementView.as_view()),
    path('source', views.SourceView.as_view()),
    path('sources', views.SourceListView.as_view()),
]