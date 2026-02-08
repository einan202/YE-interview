from django.urls import path

from . import views

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('blog/<int:id>/', views.SingleBlogView.as_view(), name='single_blog'),
    path('author/<str:username>/', views.AuthorProfileView.as_view(), name='author_profile'),
    path('topic/<slug:slug>', views.CatagoryView.as_view(), name='catagory'),
    path('tag/<int:id>', views.TagView.as_view(), name='tag'),
    path('subscribe/', views.SubsCribe.as_view(), name='subscribe'),
    path('search/', views.SearchView.as_view(), name='search'),
    path('<int:id>/create-comment/', views.CommentView.as_view(), name='comment'),
    path('blog/<int:id>/like/', views.LikeToggleView.as_view(), name='like'),
    path('test/', views.test, name='test'),
]