from django.urls import path
from . import views

app_name = 'docs_view'

urlpatterns = [
    path('doclist/', views.doc_list_view, name='doc_list'),
    path('doc/<path:doc_path>/', views.doc_view, name='doc_view'),
    path('api/docs/', views.get_docs_tree, name='get_docs_tree'),
    path('api/doc/<path:doc_path>/', views.get_doc_content, name='get_doc_content'),
] 