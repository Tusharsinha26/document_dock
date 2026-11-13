import os
import uuid
from datetime import datetime, date, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.exceptions import PermissionDenied
from django.http import Http404, JsonResponse, HttpResponse

from .forms import DocumentForm, RegisterForm
from .db import (
    get_documents_collection,
    get_user_documents,
    get_document_by_id,
    delete_document_by_id,
    get_dashboard_metrics,
    seed_demo_documents,
    CATEGORY_METADATA,
    enrich_document,
    store_uploaded_file,
    get_stored_file
)


def landing(request):
    """
    Renders the editorial landing page for DocumentDock.
    """
    sample_items = [
        {
            'title': 'British Biometric Passport',
            'category': 'Identity & Travel',
            'expiry_human': 'Expires in 42 days',
            'status': 'Expiring Soon',
            'urgency_class': 'status-warning',
            'days': 42,
            'number': 'GBR-88429104'
        },
        {
            'title': 'Comprehensive Auto Insurance',
            'category': 'Vehicles & Transport',
            'expiry_human': 'Expires in 18 days',
            'status': 'Expiring Soon',
            'urgency_class': 'status-warning',
            'days': 18,
            'number': 'ALZ-MOT-773019'
        },
        {
            'title': 'Residential Tenancy Agreement',
            'category': 'Property & Housing',
            'expiry_human': 'Valid for 215 days',
            'status': 'Active',
            'urgency_class': 'status-active',
            'days': 215,
            'number': 'TNC-2024-LON'
        },
        {
            'title': 'Global Platinum Health Cover',
            'category': 'Insurance & Health',
            'expiry_human': 'Valid for 160 days',
            'status': 'Active',
            'urgency_class': 'status-active',
            'days': 160,
            'number': 'BUP-INT-99214'
        }
    ]

    context = {
        'sample_items': sample_items,
        'categories': CATEGORY_METADATA,
        'is_authenticated': request.user.is_authenticated,
    }
    return render(request, 'landing.html', context)


@login_required
def dashboard(request):
    """
    Main authenticated dashboard overview.
    """
    # Ensure sample data exists for demonstration purposes
    seed_demo_documents(request.user.id)
    metrics = get_dashboard_metrics(request.user.id)

    context = {
        'metrics': metrics,
        'user': request.user,
        'active_nav': 'dashboard'
    }
    return render(request, 'dashboard.html', context)


@login_required
def documents_list(request):
    """
    Document management view with search, filter by category and status, and sort.
    """
    seed_demo_documents(request.user.id)
    search_query = request.GET.get('q', '').strip()
    selected_category = request.GET.get('category', 'All')
    selected_status = request.GET.get('status', 'All')
    selected_sort = request.GET.get('sort', 'newest')

    documents = get_user_documents(
        user_id=request.user.id,
        search_term=search_query,
        category=selected_category,
        status=selected_status,
        sort_by=selected_sort
    )

    categories = ['All'] + list(CATEGORY_METADATA.keys())
    statuses = ['All', 'Active', 'Expiring Soon', 'Expired', 'Lifetime']

    context = {
        'documents': documents,
        'search_query': search_query,
        'selected_category': selected_category,
        'selected_status': selected_status,
        'selected_sort': selected_sort,
        'categories': categories,
        'statuses': statuses,
        'total_count': len(documents),
        'active_nav': 'documents'
    }
    return render(request, 'documents/index.html', context)


@login_required
def document_add(request):
    """
    Add new document to MongoDB collection.
    """
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            data = form.cleaned_data
            file_url = ''

            # Handle file upload if present
            uploaded_file = request.FILES.get('file')
            gridfs_id = None
            if uploaded_file:
                stored = store_uploaded_file(
                    uploaded_file, 
                    uploaded_file.name, 
                    content_type=uploaded_file.content_type, 
                    user_id=request.user.id
                )
                file_url = stored['file_url']
                gridfs_id = stored.get('gridfs_id')

            # Prepare document dict for MongoDB
            new_doc = {
                'title': data['title'].strip(),
                'category': data['category'],
                'document_number': data.get('document_number', '').strip(),
                'issuing_authority': data.get('issuing_authority', '').strip(),
                'issue_date': data['issue_date'].strftime("%Y-%m-%d") if data.get('issue_date') else '',
                'expiry_date': data['expiry_date'].strftime("%Y-%m-%d") if data.get('expiry_date') else '',
                'reminder_days': data.get('reminder_days') or 30,
                'notes': data.get('notes', '').strip(),
                'file_url': file_url,
                'gridfs_id': gridfs_id,
                'is_pinned': False,
                'created_at': datetime.now().isoformat(),
                'user_id': str(request.user.id)
            }

            coll = get_documents_collection()
            res = coll.insert_one(new_doc)
            messages.success(request, f"“{new_doc['title']}” has been securely archived in your vault.")
            return redirect('document_detail', doc_id=str(res.inserted_id))
    else:
        form = DocumentForm()

    context = {
        'form': form,
        'is_edit': False,
        'active_nav': 'add_document',
        'categories': CATEGORY_METADATA
    }
    return render(request, 'documents/form.html', context)


