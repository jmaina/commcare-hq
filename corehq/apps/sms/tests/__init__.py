from django.test import TestCase
from corehq.apps.domain.models import Domain
from corehq.apps.sms.mixin import SMSBackend, BackendMapping, BadSMSConfigException
from corehq.apps.sms.api import send_sms, send_sms_to_verified_number, send_sms_with_backend, send_sms_with_backend_name, BackendAuthorizationException
from corehq.apps.sms.models import CommConnectCase
from django.conf import settings
from couchdbkit.ext.django.schema import *
from couchdbkit.exceptions import ResourceNotFound
from casexml.apps.case.models import CommCareCase
#from .inbound_handlers import *
from .opt_tests import *

class BackendInvocationDoc(Document):
    pass

class TestCaseBackend(SMSBackend):

    @classmethod
    def get_api_id(cls):
        return "TEST_CASE_BACKEND"

    def send(self, msg, *args, **kwargs):
        self.create_invoke_doc()
        print "***************************************************"
        print "Backend:         %s" % self.name
        print "Message To:      %s" % msg.phone_number
        print "Message Content: %s" % msg.text
        print "***************************************************"

    def get_invoke_doc_id(self):
        return "SEND-INVOKED-FROM-%s" % self._id

    def create_invoke_doc(self):
        if not self.invoke_doc_exists():
            doc = BackendInvocationDoc(_id=self.get_invoke_doc_id())
            doc.save()

    def delete_invoke_doc(self):
        try:
            doc = BackendInvocationDoc.get(self.get_invoke_doc_id())
            doc.delete()
        except ResourceNotFound:
            pass

    def invoke_doc_exists(self):
        try:
            BackendInvocationDoc.get(self.get_invoke_doc_id())
            return True
        except ResourceNotFound:
            return False

