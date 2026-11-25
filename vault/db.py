"""
DocumentDock MongoDB Data Access Layer
======================================
Connects to MongoDB using PyMongo. 
Provides a resilient fallback to a persistent JSON-backed document store
so the application functions smoothly in all environments (including offline 
evaluations and sandboxes), while adhering strictly to MongoDB collection semantics.
"""

import json
import os
import uuid
from datetime import datetime, date
from pathlib import Path
from django.conf import settings
import pymongo
import gridfs
from bson import ObjectId

# Path for persistent fallback JSON storage if MongoDB daemon is unreachable
IS_VERCEL = bool(os.environ.get('VERCEL'))
FALLBACK_DATA_DIR = Path('/tmp/documentdock_data') if IS_VERCEL else Path(settings.BASE_DIR) / 'data'
FALLBACK_DATA_DIR.mkdir(parents=True, exist_ok=True)
FALLBACK_DB_FILE = FALLBACK_DATA_DIR / 'documents_store.json'
FALLBACK_MEDIA_DIR = Path('/tmp/documentdock_media') if IS_VERCEL else Path(settings.MEDIA_ROOT)


class JSONFallbackCollection:
    """
    A lightweight, persistent JSON collection providing the same core API
    as a PyMongo collection. Used automatically if local MongoDB is stopped.
    """
    def __init__(self, filepath):
        self.filepath = filepath
        if not self.filepath.exists():
            self._write([])

    def _read(self):
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return []

    def _write(self, data):
        with open(self.filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str)

    def insert_one(self, document):
        data = self._read()
        doc = dict(document)
        if '_id' not in doc:
            doc['_id'] = str(uuid.uuid4())
        else:
            doc['_id'] = str(doc['_id'])
        data.append(doc)
        self._write(data)
        class InsertResult:
            def __init__(self, inserted_id):
                self.inserted_id = inserted_id
        return InsertResult(doc['_id'])

    def find(self, filter_dict=None, sort=None):
        data = self._read()
        filter_dict = filter_dict or {}
        results = []
        for item in data:
            match = True
            for k, v in filter_dict.items():
                if k == '_id':
                    if str(item.get('_id')) != str(v):
                        match = False
                        break
                elif item.get(k) != v:
                    match = False
                    break
            if match:
                results.append(dict(item))

        if sort:
            for field, direction in reversed(sort):
                reverse = direction < 0
                results.sort(key=lambda x: x.get(field) or '', reverse=reverse)
        return results

    def find_one(self, filter_dict):
        results = self.find(filter_dict)
        return results[0] if results else None

    def update_one(self, filter_dict, update_dict):
        data = self._read()
        set_vals = update_dict.get('$set', {})
        modified_count = 0
        for item in data:
            match = True
            for k, v in filter_dict.items():
                if k == '_id':
                    if str(item.get('_id')) != str(v):
                        match = False
                        break
                elif item.get(k) != v:
                    match = False
                    break
            if match:
                item.update(set_vals)
                modified_count += 1
                break
        if modified_count > 0:
            self._write(data)
        class UpdateResult:
            def __init__(self, count):
                self.modified_count = count
        return UpdateResult(modified_count)

    def delete_one(self, filter_dict):
        data = self._read()
        initial_len = len(data)
        new_data = []
        deleted = False
        for item in data:
            if not deleted:
                match = True
                for k, v in filter_dict.items():
                    if k == '_id':
                        if str(item.get('_id')) != str(v):
                            match = False
                            break
                    elif item.get(k) != v:
                        match = False
                        break
                if match:
                    deleted = True
                    continue
            new_data.append(item)
        if deleted:
            self._write(new_data)
        class DeleteResult:
            def __init__(self, count):
                self.deleted_count = count
        return DeleteResult(1 if deleted else 0)

    def count_documents(self, filter_dict=None):
        return len(self.find(filter_dict))


_mongo_client = None
_db_connection_status = None
_connection_attempted = False