@login_required
def document_detail(request, doc_id):
    """
    View details, renewal checklist, and preview file for a single document.
    """
    doc = get_document_by_id(doc_id, request.user.id)
    if not doc:
        messages.error(request, "Document could not be found or you do not have permission to view it.")
        return redirect('documents_list')

    context = {
        'doc': doc,
        'active_nav': 'documents'
    }
    return render(request, 'documents/detail.html', context)


@login_required
def document_edit(request, doc_id):
    """
    Edit document attributes and renewal terms.
    """
    doc = get_document_by_id(doc_id, request.user.id)
    if not doc:
        raise Http404("Document not found.")

    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            data = form.cleaned_data
            file_url = doc.get('file_url', '')
            gridfs_id = doc.get('gridfs_id')

            # Check if a replacement file was uploaded
            uploaded_file = request.FILES.get('file')
            if uploaded_file:
                stored = store_uploaded_file(
                    uploaded_file, 
                    uploaded_file.name, 
                    content_type=uploaded_file.content_type, 
                    user_id=request.user.id
                )
                file_url = stored['file_url']
                gridfs_id = stored.get('gridfs_id')

            updated_fields = {
                'title': data['title'].strip(),
                'category': data['category'],
                'document_number': data.get('document_number', '').strip(),
                'issuing_authority': data.get('issuing_authority', '').strip(),
                'issue_date': data['issue_date'].strftime("%Y-%m-%d") if data.get('issue_date') else '',
                'expiry_date': data['expiry_date'].strftime("%Y-%m-%d") if data.get('expiry_date') else '',
                'reminder_days': data.get('reminder_days') or 30,
                'notes': data.get('notes', '').strip(),
                'file_url': file_url,
                'gridfs_id': gridfs_id,
                'updated_at': datetime.now().isoformat()
            }

            coll = get_documents_collection()
            try:
                from bson import ObjectId
                coll.update_one({'_id': ObjectId(doc_id), 'user_id': str(request.user.id)}, {'$set': updated_fields})
            except Exception:
                coll.update_one({'_id': str(doc_id), 'user_id': str(request.user.id)}, {'$set': updated_fields})

            messages.success(request, f"Document “{updated_fields['title']}” has been updated successfully.")
            return redirect('document_detail', doc_id=doc_id)
    else:
        # Prepopulate form
        initial_data = {
            'title': doc.get('title'),
            'category': doc.get('category'),
            'document_number': doc.get('document_number'),
            'issuing_authority': doc.get('issuing_authority'),
            'issue_date': doc.get('issue_date'),
            'expiry_date': doc.get('expiry_date'),
            'reminder_days': doc.get('reminder_days', 30),
            'notes': doc.get('notes'),
        }
        form = DocumentForm(initial=initial_data)

    context = {
        'form': form,
        'doc': doc,
        'is_edit': True,
        'active_nav': 'documents',
        'categories': CATEGORY_METADATA
    }
    return render(request, 'documents/form.html', context)


@login_required
def document_delete(request, doc_id):
    """
    Deletes a document from the user's vault.
    """
    if request.method == 'POST':
        success = delete_document_by_id(doc_id, request.user.id)
        if success:
            messages.success(request, "Document removed from your vault.")
        else:
            messages.error(request, "Failed to delete document.")
        return redirect('documents_list')
    return redirect('document_detail', doc_id=doc_id)


def auth_login(request):
    """
    Editorial styled login page.
    """
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f"Welcome back, {user.first_name or user.username}!")
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid username or password. Please try again.")

    return render(request, 'auth/login.html')


