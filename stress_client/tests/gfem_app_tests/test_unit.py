from ..utils import test_read_excel
from django.test import TestCase, Client
from stress_client.settings import CONFIG
import re
from ..service_tests.test_unit import TestOutFile


class CommonCheck(TestOutFile):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.client = Client()
        cls.ref = './tests/test_reference/'
        cls.path = './tests/test_input/'

    def smart_check(self, url, input_data: dict, templates: list, page, test_name):
        response = self.client.get(url, input_data)
        self.assertEqual(response.status_code, 200, msg=test_name)
        for template in templates:
            self.assertTemplateUsed(response, template, msg_prefix=test_name)
        csrf_regex = r'<input[^>]+csrfmiddlewaretoken[^>]+>'
        observed_html = re.sub(csrf_regex, '', response.content.decode('utf8'))  # remove line with csrf
        self.maxDiff = None
        self.assertHTMLEqual(observed_html, page, msg=test_name) if page else None
        return response


class ViewCases(CommonCheck):
    def test_main_view(self):
        input_data = {}
        with open(''.join((self.ref, 'first_page.html')), 'r', encoding='utf8') as f:
            page = f.read()
        self.smart_check('', input_data, ['first_page.html', 'hf_template.html', 'gfem_rules/node_create_rule.html'],
                         page, 'First page test.')

    def test_post_view(self):
        input_data = {}
        with open(''.join((self.ref, 'post_page.html')), 'r', encoding='utf8') as f:
            page = f.read()
        response = self.smart_check('/gfem/post_data', input_data, ['post_page.html', 'hf_template.html', 'table_form.html'],
                         page, 'Post page test.')
        self.assertContains(response, "Node")  # check that html contain. It is not recommended to check all html

    def test_get_view(self):
        input_data = {}
        with open(''.join((self.ref, 'get_page.html')), 'r', encoding='utf8') as f:
            page = f.read()
        self.smart_check('/gfem/get_data', input_data, ['get_page.html', 'hf_template.html', 'table_form.html'],
                         page, 'Post page test.')

    def test_put_view(self):
        input_data = {}
        with open(''.join((self.ref, 'put_page.html')), 'r', encoding='utf8') as f:
            page = f.read()
        self.smart_check('/gfem/update_data', input_data, ['change_page.html', 'hf_template.html', 'table_form.html'],
                         page, 'Put page test.')

    def test_del_view(self):
        input_data = {}
        with open(''.join((self.ref, 'delete_page.html')), 'r', encoding='utf8') as f:
            page = f.read()
        self.smart_check('/gfem/delete_data', input_data, ['delete_page.html', 'hf_template.html', 'table_form.html'],
                         page, 'Delete page test.')

    # ToDo create tests for wrong inputs


class AjaxTests(CommonCheck):
    def test_get_table_fields(self):
        url = '/ajax/get_table_fields/'
        input_data = {'table_name': 'Node'}
        fields = {'Node': ['uid', 'frame', 'stringer', 'side', 'cs1', 'coord_x', 'coord_y', 'coord_z']}
        response = self.smart_check(url, input_data, ['table_form.html'], None, 'Ajax page test.')
        [self.assertContains(response, field) for field in fields['Node']]

    # ToDo create tests for other ajax pages


class UtilsTest(CommonCheck):
    def test_from_xls_to_dict(self):
        input_data = {'table_name': 'L-Section', 'excel_selection': 'on', 'upload': 'CrossSections_Test.xlsx'}
        pass
        # TODO create test