def get_db():
    """
    Returns the MongoDB database instance or fallback document store.
    Supports local MongoDB as well as cloud MongoDB Atlas clusters.
    """
    global _mongo_client, _db_connection_status, _connection_attempted
    if not _connection_attempted:
        _connection_attempted = True
        uri = getattr(settings, 'MONGODB_URI', 'mongodb://localhost:27017/').strip()
        db_name = getattr(settings, 'MONGODB_DB_NAME', 'documentdock_db')
        if IS_VERCEL and (not uri or 'localhost' in uri or '127.0.0.1' in uri):
            _mongo_client = None
            _db_connection_status = "Temporary Vercel Store (Connect MONGODB_URI for Persistence)"
            return _mongo_client
        try:
            client = pymongo.MongoClient(
                uri,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000
            )
            # Ping to verify active connection
            client.admin.command('ping')
            _mongo_client = client[db_name]
            if 'mongodb+srv://' in uri or '.mongodb.net' in uri:
                _db_connection_status = "MongoDB Atlas (Cloud Cluster Live)"
            else:
                _db_connection_status = "MongoDB (Live Database Engine)"
        except Exception:
            _mongo_client = None
            _db_connection_status = "MongoDB Offline Fallback (JSON Document Store)"

    return _mongo_client


def get_gridfs():
    """
    Returns the GridFS bucket for persistent document file storage
    within MongoDB Atlas, or None if in fallback mode.
    """
    db = get_db()
    if db is not None:
        try:
            return gridfs.GridFS(db)
        except Exception:
            return None
    return None


def store_uploaded_file(file_obj, filename, content_type=None, user_id=None):
    """
    Stores an uploaded PDF or image into MongoDB Atlas GridFS for permanent persistence.
    Falls back to local filesystem storage if in offline fallback mode.
    """
    fs = get_gridfs()
    if fs is not None:
        try:
            file_obj.seek(0)
            file_data = file_obj.read()
            grid_id = fs.put(
                file_data,
                filename=filename,
                content_type=content_type or 'application/octet-stream',
                user_id=str(user_id) if user_id else ''
            )
            return {
                'storage_type': 'gridfs',
                'gridfs_id': str(grid_id),
                'filename': filename,
                'content_type': content_type,
                'file_url': f"/documents/file/{grid_id}/"
            }
        except Exception:
            pass

    # Local fallback storage
    from django.core.files.storage import FileSystemStorage, default_storage
    safe_filename = f"{uuid.uuid4().hex[:12]}_{filename.replace(' ', '_')}"
    upload_path = os.path.join('documents', safe_filename)
    file_obj.seek(0)
    if IS_VERCEL:
        FALLBACK_MEDIA_DIR.mkdir(parents=True, exist_ok=True)
        tmp_storage = FileSystemStorage(location=str(FALLBACK_MEDIA_DIR))
        saved_path = tmp_storage.save(upload_path, file_obj)
    else:
        saved_path = default_storage.save(upload_path, file_obj)
    return {
        'storage_type': 'local',
        'gridfs_id': None,
        'filename': filename,
        'content_type': content_type,
        'file_url': settings.MEDIA_URL + saved_path
    }


def get_stored_file(gridfs_id):
    """
    Retrieves file bytes, filename, and content_type from MongoDB GridFS.
    """
    fs = get_gridfs()
    if fs is None:
        return None
    try:
        grid_out = fs.get(ObjectId(gridfs_id))
        return {
            'data': grid_out.read(),
            'filename': grid_out.filename,
            'content_type': getattr(grid_out, 'content_type', 'application/octet-stream')
        }
    except Exception:
        return None


def get_documents_collection():
    """
    Returns the documents collection from MongoDB or fallback store.
    """
    db = get_db()
    if db is not None:
        return db.documents
    return JSONFallbackCollection(FALLBACK_DB_FILE)


def get_db_status():
    get_db()
    return _db_connection_status


def parse_date(date_val):
    """Safely converts string or date object to date."""
    if not date_val:
        return None
    if isinstance(date_val, (date, datetime)):
        if isinstance(date_val, datetime):
            return date_val.date()
        return date_val
    try:
        return datetime.strptime(str(date_val).strip()[:10], "%Y-%m-%d").date()
    except Exception:
        return None


