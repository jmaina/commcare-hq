from django.test import TestCase
from corehq.apps.sms.mixin import BackendMapping
from corehq.apps.sms.api import incoming, send_sms
from corehq.apps.sms.models import PhoneNumber
from corehq.apps.sms.test_backend import TestSMSBackend
from corehq.apps.domain.models import Domain


class OptTestCase(TestCase):
    def setUp(self):
        self.domain = "opt-test"

        self.domain_obj = Domain(name=self.domain)
        self.domain_obj.save()

        self.backend = TestSMSBackend(is_global=True)
        self.backend.save()

        self.backend_mapping = BackendMapping(
            is_global=True,
            prefix="*",
            backend_id=self.backend._id,
        )
        self.backend_mapping.save()

    def test_opt_out_and_opt_in(self):
        self.assertEqual(PhoneNumber.objects.count(), 0)

        incoming("99912345678", "stop", "GVI")
        self.assertEqual(PhoneNumber.objects.count(), 1)
        phone_number = PhoneNumber.objects.get(phone_number="99912345678")
        self.assertFalse(phone_number.send_sms)

        incoming("99912345678", "start", "GVI")
        self.assertEqual(PhoneNumber.objects.count(), 1)
        phone_number = PhoneNumber.objects.get(phone_number="99912345678")
        self.assertTrue(phone_number.send_sms)

    def test_sending_to_opted_out_number(self):
        self.assertEqual(PhoneNumber.objects.count(), 0)
        self.assertTrue(send_sms(self.domain, None, "999123456789", "hello"))

        incoming("999123456789", "stop", "GVI")
        self.assertEqual(PhoneNumber.objects.count(), 1)
        phone_number = PhoneNumber.objects.get(phone_number="999123456789")
        self.assertFalse(phone_number.send_sms)

        self.assertFalse(send_sms(self.domain, None, "999123456789", "hello"))

    def tearDown(self):
        self.backend_mapping.delete()
        self.backend.delete()
        self.domain_obj.delete()
