from django.test import TestCase, Client
from stress_service.utils import cs_converter, cs_utils, uid_generate
import pandas as pd
from ..utils import test_read_excel


L_SECTION = [{'type': 'L-Section', 'area': 79.0, 'cog_Y': 13.514, 'cog_Z': 17.017, 'Iyy': 33088.41, 'Izz': 29907.99,
          'Iyz': 10931.45, 'J': 25.28, 'Iyy_cog': 10211.329, 'Izz_cog': 15479.305, 'Iyz_cog': -7236.8226,
          'alpha': -35.0, 'Imain_1': 5144.05, 'Imain_2': 20546.58, 'I0': 7.27e-09}]


class TestOutFile(TestCase):
    def excel_check(self, url, input_data, reference, messages, test_name):
        with open(''.join((self.path, input_data['upload'])), mode='rb') as input_file:
            input_data['upload'] = input_file
            response = self.client.post(url, input_data)  # make a post with excel file upload
        self.assertEqual(response.status_code, 200, f"{test_name} status not 200")  # check status
        response_dct = response.json()  # taken dict from response
        self.assertEqual(response_dct['messages'], messages, msg=test_name)  # check messages with print in modal window
        rsp_sheet_names, rsp_dfs = test_read_excel(response_dct['load_to_file'].replace('file_save?file=/', ''))
        # get sheet names and dict with Data Frames from response
        ref_sheet_names, ref_dfs = test_read_excel(''.join((self.ref, reference)))
        # get sheet names and dict with Data Frames from reference (etalon)
        for name in ref_sheet_names:
            pd.testing.assert_frame_equal(rsp_dfs[name], ref_dfs[name], obj=f"{test_name}. Data Frames are different")
            # check each corresponding Data Frame

class UtilsTestCases(TestCase):
    def test_cs_fem_polygon(self):
        input_list = [{'type': 'FEM-Polygon', 'y_0': '0', 'y_1': '0', 'y_2': '10', 'y_3': '0',
                       'z_0': '0', 'z_1': '10', 'z_2': '0', 'z_3': '0', 'points': '4'}]
        result, picture = cs_converter(input_list)
        res_properties = [{'type': 'FEM-Polygon', 'area': 50.0, 'Iyy': 277.78, 'Izz': 277.78, 'Iyz': -138.89, 'J': 260.92, 'phi': -135.0}]
        for k, v in res_properties[0].items():
            self.assertAlmostEqual(v, result[0][k], places=2)

    def test_cs_l_angle(self):
        input_list = [{'type': 'L-Section', 'height': '40', 'th_1': '1.0', 'width_1': '40', 'th_2': '1.0', 'alpha':
                       '10.0', 'div_y': '5.1', 'div_z': '5'}]
        result, picture = cs_converter(input_list)
        for k, v in L_SECTION[0].items():
            self.assertAlmostEqual(v, result[0][k], places=2)

    def test_cs_wrong_table_name(self):
        input_list = [{'type': 'LSection', 'height': '40', 'th_1': '1.0', 'width_1': '40', 'th_2': '1.0', 'alpha':
            '10.0', 'div_y': '5.1', 'div_z': '5'}]
        with self.assertRaises(AttributeError) as error:
            cs_converter(input_list)
        self.assertEqual(error.exception.__str__(), 'Wrong section name')


class ViewsTestCases(TestOutFile):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.path = './tests/test_input/'
        cls.ref = './tests/test_reference/'
        cls.client = Client()
        cls.url = '/stress-service/ajax/CS-calculation/'

    def test_cs_calc(self):
        input_data = {'table_name': 'L-Section', 'height': '40', 'th_1': '1.0', 'width_1': '40', 'th_2': '1.0',
                      'alpha': '10.0', 'div_y': '5.1', 'div_z': '5'}
        response = self.client.post(self.url, input_data)
        response_dct = response.json()
        df = pd.DataFrame(L_SECTION).to_html(justify='left', classes="table table-striped",
                                             float_format=lambda x: f"{x:.2f}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response_dct['messages'], 'Расчет выполнен')
        self.assertEqual(response_dct['html'], df)

    def test_cs_calc_fem_polygon_file(self):
        with open(''.join((self.path, 'L_section.csv')), 'r') as input_file:
            input_data = {'table_name': 'FEM-Polygon', 'excel_selection': 'on', 'upload': input_file}
            response = self.client.post(self.url, input_data)
        fem_polygon = [{'type': 'FEM-Polygon', 'area': 19.0, 'Iyy': 180.0, 'Izz': 180.0, 'Iyz': -106.58,
                       'J': 6.22, 'phi': -135.0}]
        df = pd.DataFrame(fem_polygon).to_html(justify='left', classes="table table-striped",
                                               float_format=lambda x: f"{x:.2f}")
        response_dct = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response_dct['messages'], 'Расчет выполнен')
        self.assertEqual(response_dct['html'], df)

    def test_cs_calc_excel_file(self):
        input_data = {'table_name': 'L-Section', 'excel_selection': 'on', 'upload': 'CrossSections_Test.xlsx'}
        self.excel_check(url=self.url, input_data=input_data, reference='L-Section.xlsx', \
                         messages='Расчет выполнен', test_name='Excel Cross-Section calculation.')

    def test_unique_id(self):
        input_data = {'id_offset': '1000', 'upload': 'Unique_ID_Test.xlsx'}
        url = '/stress-service/ajax/generator-id/'
        self.excel_check(url=url, input_data=input_data, reference='Unique_ID_Test_map.xlsx', \
                         messages='ID и карта созданы, загрузите файл', test_name='Unique ID creation.')