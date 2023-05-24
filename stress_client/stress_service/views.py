from django.http import JsonResponse
from stress_client.settings import CONFIG
from .utils import uid_generate
import pandas as pd
from gfem_app.utils import from_xls_to_dict, convert_from_db
from .utils import cs_converter


def id_generate_view(request, *args, **kwargs):
    '''
    view to write excel file with unique id mapping and sheet with list of parameters (for future post in
    db through csv format) from excel with pivot tables
    '''
    parameters = {k: v for k, v in request.POST.dict().items() if v}
    uid_offset = int(parameters.get('id_offset', 0))
    excel_file = uid_generate(request.FILES['upload'], uid_offset)
    data = {'messages': 'ID и карта созданы, загрузите файл',
            "load_to_file": f"file_save?file={excel_file.upload.url}"}
    return JsonResponse(data=data, status=200)


def cs_calculation_view(request, *args, **kwargs):
    '''
    view for rendering Cross-Section calculation service
    '''
    parameters = {k: v for k, v in request.POST.dict().items() if v and k != '_method'}
    # print(parameters)
    if 'excel_selection' in parameters:
        if parameters['table_name'] == 'FEM-Polygon':
            # print(request.FILES)
            _dct = pd.read_csv(request.FILES['upload'], header=0).to_dict()
            lst_dct = [{f'{_k}_{_in_k}': _in_v for _k, _v in _dct.items() for _in_k, _in_v in _v.items()}]
            lst_dct[0]['points'] = len(lst_dct[0])/2
            lst_dct[0]['type'] = parameters['table_name']
            # print(lst_dct)
        else:
            lst_dct = from_xls_to_dict(request.FILES['upload'], CONFIG['DATA_BASE']['Section']['ref_fields'])
            # print(lst_dct)
        sections, picture = cs_converter(lst_dct)
    else:
        dct = {k: float(v) for k, v in parameters.items() if k not in ('table_name', 'excel_selection')}
        dct['type'] = parameters['table_name']
        # print(dct)
        sections, picture = cs_converter([dct])
    # print(picture)
    easy_format = False if 'side' and 'stringer' and 'frame' in sections[0] else True
    excel_file, html_table = convert_from_db(sections, 'excel', parameters['table_name'], easy_format=easy_format)
    data = {'messages': 'Расчет выполнен', 'html': html_table,
            "load_to_file": f"file_save?file={excel_file.upload.url}",
            'picture': picture
            }
    return JsonResponse(data, status=200)