def calculate_document_status(doc):
    """
    Computes status and remaining days relative to current date.
    Returns (status, days_remaining, urgency_class, badge_text)
    """
    expiry_date = parse_date(doc.get('expiry_date'))
    reminder_days = int(doc.get('reminder_days') or 30)
    today = date.today()

    if not expiry_date:
        return {
            'status': 'Lifetime',
            'days_remaining': None,
            'urgency_class': 'status-lifetime',
            'badge_text': 'Permanent / Lifetime',
            'human_delta': 'Never expires',
            'progress_pct': 100
        }

    delta = (expiry_date - today).days

    if delta < 0:
        return {
            'status': 'Expired',
            'days_remaining': delta,
            'urgency_class': 'status-expired',
            'badge_text': 'Expired',
            'human_delta': f"Expired {abs(delta)} day{'s' if abs(delta) != 1 else ''} ago",
            'progress_pct': 0
        }
    elif delta <= reminder_days:
        return {
            'status': 'Expiring Soon',
            'days_remaining': delta,
            'urgency_class': 'status-warning',
            'badge_text': 'Expiring Soon',
            'human_delta': f"Expires in {delta} day{'s' if delta != 1 else ''}",
            'progress_pct': max(10, min(100, int((delta / max(reminder_days, 1)) * 100)))
        }
    else:
        return {
            'status': 'Active',
            'days_remaining': delta,
            'urgency_class': 'status-active',
            'badge_text': 'Valid',
            'human_delta': f"Valid for {delta} days",
            'progress_pct': 100
        }


CATEGORY_METADATA = {
    'Identity & Travel': {
        'icon': 'passport',
        'color': '#183D32',
        'bg': '#EAF1ED',
        'description': 'Passports, National IDs, Visas, Driver Licenses'
    },
    'Vehicles & Transport': {
        'icon': 'car',
        'color': '#335C4C',
        'bg': '#EBF2EE',
        'description': 'Vehicle Registration, Auto Insurance, Road Tax, MOT'
    },
    'Insurance & Health': {
        'icon': 'shield',
        'color': '#C26A38',
        'bg': '#F9EDE5',
        'description': 'Health Cover, Life Insurance, Dental, Medical Cards'
    },
    'Property & Housing': {
        'icon': 'home',
        'color': '#4A5568',
        'bg': '#EDF2F7',
        'description': 'Tenancy Agreements, Title Deeds, Utility Leases'
    },
    'Professional & Work': {
        'icon': 'briefcase',
        'color': '#2C4A3E',
        'bg': '#EDF4F1',
        'description': 'Work Permits, Accreditations, Diplomas, Contracts'
    },
    'Personal & Finance': {
        'icon': 'file-text',
        'color': '#5D645E',
        'bg': '#F1F3F1',
        'description': 'Memberships, Tax Documents, Warranties, Banking'
    }
}


def enrich_document(doc):
    """
    Augments raw MongoDB document with computed UI properties, formatted dates, and badges.
    """
    if not doc:
        return None
    d = dict(doc)
    doc_id = str(d.get('_id', ''))
    d['id'] = doc_id
    d['id_str'] = doc_id

    # Compute status
    status_info = calculate_document_status(d)
    d.update(status_info)

    # Format dates
    issue_date = parse_date(d.get('issue_date'))
    expiry_date = parse_date(d.get('expiry_date'))
    d['formatted_issue_date'] = issue_date.strftime("%b %d, %Y") if issue_date else "—"
    d['formatted_expiry_date'] = expiry_date.strftime("%b %d, %Y") if expiry_date else "No Expiry Date"
    d['iso_expiry_date'] = expiry_date.strftime("%Y-%m-%d") if expiry_date else ""

    # Category metadata
    category = d.get('category', 'Identity & Travel')
    d['category_meta'] = CATEGORY_METADATA.get(category, CATEGORY_METADATA['Identity & Travel'])

    # File type icon
    file_url = d.get('file_url', '')
    if file_url:
        ext = file_url.split('.')[-1].lower()
        if ext in ['jpg', 'jpeg', 'png', 'webp', 'gif']:
            d['file_type'] = 'image'
        elif ext == 'pdf':
            d['file_type'] = 'pdf'
        else:
            d['file_type'] = 'doc'
    else:
        d['file_type'] = 'none'

    return d