class BackendTestCase(TestCase):
    def setUp(self):
        self.domain = "test-domain"
        self.domain2 = "test-domain2"

        self.domain_obj = Domain(name=self.domain)
        self.domain_obj.save()
        self.domain_obj = Domain.get(self.domain_obj._id) # Prevent resource conflict

        self.backend1 = TestCaseBackend(name="BACKEND1",is_global=True)
        self.backend1.save()

        self.backend2 = TestCaseBackend(name="BACKEND2",is_global=True)
        self.backend2.save()

        self.backend3 = TestCaseBackend(name="BACKEND3",is_global=True)
        self.backend3.save()

        self.backend4 = TestCaseBackend(name="BACKEND4",is_global=True)
        self.backend4.save()

        self.backend5 = TestCaseBackend(name="BACKEND5",domain=self.domain,is_global=False,authorized_domains=[])
        self.backend5.save()

        self.backend6 = TestCaseBackend(name="BACKEND6",domain=self.domain2,is_global=False,authorized_domains=[self.domain])
        self.backend6.save()

        self.backend7 = TestCaseBackend(name="BACKEND7",domain=self.domain2,is_global=False,authorized_domains=[])
        self.backend7.save()
        
        self.backend8 = TestCaseBackend(name="BACKEND",domain=self.domain,is_global=False,authorized_domains=[])
        self.backend8.save()

        self.backend9 = TestCaseBackend(name="BACKEND",domain=self.domain2,is_global=False,authorized_domains=[self.domain])
        self.backend9.save()

        self.backend10 = TestCaseBackend(name="BACKEND",is_global=True)
        self.backend10.save()

        self.backend_mapping1 = BackendMapping(is_global=True,prefix="*",backend_id=self.backend1._id)
        self.backend_mapping1.save()

        self.backend_mapping2 = BackendMapping(is_global=True,prefix="1",backend_id=self.backend2._id)
        self.backend_mapping2.save()

        self.backend_mapping3 = BackendMapping(is_global=True,prefix="91",backend_id=self.backend3._id)
        self.backend_mapping3.save()

        self.backend_mapping4 = BackendMapping(is_global=True,prefix="265",backend_id=self.backend4._id)
        self.backend_mapping4.save()

        self.case = CommCareCase(domain=self.domain)
        self.case.set_case_property("contact_phone_number","15551234567")
        self.case.set_case_property("contact_phone_number_is_verified", "1")
        self.case.save()

        self.contact = CommConnectCase.wrap(self.case.to_json())

        settings.SMS_LOADED_BACKENDS.append("corehq.apps.sms.tests.TestCaseBackend")

    def tearDown(self):
        self.backend1.delete_invoke_doc()
        self.backend1.delete()
        self.backend_mapping1.delete()

        self.backend2.delete_invoke_doc()
        self.backend2.delete()
        self.backend_mapping2.delete()

        self.backend3.delete_invoke_doc()
        self.backend3.delete()
        self.backend_mapping3.delete()

        self.backend4.delete_invoke_doc()
        self.backend4.delete()
        self.backend_mapping4.delete()

        self.backend5.delete_invoke_doc()
        self.backend5.delete()

        self.backend6.delete_invoke_doc()
        self.backend6.delete()

        self.backend7.delete_invoke_doc()
        self.backend7.delete()

        self.contact.delete_verified_number()
        self.case.delete()

        self.domain_obj.delete()

        settings.SMS_LOADED_BACKENDS.pop()

    def test_backend(self):
        # Test the backend map

        self.assertTrue(send_sms(self.domain, None, "15551234567", "Test for BACKEND2"))
        self.assertFalse(self.backend1.invoke_doc_exists())
        self.assertTrue(self.backend2.invoke_doc_exists())
        self.assertFalse(self.backend3.invoke_doc_exists())
        self.assertFalse(self.backend4.invoke_doc_exists())
        self.assertFalse(self.backend5.invoke_doc_exists())
        self.assertFalse(self.backend6.invoke_doc_exists())
        self.assertFalse(self.backend7.invoke_doc_exists())
        self.assertFalse(self.backend8.invoke_doc_exists())
        self.assertFalse(self.backend9.invoke_doc_exists())
        self.assertFalse(self.backend10.invoke_doc_exists())
        self.backend2.delete_invoke_doc()
        self.assertFalse(self.backend2.invoke_doc_exists())

        self.assertTrue(send_sms(self.domain, None, "9100000000", "Test for BACKEND3"))
        self.assertFalse(self.backend1.invoke_doc_exists())
        self.assertFalse(self.backend2.invoke_doc_exists())
        self.assertTrue(self.backend3.invoke_doc_exists())
        self.assertFalse(self.backend4.invoke_doc_exists())
        self.assertFalse(self.backend5.invoke_doc_exists())
        self.assertFalse(self.backend6.invoke_doc_exists())
        self.assertFalse(self.backend7.invoke_doc_exists())
        self.assertFalse(self.backend8.invoke_doc_exists())
        self.assertFalse(self.backend9.invoke_doc_exists())
        self.assertFalse(self.backend10.invoke_doc_exists())
        self.backend3.delete_invoke_doc()
        self.assertFalse(self.backend3.invoke_doc_exists())

        self.assertTrue(send_sms(self.domain, None, "26500000000", "Test for BACKEND4"))
        self.assertFalse(self.backend1.invoke_doc_exists())
        self.assertFalse(self.backend2.invoke_doc_exists())
        self.assertFalse(self.backend3.invoke_doc_exists())
        self.assertTrue(self.backend4.invoke_doc_exists())
        self.assertFalse(self.backend5.invoke_doc_exists())
        self.assertFalse(self.backend6.invoke_doc_exists())
        self.assertFalse(self.backend7.invoke_doc_exists())
        self.assertFalse(self.backend8.invoke_doc_exists())
        self.assertFalse(self.backend9.invoke_doc_exists())
        self.assertFalse(self.backend10.invoke_doc_exists())
        self.backend4.delete_invoke_doc()
        self.assertFalse(self.backend4.invoke_doc_exists())

        self.assertTrue(send_sms(self.domain, None, "25800000000", "Test for BACKEND1"))
        self.assertTrue(self.backend1.invoke_doc_exists())
        self.assertFalse(self.backend2.invoke_doc_exists())
        self.assertFalse(self.backend3.invoke_doc_exists())
        self.assertFalse(self.backend4.invoke_doc_exists())
        self.assertFalse(self.backend5.invoke_doc_exists())
        self.assertFalse(self.backend6.invoke_doc_exists())
        self.assertFalse(self.backend7.invoke_doc_exists())
        self.assertFalse(self.backend8.invoke_doc_exists())
        self.assertFalse(self.backend9.invoke_doc_exists())
        self.assertFalse(self.backend10.invoke_doc_exists())
        self.backend1.delete_invoke_doc()
        self.assertFalse(self.backend1.invoke_doc_exists())

        # Test overriding with a domain-level backend

        self.domain_obj.default_sms_backend_id = self.backend5._id
        self.domain_obj.save()

        self.assertTrue(send_sms(self.domain, None, "15551234567", "Test for BACKEND5"))
        self.assertFalse(self.backend1.invoke_doc_exists())
        self.assertFalse(self.backend2.invoke_doc_exists())
        self.assertFalse(self.backend3.invoke_doc_exists())
        self.assertFalse(self.backend4.invoke_doc_exists())
        self.assertTrue(self.backend5.invoke_doc_exists())
        self.assertFalse(self.backend6.invoke_doc_exists())
        self.assertFalse(self.backend7.invoke_doc_exists())
        self.assertFalse(self.backend8.invoke_doc_exists())
        self.assertFalse(self.backend9.invoke_doc_exists())
        self.assertFalse(self.backend10.invoke_doc_exists())
        self.backend5.delete_invoke_doc()
        self.assertFalse(self.backend5.invoke_doc_exists())

        # Test use of backend that another domain owns but has granted access

        self.domain_obj.default_sms_backend_id = self.backend6._id
        self.domain_obj.save()

        self.assertTrue(send_sms(self.domain, None, "25800000000", "Test for BACKEND6"))
        self.assertFalse(self.backend1.invoke_doc_exists())
        self.assertFalse(self.backend2.invoke_doc_exists())
        self.assertFalse(self.backend3.invoke_doc_exists())
        self.assertFalse(self.backend4.invoke_doc_exists())
        self.assertFalse(self.backend5.invoke_doc_exists())
        self.assertTrue(self.backend6.invoke_doc_exists())
        self.assertFalse(self.backend7.invoke_doc_exists())
        self.assertFalse(self.backend8.invoke_doc_exists())
        self.assertFalse(self.backend9.invoke_doc_exists())
        self.assertFalse(self.backend10.invoke_doc_exists())
        self.backend6.delete_invoke_doc()
        self.assertFalse(self.backend6.invoke_doc_exists())

        # Test backend access control

        self.domain_obj.default_sms_backend_id = self.backend7._id
        self.domain_obj.save()

        self.assertFalse(send_sms(self.domain, None, "25800000000", "Test for BACKEND7"))
        self.assertFalse(self.backend1.invoke_doc_exists())
        self.assertFalse(self.backend2.invoke_doc_exists())
        self.assertFalse(self.backend3.invoke_doc_exists())
        self.assertFalse(self.backend4.invoke_doc_exists())
        self.assertFalse(self.backend5.invoke_doc_exists())
        self.assertFalse(self.backend6.invoke_doc_exists())
        self.assertFalse(self.backend7.invoke_doc_exists())
        self.assertFalse(self.backend8.invoke_doc_exists())
        self.assertFalse(self.backend9.invoke_doc_exists())
        self.assertFalse(self.backend10.invoke_doc_exists())

        # Test sending to verified number with backend map

        self.domain_obj.default_sms_backend_id = None
        self.domain_obj.save()

        verified_number = self.contact.get_verified_number()
        self.assertTrue(verified_number is not None)
        self.assertTrue(verified_number.backend_id is None)
        self.assertEqual(verified_number.phone_number, "15551234567")

        self.assertTrue(send_sms_to_verified_number(verified_number, "Test for BACKEND2"))
        self.assertFalse(self.backend1.invoke_doc_exists())
        self.assertTrue(self.backend2.invoke_doc_exists())
        self.assertFalse(self.backend3.invoke_doc_exists())
        self.assertFalse(self.backend4.invoke_doc_exists())
        self.assertFalse(self.backend5.invoke_doc_exists())
        self.assertFalse(self.backend6.invoke_doc_exists())
        self.assertFalse(self.backend7.invoke_doc_exists())
        self.assertFalse(self.backend8.invoke_doc_exists())
        self.assertFalse(self.backend9.invoke_doc_exists())
        self.assertFalse(self.backend10.invoke_doc_exists())
        self.backend2.delete_invoke_doc()
        self.assertFalse(self.backend2.invoke_doc_exists())

        # Test sending to verified number with default domain backend

        self.domain_obj.default_sms_backend_id = self.backend5._id
        self.domain_obj.save()

        self.assertTrue(send_sms_to_verified_number(verified_number, "Test for BACKEND5"))
        self.assertFalse(self.backend1.invoke_doc_exists())
        self.assertFalse(self.backend2.invoke_doc_exists())
        self.assertFalse(self.backend3.invoke_doc_exists())
        self.assertFalse(self.backend4.invoke_doc_exists())
        self.assertTrue(self.backend5.invoke_doc_exists())
        self.assertFalse(self.backend6.invoke_doc_exists())
        self.assertFalse(self.backend7.invoke_doc_exists())
        self.assertFalse(self.backend8.invoke_doc_exists())
        self.assertFalse(self.backend9.invoke_doc_exists())
        self.assertFalse(self.backend10.invoke_doc_exists())
        self.backend5.delete_invoke_doc()
        self.assertFalse(self.backend5.invoke_doc_exists())

        # Test sending to verified number with a contact-level backend owned by the domain

        self.case.set_case_property("contact_backend_id", "BACKEND")
        self.case.save()
        self.contact = CommConnectCase.wrap(self.case.to_json())
        verified_number = self.contact.get_verified_number()
        self.assertTrue(verified_number is not None)
        self.assertEqual(verified_number.backend_id, "BACKEND")
        self.assertEqual(verified_number.phone_number, "15551234567")

        self.assertTrue(send_sms_to_verified_number(verified_number, "Test for BACKEND"))
        self.assertFalse(self.backend1.invoke_doc_exists())
        self.assertFalse(self.backend2.invoke_doc_exists())
        self.assertFalse(self.backend3.invoke_doc_exists())
        self.assertFalse(self.backend4.invoke_doc_exists())
        self.assertFalse(self.backend5.invoke_doc_exists())
        self.assertFalse(self.backend6.invoke_doc_exists())
        self.assertFalse(self.backend7.invoke_doc_exists())
        self.assertTrue(self.backend8.invoke_doc_exists())
        self.assertFalse(self.backend9.invoke_doc_exists())
        self.assertFalse(self.backend10.invoke_doc_exists())
        self.backend8.delete_invoke_doc()
        self.assertFalse(self.backend8.invoke_doc_exists())

        # Test sending to verified number with a contact-level backend granted to the domain by another domain

        self.backend8.delete()

        self.assertTrue(send_sms_to_verified_number(verified_number, "Test for BACKEND"))
        self.assertFalse(self.backend1.invoke_doc_exists())
        self.assertFalse(self.backend2.invoke_doc_exists())
        self.assertFalse(self.backend3.invoke_doc_exists())
        self.assertFalse(self.backend4.invoke_doc_exists())
        self.assertFalse(self.backend5.invoke_doc_exists())
        self.assertFalse(self.backend6.invoke_doc_exists())
        self.assertFalse(self.backend7.invoke_doc_exists())
        self.assertTrue(self.backend9.invoke_doc_exists())
        self.assertFalse(self.backend10.invoke_doc_exists())
        self.backend9.delete_invoke_doc()
        self.assertFalse(self.backend9.invoke_doc_exists())

        # Test sending to verified number with a contact-level global backend

        self.backend9.delete()

        self.assertTrue(send_sms_to_verified_number(verified_number, "Test for BACKEND"))
        self.assertFalse(self.backend1.invoke_doc_exists())
        self.assertFalse(self.backend2.invoke_doc_exists())
        self.assertFalse(self.backend3.invoke_doc_exists())
        self.assertFalse(self.backend4.invoke_doc_exists())
        self.assertFalse(self.backend5.invoke_doc_exists())
        self.assertFalse(self.backend6.invoke_doc_exists())
        self.assertFalse(self.backend7.invoke_doc_exists())
        self.assertTrue(self.backend10.invoke_doc_exists())
        self.backend10.delete_invoke_doc()
        self.assertFalse(self.backend10.invoke_doc_exists())

        # Test raising exception if contact-level backend is not found

        self.backend10.delete()

        try:
            self.assertTrue(send_sms_to_verified_number(verified_number, "Test for BACKEND"))
        except BadSMSConfigException:
            pass
        else:
            self.assertTrue(False)

        # Test send_sms_with_backend

        self.assertTrue(send_sms_with_backend(self.domain, "+15551234567", "Test for BACKEND3", self.backend3._id))
        self.assertFalse(self.backend1.invoke_doc_exists())
        self.assertFalse(self.backend2.invoke_doc_exists())
        self.assertTrue(self.backend3.invoke_doc_exists())
        self.assertFalse(self.backend4.invoke_doc_exists())
        self.assertFalse(self.backend5.invoke_doc_exists())
        self.assertFalse(self.backend6.invoke_doc_exists())
        self.assertFalse(self.backend7.invoke_doc_exists())
        self.backend3.delete_invoke_doc()
        self.assertFalse(self.backend3.invoke_doc_exists())

        # Test send_sms_with_backend_name

        self.assertTrue(send_sms_with_backend_name(self.domain, "+15551234567", "Test for BACKEND3", "BACKEND3"))
        self.assertFalse(self.backend1.invoke_doc_exists())
        self.assertFalse(self.backend2.invoke_doc_exists())
        self.assertTrue(self.backend3.invoke_doc_exists())
        self.assertFalse(self.backend4.invoke_doc_exists())
        self.assertFalse(self.backend5.invoke_doc_exists())
        self.assertFalse(self.backend6.invoke_doc_exists())
        self.assertFalse(self.backend7.invoke_doc_exists())
        self.backend3.delete_invoke_doc()
        self.assertFalse(self.backend3.invoke_doc_exists())


