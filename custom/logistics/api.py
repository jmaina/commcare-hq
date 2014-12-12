from decimal import Decimal
import logging
from couchforms.models import XFormInstance
from restkit import ResourceNotFound
from corehq.apps.consumption.const import DAYS_IN_MONTH
from corehq.apps.products.models import Product, SQLProduct
from dimagi.utils.dates import force_to_datetime
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
import requests
from corehq.apps.commtrack.models import SupplyPointCase
from corehq.apps.sms.mixin import PhoneNumberInUseException, VerifiedNumber
from corehq.apps.users.models import CouchUser, CommCareUser, WebUser
from custom.api.utils import EndpointMixin, apply_updates
from custom.logistics.commtrack import add_location

from casexml.apps.stock.models import StockReport, StockTransaction
from corehq.apps.commtrack.models import StockState


class MigrationException(Exception):
    pass


class LogisticsEndpoint(EndpointMixin):
    models_map = {}

    def __init__(self, base_uri, username, password):
        self.base_uri = base_uri.rstrip('/')
        self.username = username
        self.password = password
        self.products_url = self._urlcombine(self.base_uri, '/products/')
        self.webusers_url = self._urlcombine(self.base_uri, '/webusers/')
        self.smsusers_url = self._urlcombine(self.base_uri, '/smsusers/')
        self.locations_url = self._urlcombine(self.base_uri, '/locations/')
        self.productstock_url = self._urlcombine(self.base_uri, '/productstocks/')
        self.stocktransactions_url = self._urlcombine(self.base_uri, '/stocktransactions/')

    def get_objects(self, url, params=None, filters=None, limit=100, offset=0, **kwargs):
        params = params if params else {}
        if filters:
            params.update(filters)

        params.update({
            'limit': limit,
            'offset': offset
        })

        if 'next_url_params' in kwargs and kwargs['next_url_params']:
            url = url + "?" + kwargs['next_url_params']
            params = {}

        response = requests.get(url, params=params,
                                auth=self._auth())
        if response.status_code == 200 and 'objects' in response.json():
            meta = response.json()['meta']
            objects = response.json()['objects']
        elif response.status_code == 401:
            raise MigrationException('Invalid credentials.')
        else:
            raise MigrationException('Something went wrong during migration.')

        return meta, objects

    def get_products(self, **kwargs):
        meta, products = self.get_objects(self.products_url, **kwargs)
        return meta, [(self.models_map['product'])(product) for product in products]

    def get_webusers(self, **kwargs):
        meta, users = self.get_objects(self.webusers_url, **kwargs)
        return meta, [(self.models_map['webuser'])(user) for user in users]

    def get_smsusers(self, **kwargs):
        meta, users = self.get_objects(self.smsusers_url, **kwargs)
        return meta, [(self.models_map['smsuser'])(user) for user in users]

    def get_location(self, id, params=None):
        response = requests.get(self.locations_url + str(id) + "/", params=params, auth=self._auth())
        return response.json()

    def get_locations(self, **kwargs):
        meta, locations = self.get_objects(self.locations_url, **kwargs)
        return meta, [(self.models_map['location'])(location) for location in locations]

    def get_productstocks(self, **kwargs):
        meta, product_stocks = self.get_objects(self.productstock_url, **kwargs)
        return meta, [(self.models_map['product_stock'])(product_stock) for product_stock in product_stocks]

    def get_stocktransactions(self, **kwargs):
        meta, stock_transactions = self.get_objects(self.stocktransactions_url, **kwargs)
        return meta, [(self.models_map['stock_transaction'])(stock_transaction)
                      for stock_transaction in stock_transactions]


class AbstractAPISynchronization(object):

    def __init__(self, domain, endpoint):
        self.domain = domain
        self.endpoint = endpoint