def auth_register(request):
    """
    Editorial styled user registration.
    """
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            # Seed starter vault documents
            seed_demo_documents(user.id)
            login(request, user)
            messages.success(request, f"Welcome to DocumentDock, {user.first_name}! Your private vault has been prepared.")
            return redirect('dashboard')
    else:
        form = RegisterForm()

    return render(request, 'auth/register.html', {'form': form})


def auth_logout(request):
    """
    Logs out the user.
    """
    logout(request)
    messages.info(request, "You have been signed out of your vault.")
    return redirect('landing')


def demo_login(request):
    """
    Instant demo vault access. Perfect for college professors or reviewers.
    Creates or retrieves the 'demo' account and logs in directly.
    """
    demo_username = 'demo_reviewer'
    user, created = User.objects.get_or_create(
        username=demo_username,
        defaults={
            'first_name': 'Eleanor',
            'last_name': 'Vance',
            'email': 'eleanor.vance@documentdock.io'
        }
    )
    if created:
        user.set_password('demo1234')
        user.save()

    seed_demo_documents(user.id)
    login(request, user)
    messages.success(request, "Entered interactive demo vault as Eleanor Vance.")
    return redirect('dashboard')


@login_required
def export_vault(request):
    """
    Exports the user's complete vault records from MongoDB as an authenticated JSON file.
    """
    docs = get_user_documents(request.user.id)
    export_payload = {
        'platform': 'DocumentDock',
        'export_version': '1.0',
        'exported_at': datetime.now().isoformat(),
        'vault_user': request.user.username,
        'user_email': request.user.email,
        'total_documents': len(docs),
        'documents': [
            {
                'id': d.get('id_str'),
                'title': d.get('title'),
                'category': d.get('category'),
                'document_number': d.get('document_number'),
                'issuing_authority': d.get('issuing_authority'),
                'issue_date': d.get('issue_date'),
                'expiry_date': d.get('expiry_date'),
                'status': d.get('status'),
                'days_remaining': d.get('days_remaining'),
                'reminder_days': d.get('reminder_days'),
                'notes': d.get('notes'),
                'created_at': d.get('created_at'),
            }
            for d in docs
        ]
    }
    response = JsonResponse(export_payload, json_dumps_params={'indent': 2})
    filename = f"documentdock_vault_{request.user.username}_{date.today().isoformat()}.json"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@login_required
def document_renew(request, doc_id):
    """
    Quick renewal action: extends document expiry date by selected years
    and updates the MongoDB collection directly.
    """
    if request.method == 'POST':
        doc = get_document_by_id(doc_id, request.user.id)
        if not doc:
            raise Http404("Document not found.")

        try:
            years = int(request.POST.get('years', 1))
        except (ValueError, TypeError):
            years = 1

        from .db import parse_date
        current_expiry = parse_date(doc.get('expiry_date')) or date.today()
        base_date = max(current_expiry, date.today())
        
        try:
            new_expiry = base_date.replace(year=base_date.year + years)
        except ValueError:
            new_expiry = base_date + timedelta(days=365 * years)

        coll = get_documents_collection()
        try:
            from bson import ObjectId
            coll.update_one(
                {'_id': ObjectId(doc_id), 'user_id': str(request.user.id)},
                {'$set': {'expiry_date': new_expiry.strftime("%Y-%m-%d"), 'updated_at': datetime.now().isoformat()}}
            )
        except Exception:
            coll.update_one(
                {'_id': str(doc_id), 'user_id': str(request.user.id)},
                {'$set': {'expiry_date': new_expiry.strftime("%Y-%m-%d"), 'updated_at': datetime.now().isoformat()}}
            )

        messages.success(request, f"“{doc['title']}” has been marked renewed! Expiry extended to {new_expiry.strftime('%b %d, %Y')}.")
        return redirect('document_detail', doc_id=doc_id)
    return redirect('document_detail', doc_id=doc_id)


@login_required
def document_file_view(request, file_id):
    """
    Secure authenticated access to document attachments stored in MongoDB GridFS.
    Ensures that only the document owner (or admin) can view or download the file.
    """
    coll = get_documents_collection()
    doc = coll.find_one({'gridfs_id': str(file_id), 'user_id': str(request.user.id)})
    if not doc and not request.user.is_superuser:
        raise PermissionDenied("You do not have permission to access this archival asset.")

    file_meta = get_stored_file(file_id)
    if not file_meta:
        raise Http404("Document asset not found.")

    response = HttpResponse(file_meta['data'], content_type=file_meta['content_type'])
    response['Content-Disposition'] = f'inline; filename="{file_meta["filename"]}"'
    return response