def seed_demo_documents(user_id):
    """
    Pre-populates an initial realistic, editorial set of documents for any newly registered
    user or demo account so the dashboard looks rich and alive immediately.
    """
    coll = get_documents_collection()
    existing = coll.count_documents({'user_id': str(user_id)})
    if existing > 0:
        return

    today = date.today()
    from datetime import timedelta

    sample_docs = [
        {
            'title': 'Biometric British Passport',
            'category': 'Identity & Travel',
            'document_number': 'GBR-88429104',
            'issue_date': (today - timedelta(days=3600)).strftime("%Y-%m-%d"),
            'expiry_date': (today + timedelta(days=42)).strftime("%Y-%m-%d"),
            'reminder_days': 60,
            'notes': 'Renewal window open. Ensure standard UK passport photos comply with HM Passport Office specifications.',
            'issuing_authority': 'His Majesty’s Passport Office',
            'file_url': '/media/sample/passport-sample.jpg',
            'is_pinned': True,
            'created_at': datetime.now().isoformat(),
            'user_id': str(user_id)
        },
        {
            'title': 'Allianz Comprehensive Auto Cover',
            'category': 'Vehicles & Transport',
            'document_number': 'ALZ-MOT-773019',
            'issue_date': (today - timedelta(days=347)).strftime("%Y-%m-%d"),
            'expiry_date': (today + timedelta(days=18)).strftime("%Y-%m-%d"),
            'reminder_days': 30,
            'notes': 'Includes breakdown assistance and zero-deductible windshield coverage. Review renewal quote before direct debit.',
            'issuing_authority': 'Allianz Global Corporate',
            'file_url': '/media/sample/insurance-sample.jpg',
            'is_pinned': True,
            'created_at': datetime.now().isoformat(),
            'user_id': str(user_id)
        },
        {
            'title': 'Residential Lease & Tenancy Agreement',
            'category': 'Property & Housing',
            'document_number': 'TNC-2024-LON-09',
            'issue_date': (today - timedelta(days=150)).strftime("%Y-%m-%d"),
            'expiry_date': (today + timedelta(days=215)).strftime("%Y-%m-%d"),
            'reminder_days': 60,
            'notes': 'Fixed term lease with 2-month notice clause. Deposit registered with DPS Deposit Protection Service.',
            'issuing_authority': 'Chestertons Kensington',
            'file_url': '/media/sample/contract-sample.jpg',
            'is_pinned': False,
            'created_at': datetime.now().isoformat(),
            'user_id': str(user_id)
        },
        {
            'title': 'Bupa Global Platinum Healthcare',
            'category': 'Insurance & Health',
            'document_number': 'BUP-INT-992144',
            'issue_date': (today - timedelta(days=205)).strftime("%Y-%m-%d"),
            'expiry_date': (today + timedelta(days=160)).strftime("%Y-%m-%d"),
            'reminder_days': 45,
            'notes': 'Worldwide health plan including out-patient consultations, dental care, and optical checkups.',
            'issuing_authority': 'Bupa International',
            'file_url': '',
            'is_pinned': False,
            'created_at': datetime.now().isoformat(),
            'user_id': str(user_id)
        },
        {
            'title': 'AWS Certified Solutions Architect – Professional',
            'category': 'Professional & Work',
            'document_number': 'AWS-SAP-09418',
            'issue_date': (today - timedelta(days=420)).strftime("%Y-%m-%d"),
            'expiry_date': (today + timedelta(days=310)).strftime("%Y-%m-%d"),
            'reminder_days': 30,
            'notes': '3-year recertification cycle. Check available voucher codes through AWS Training Portal.',
            'issuing_authority': 'Amazon Web Services Training & Cert',
            'file_url': '',
            'is_pinned': False,
            'created_at': datetime.now().isoformat(),
            'user_id': str(user_id)
        },
        {
            'title': 'International Driving Permit (IDP 1949)',
            'category': 'Identity & Travel',
            'document_number': 'IDP-UK-550192',
            'issue_date': (today - timedelta(days=377)).strftime("%Y-%m-%d"),
            'expiry_date': (today - timedelta(days=12)).strftime("%Y-%m-%d"),
            'reminder_days': 30,
            'notes': 'Expired during last road trip. Need to request renewed 1949 & 1968 permits at the Post Office.',
            'issuing_authority': 'Automobile Association (AA)',
            'file_url': '',
            'is_pinned': False,
            'created_at': datetime.now().isoformat(),
            'user_id': str(user_id)
        },
        {
            'title': 'Original Certified Birth Certificate',
            'category': 'Identity & Travel',
            'document_number': 'GRO-BIRT-1998-02',
            'issue_date': '1998-06-15',
            'expiry_date': '',
            'reminder_days': 0,
            'notes': 'Stored in physical fireproof document safe in vault drawer #3. Original embossed seal.',
            'issuing_authority': 'General Register Office',
            'file_url': '',
            'is_pinned': False,
            'created_at': datetime.now().isoformat(),
            'user_id': str(user_id)
        }
    ]

    for doc in sample_docs:
        coll.insert_one(doc)