class APISynchronization(AbstractAPISynchronization):

    def prepare_commtrack_config(self):
        raise NotImplemented("Not implemented yet")

    def products_sync(self, ilsgateway_product):
        product = Product.get_by_code(self.domain, ilsgateway_product.sms_code)
        product_dict = {
            'domain': self.domain,
            'name': ilsgateway_product.name,
            'code': ilsgateway_product.sms_code,
            'unit': str(ilsgateway_product.units),
            'description': ilsgateway_product.description,
        }
        if product is None:
            product = Product(**product_dict)
            product.save()
        else:
            if apply_updates(product, product_dict):
                product.save()
        return product

    def locations_sync(self, ilsgateway_location):
        raise NotImplemented("Not implemented yet")

    def web_users_sync(self, ilsgateway_webuser):
        username = ilsgateway_webuser.email.lower()
        if not username:
            try:
                validate_email(ilsgateway_webuser.username)
                username = ilsgateway_webuser.username
            except ValidationError:
                return None
        user = WebUser.get_by_username(username)
        user_dict = {
            'first_name': ilsgateway_webuser.first_name,
            'last_name': ilsgateway_webuser.last_name,
            'is_active': ilsgateway_webuser.is_active,
            'last_login': force_to_datetime(ilsgateway_webuser.last_login),
            'date_joined': force_to_datetime(ilsgateway_webuser.date_joined),
            'password_hashed': True,
        }
        sp = SupplyPointCase.view('hqcase/by_domain_external_id',
                                  key=[self.domain, str(ilsgateway_webuser.location)],
                                  reduce=False,
                                  include_docs=True,
                                  limit=1).first()
        location_id = sp.location_id if sp else None

        if user is None:
            try:
                user = WebUser.create(domain=None, username=username,
                                      password=ilsgateway_webuser.password, email=ilsgateway_webuser.email,
                                      **user_dict)
                user.add_domain_membership(self.domain, location_id=location_id)
                user.save()
            except Exception as e:
                logging.error(e)
        else:
            if self.domain not in user.get_domains():
                user.add_domain_membership(self.domain, location_id=location_id)
                user.save()
        return user

    def sms_users_sync(self, ilsgateway_smsuser):
        domain_part = "%s.commcarehq.org" % self.domain
        username_part = "%s%d" % (ilsgateway_smsuser.name.strip().replace(' ', '.').lower(), ilsgateway_smsuser.id)
        username = "%s@%s" % (username_part[:(128 - (len(domain_part) + 1))], domain_part)
        # sanity check
        assert len(username) <= 128
        user = CouchUser.get_by_username(username)
        splitted_value = ilsgateway_smsuser.name.split(' ', 1)
        first_name = last_name = ''
        if splitted_value:
            first_name = splitted_value[0][:30]
            last_name = splitted_value[1][:30] if len(splitted_value) > 1 else ''

        user_dict = {
            'first_name': first_name,
            'last_name': last_name,
            'is_active': bool(ilsgateway_smsuser.is_active),
            'email': ilsgateway_smsuser.email,
            'user_data': {}
        }

        if ilsgateway_smsuser.role:
            user_dict['user_data']['role'] = ilsgateway_smsuser.role

        if ilsgateway_smsuser.phone_numbers:
            user_dict['phone_numbers'] = [ilsgateway_smsuser.phone_numbers[0].replace('+', '')]
            user_dict['user_data']['backend'] = ilsgateway_smsuser.backend

        sp = SupplyPointCase.view('hqcase/by_domain_external_id',
                                  key=[self.domain, str(ilsgateway_smsuser.supply_point)],
                                  reduce=False,
                                  include_docs=True,
                                  limit=1).first()
        location_id = sp.location_id if sp else None

        if user is None and username_part:
            try:
                password = User.objects.make_random_password()
                user = CommCareUser.create(domain=self.domain, username=username, password=password,
                                           email=ilsgateway_smsuser.email, commit=False)
                user.first_name = first_name
                user.last_name = last_name
                user.is_active = bool(ilsgateway_smsuser.is_active)
                user.user_data = user_dict["user_data"]
                if "phone_numbers" in user_dict:
                    user.set_default_phone_number(user_dict["phone_numbers"][0])
                    try:
                        user.save_verified_number(self.domain, user_dict["phone_numbers"][0], True,
                                                  ilsgateway_smsuser.backend)
                    except PhoneNumberInUseException as e:
                        v = VerifiedNumber.by_phone(user_dict["phone_numbers"][0], include_pending=True)
                        v.delete()
                        user.save_verified_number(self.domain, user_dict["phone_numbers"][0], True,
                                                  ilsgateway_smsuser.backend)
                dm = user.get_domain_membership(self.domain)
                dm.location_id = location_id
                user.save()
                add_location(user, location_id)

            except Exception as e:
                logging.error(e)
        else:
            dm = user.get_domain_membership(self.domain)
            current_location_id = dm.location_id if dm else None
            save = False

            if current_location_id != location_id:
                dm.location_id = location_id
                add_location(user, location_id)
                save = True

            if apply_updates(user, user_dict) or save:
                user.save()
        return user


class StockDataAPI(AbstractAPISynchronization):

    def _get_fake_xform(self):
        try:
            xform = XFormInstance.get(docid='ilsgateway-xform')
        except ResourceNotFound:
            xform = XFormInstance(_id='ilsgateway-xform')
            xform.save()
        return xform

    def product_stocks_sync(self, product_stock):
        case = SupplyPointCase.view('hqcase/by_domain_external_id',
                                    key=[self.domain, str(product_stock.supply_point)],
                                    reduce=False,
                                    include_docs=True,
                                    limit=1).first()
        product = Product.get_by_code(self.domain, product_stock.product)
        try:
            stock_state = StockState.objects.get(section_id='stock',
                                                 case_id=case._id,
                                                 product_id=product._id)
        except StockState.DoesNotExist:
            stock_state = StockState(section_id='stock',
                                     case_id=case._id,
                                     product_id=product._id,
                                     stock_on_hand=product_stock.quantity or 0,
                                     last_modified_date=product_stock.last_modified,
                                     sql_product=SQLProduct.objects.get(product_id=product._id))

        if product_stock.auto_monthly_consumption:
            stock_state.daily_consumption = product_stock.auto_monthly_consumption / DAYS_IN_MONTH
        else:
            stock_state.daily_consumption = None
        stock_state.save()

    def stock_transactions_sync(self, stocktransaction):
        case = SupplyPointCase.view('hqcase/by_domain_external_id',
                                    key=[self.domain, str(stocktransaction.supply_point)],
                                    reduce=False,
                                    include_docs=True,
                                    limit=1).first()
        product = Product.get_by_code(self.domain, stocktransaction.product)
        report = StockReport(
            form_id=self._get_fake_xform()._id,
            date=force_to_datetime(stocktransaction.date),
            type='balance',
            domain=self.domain
        )
        report.save()
        try:
            sql_product = SQLProduct.objects.get(product_id=product._id)
        except SQLProduct.DoesNotExist:
            return None

        return StockTransaction(
            case_id=case._id,
            product_id=product._id,
            sql_product=sql_product,
            section_id='stock',
            type='stockonhand',
            stock_on_hand=Decimal(stocktransaction.ending_balance),
            report=report
        )
