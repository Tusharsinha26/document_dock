from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from datetime import date, timedelta
from vault.db import get_documents_collection, get_user_documents, calculate_document_status


class DocumentDockTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='secretpassword123',
            first_name='Arthur',
            last_name='Dent',
            email='arthur@example.com'
        )

    def test_landing_page_renders_successfully(self):
        response = self.client.get(reverse('landing'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Important things shouldn't")
        self.assertContains(response, "Small deadlines")
        self.assertContains(response, "Add your documents")
        self.assertContains(response, "Track expiry dates")
        self.assertContains(response, "Renew before deadlines")
        self.assertContains(response, "Your papers are your business")
        self.assertContains(response, "Get ahead of every expiry")

    def test_demo_login_seeds_vault_and_redirects(self):
        response = self.client.get(reverse('demo_login'))
        self.assertRedirects(response, reverse('dashboard'))
        dash_response = self.client.get(reverse('dashboard'))
        self.assertEqual(dash_response.status_code, 200)
        self.assertContains(dash_response, "Upcoming Expiry Timeline")
        self.assertContains(dash_response, "Vault Composition")

    def test_document_crud_flow_and_renew(self):
        self.client.login(username='testuser', password='secretpassword123')
        
        # 1. Dashboard
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)

        # 2. Add Document
        today = date.today()
        test_expiry = (today + timedelta(days=20)).strftime("%Y-%m-%d")
        add_response = self.client.post(reverse('document_add'), {
            'title': 'Test Global Passport',
            'category': 'Identity & Travel',
            'document_number': 'TST-990011',
            'issuing_authority': 'Department of Foreign Affairs',
            'issue_date': '2020-01-01',
            'expiry_date': test_expiry,
            'reminder_days': 60,
            'notes': 'Test notes for passport'
        })
        self.assertEqual(add_response.status_code, 302)

        docs = get_user_documents(self.user.id)
        test_doc = next((d for d in docs if d['document_number'] == 'TST-990011'), None)
        self.assertIsNotNone(test_doc)
        self.assertEqual(test_doc['status'], 'Expiring Soon')

        # 3. View Document Detail
        detail_response = self.client.get(reverse('document_detail', args=[test_doc['id']]))
        self.assertEqual(detail_response.status_code, 200)
        self.assertContains(detail_response, 'Test Global Passport')
        self.assertContains(detail_response, 'TST-990011')

        # 4. Quick Renew Action (+1 Year)
        renew_response = self.client.post(reverse('document_renew', args=[test_doc['id']]), {'years': 1})
        self.assertEqual(renew_response.status_code, 302)
        
        # Verify renewed document is now Active
        docs_after_renew = get_user_documents(self.user.id)
        renewed_doc = next((d for d in docs_after_renew if d['document_number'] == 'TST-990011'), None)
        self.assertEqual(renewed_doc['status'], 'Active')

        # 5. Export Vault Data
        export_response = self.client.get(reverse('export_vault'))
        self.assertEqual(export_response.status_code, 200)
        self.assertEqual(export_response['Content-Type'], 'application/json')
        export_data = export_response.json()
        self.assertIn('documents', export_data)
        self.assertGreaterEqual(len(export_data['documents']), 1)

        # 6. Filter & Search with Category containing &
        list_response = self.client.get(reverse('documents_list') + '?category=Identity%20%26%20Travel')
        self.assertEqual(list_response.status_code, 200)
        self.assertContains(list_response, 'Test Global Passport')

        # 7. Delete Document
        del_response = self.client.post(reverse('document_delete', args=[test_doc['id']]))
        self.assertEqual(del_response.status_code, 302)
        
        docs_after = get_user_documents(self.user.id)
        found = any(d['id'] == test_doc['id'] for d in docs_after)
        self.assertFalse(found)

    def test_status_calculations_accuracy(self):
        today = date.today()
        # Expired
        doc_expired = {'expiry_date': (today - timedelta(days=5)).strftime("%Y-%m-%d"), 'reminder_days': 30}
        res_exp = calculate_document_status(doc_expired)
        self.assertEqual(res_exp['status'], 'Expired')
        self.assertEqual(res_exp['days_remaining'], -5)

        # Expiring Soon
        doc_soon = {'expiry_date': (today + timedelta(days=15)).strftime("%Y-%m-%d"), 'reminder_days': 30}
        res_soon = calculate_document_status(doc_soon)
        self.assertEqual(res_soon['status'], 'Expiring Soon')

        # Active
        doc_active = {'expiry_date': (today + timedelta(days=120)).strftime("%Y-%m-%d"), 'reminder_days': 30}
        res_act = calculate_document_status(doc_active)
        self.assertEqual(res_act['status'], 'Active')

        # Lifetime (no expiry)
        doc_life = {'expiry_date': '', 'reminder_days': 30}
        res_life = calculate_document_status(doc_life)
        self.assertEqual(res_life['status'], 'Lifetime')
        self.assertIsNone(res_life['days_remaining'])