def get_user_documents(user_id, search_term=None, category=None, status=None, sort_by=None):
    """
    Retrieves and filters documents for a given user.
    """
    coll = get_documents_collection()
    raw_docs = coll.find({'user_id': str(user_id)})
    enriched = [enrich_document(d) for d in raw_docs]

    # Filter by search term
    if search_term:
        term = search_term.lower().strip()
        enriched = [
            d for d in enriched
            if term in d.get('title', '').lower()
            or term in d.get('document_number', '').lower()
            or term in d.get('notes', '').lower()
            or term in d.get('issuing_authority', '').lower()
            or term in d.get('category', '').lower()
        ]

    # Filter by category
    if category and category != 'All':
        enriched = [d for d in enriched if d.get('category') == category]

    # Filter by status
    if status and status != 'All':
        enriched = [d for d in enriched if d.get('status') == status]

    # Sort
    if sort_by == 'expiry_asc':
        # Put items with dates first sorted by days_remaining, then lifetime at end
        enriched.sort(key=lambda x: (x.get('days_remaining') is None, x.get('days_remaining') if x.get('days_remaining') is not None else 99999))
    elif sort_by == 'expiry_desc':
        enriched.sort(key=lambda x: (x.get('days_remaining') is None, -(x.get('days_remaining') or 0)))
    elif sort_by == 'title':
        enriched.sort(key=lambda x: x.get('title', '').lower())
    else:
        # Default: newest created first
        enriched.sort(key=lambda x: x.get('created_at', ''), reverse=True)

    return enriched


def get_document_by_id(doc_id, user_id):
    """
    Fetches a single document ensuring ownership.
    """
    coll = get_documents_collection()
    
    # Try ObjectId for native Mongo or string id
    doc = None
    try:
        doc = coll.find_one({'_id': ObjectId(doc_id), 'user_id': str(user_id)})
    except Exception:
        pass

    if not doc:
        doc = coll.find_one({'_id': str(doc_id), 'user_id': str(user_id)})

    return enrich_document(doc) if doc else None


def delete_document_by_id(doc_id, user_id):
    """
    Deletes a document ensuring ownership.
    """
    coll = get_documents_collection()
    try:
        res = coll.delete_one({'_id': ObjectId(doc_id), 'user_id': str(user_id)})
        if res.deleted_count > 0:
            return True
    except Exception:
        pass
    res = coll.delete_one({'_id': str(doc_id), 'user_id': str(user_id)})
    return res.deleted_count > 0


def get_dashboard_metrics(user_id):
    """
    Computes summary metrics, category distribution, and upcoming expiry timeline.
    """
    docs = get_user_documents(user_id)
    total = len(docs)
    active = sum(1 for d in docs if d['status'] == 'Active')
    expiring_soon = sum(1 for d in docs if d['status'] == 'Expiring Soon')
    expired = sum(1 for d in docs if d['status'] == 'Expired')
    lifetime = sum(1 for d in docs if d['status'] == 'Lifetime')

    # Category counts
    category_counts = {}
    for cat in CATEGORY_METADATA.keys():
        category_counts[cat] = 0
    for d in docs:
        c = d.get('category', 'Identity & Travel')
        category_counts[c] = category_counts.get(c, 0) + 1

    # Format category breakdown with percentage
    categories_breakdown = []
    for cat, count in category_counts.items():
        pct = int((count / total) * 100) if total > 0 else 0
        categories_breakdown.append({
            'name': cat,
            'count': count,
            'percentage': pct,
            'meta': CATEGORY_METADATA.get(cat, CATEGORY_METADATA['Identity & Travel'])
        })

    # Sort categories by count descending
    categories_breakdown.sort(key=lambda x: x['count'], reverse=True)

    # Upcoming timeline: documents with expiry dates sorted by days_remaining
    timeline_docs = [
        d for d in docs 
        if d.get('days_remaining') is not None
    ]
    timeline_docs.sort(key=lambda x: x['days_remaining'])

    # Recent uploads (top 5 newest)
    recent_uploads = sorted(docs, key=lambda x: x.get('created_at', ''), reverse=True)[:5]

    return {
        'total_documents': total,
        'active_documents': active,
        'expiring_soon': expiring_soon,
        'expired': expired,
        'lifetime': lifetime,
        'categories_breakdown': categories_breakdown,
        'timeline_docs': timeline_docs[:6],
        'recent_uploads': recent_uploads,
        'db_status': get_db_status()
    }

