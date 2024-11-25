from django.urls import path, include

from Pscraper import views

urlpatterns = [
    path('', views.results, name='login'),
    path('start-scraping/', views.start_scraping, name='start_scraping'),

    # path('get_progress_data/', views.get_progress_data, name='get_progress_data'),
    path('results/', views.results, name='results'),
    path('resultsbycompany/', views.resultsbycompany, name='resultsbycompany'),
    # path('get_company_members/', views.get_company_members, name='get_company_members'),
    # path('delete_company/', views.delete_company, name='delete_company'),
    path('index/', views.index, name='index'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.login_view, name='logout'),

    # path('settings/', views.settings, name='settings'),
    path('history/', views.history, name='history'),
    # path('update_end_time/', views.update_end_time, name='update_end_time'),
    path('delete_session/', views.delete_session, name='delete_session'),
    path('register/', views.register_view, name='register'),

    path('export/', views.export, name='export')]
