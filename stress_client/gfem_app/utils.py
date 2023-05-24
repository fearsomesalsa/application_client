import datetime, re, yaml
import time
import pandas as pd
from .model import Upload
from django.db.models.query import QuerySet
from stress_client.settings import CONFIG


def time_decorate(func):
    def _wrapper(*args, **kwargs):
        _time_start = time.time()
        result = func(*args, **kwargs)
        print("function {} time  = {:.10f}".format(func.__name__, time.time() - _time_start))
        return result
    return _wrapper


def error_function(func):
    '''
    wrapper to return errors for future rendering
    '''
    def _wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            return result
        except OSError as error:
            raise OSError(error)
        except Exception as error:
            raise ValueError(f'Excel file read error. {error}')
    return _wrapper


def chunks(s: str, n: int) -> str:
    """Produce `n`-character chunks from `s`."""
    # s = s.replace('\n', '')
    for start in range(0, len(s), n):
        yield s[start:start+n]


def bdf_read_function(file: object, len_format: int) -> list:
    """
    :param file: 'GRID*    21395                          1271.30786132813850.981140136719
                  *       206.04052734375
                  CROD     154622  59      6010922 6010921
                  CHEXA    210433  91      6054226 6054234 6054235 6054224 6054541 6054549
                           6054550 6054539'
    :param len_format:
    :return:
    """
    json = list()
    _dict = dict()
    with open('./gfem_app/stress/card_config.yaml', encoding='utf-8') as f:
        card_set = set(yaml.safe_load(f).keys())  # get set with card types from dedicated tables in DB
    for line in file:
        line = line.decode('utf-8')
        if line.startswith('$') or not line or line.startswith('END'):
            continue
        elif line.startswith('*') or line.startswith(' '):
            _dict['card_str'] += line
        else:
            json.append(_dict) if _dict and _dict['type'].replace(' ', '') not in card_set \
                else None  # add dict to json from previous loop
            _type, _id, *line = [_item for _item in chunks(line, len_format)]
            _dict = {'type': _type, 'uid': int(_id), 'card_str': "".join(line)}  # create dict with type id and card_str
    json.append(_dict) if json[-1] != _dict else None  # add last dict if it was not added yet
    file.close()
    return json


def csv_reader_decarate(func):
    '''
    wrapper to read data frame from csv file
    '''
    def _wrapper(*args, **kwargs):
        if args[0]._name.endswith('xlsx'):
            result = func(*args, **kwargs)
            return result
        elif args[0]._name.endswith('csv'):
            try:
                json = pd.read_csv(args[0]).to_dict('records')
            except Exception as error:
                raise OSError(f'File {args[0]} read. {error}')
            return json
        elif args[0]._name.endswith('bdf'):
            try:
                json = bdf_read_function(args[0], 8)
            except Exception as error:
                raise OSError(f'File {args[0]} read. {error}')
            return json
    return _wrapper


@time_decorate
def extract_from_list(base_data: dict, name='positions', replace_name='position') -> list:
    json_data = list()
    for _idx, _item in enumerate(base_data):
        if type(_item[name]) == list:
            _cur_item = base_data[_idx].copy()
            _cur_item.pop(name)
            for pos in _item[name]:
                _item_dct = {replace_name: pos}
                _item_dct.update(_cur_item)
                json_data.append(_item_dct)
        else:
            json_data.append(_item)
    return json_data

@time_decorate
# @error_function
def convert_from_db(json_data: dict, file_format: str, table_name: str, easy_format=False) -> (QuerySet[Upload], pd.DataFrame.to_html):
    '''
    convert json from
    '''

    if json_data and 'positions' in json_data[0]:
        json_data = extract_from_list(json_data, name='positions')
    df = pd.DataFrame(data=json_data)
    try:
        if 'position' in df.columns:
            df_add = df.apply(lambda row: row.position['parameter'], axis=1).apply(pd.Series)
            df = pd.concat([df, df_add], axis=1).drop('position', axis=1)
    except:
        easy_format = True
    if file_format == 'excel':
        filename = convert_to_xlsx(df, table_name, easy_format)
    elif file_format == 'bdf':
        filename = convert_to_bdf(df, table_name)
    else:
        return None, df.to_html(justify='left', classes="table table-striped", max_rows=10)
    db_file = Upload.objects.create(upload=filename)
    file_out = Upload.objects.get(id=db_file.id)
    # with pd.option_context('display.max_colwidth', -1)df.set_table_attributes('class="table-style"').to_html():
    output_html = df.to_html(justify='left', classes="table table-striped", max_rows=10,
                             float_format=lambda x: f"{x:.2f}")
    return file_out, output_html


def convert_to_bdf(df: pd.DataFrame, table_name: str) -> str:
    '''
    write Data Frame to bdf file file
    return path to bdf file
    '''
    filename = f'{table_name}.bdf'
    df_to_bdf = df
    with open('./gfem_app/stress/card_config.yaml', encoding='utf-8') as f:
        card_config = yaml.safe_load(f)
    # print(card_config)
    type_column = [_name for _name in df_to_bdf.columns if _name.endswith('type')]
    with open(fr'media/{filename}', 'w') as csv_file:
        csv_file.write(f'$file created on {datetime.datetime.now()} \n')
    if len(type_column) > 0:
        for _type, df_to_bdf_group in df_to_bdf.groupby('type'):
            with open(fr'media/{filename}', 'a') as card_file:
                card_file.write(card_config[_type][0])
            df_to_bdf_group.dropna(axis=1, how='all', inplace=True)
            complex_columns = CONFIG['DATA_BASE'][table_name]['file_type']['bdf']
            if complex_columns:
                for column in complex_columns:
                    if column in df_to_bdf_group.columns:
                        idx = 's' if 'start' in column else 'e'
                        df_add = df_to_bdf_group.apply(lambda row: row[column]['parameter'], axis=1).apply(pd.Series)
                        df_add = df_add.rename(columns=lambda x: x + '_' + idx)
                        df_to_bdf_group = pd.concat([df_to_bdf_group, df_add], axis=1).drop(column, axis=1)
            with open(fr'media/{filename}', 'a') as card_file:
                [card_file.write(card_config[_type][1].format(dct=row)) for _, row in df_to_bdf_group.iterrows()]
    return filename


@error_function
def convert_to_xlsx(df: pd.DataFrame, table_name: str, easy_format: bool) -> str:
    '''
    write Data Frame to excel file (2 options: pivot tables stringer+side vs frames or simple list format in one sheet)
    return path to excel file
    '''
    filename = f'{table_name}.xlsx'
    # TODO update file name to avoid rewriting by another user
    with pd.ExcelWriter(f'media/{filename}') as tmp:
        df.dropna(axis=1, how='all', inplace=True)
        # print(df)
        if False not in [field in df.columns for field in ['frame', 'stringer', 'side']] and not easy_format:
            for _key in df.columns:
                if _key not in ['frame', 'stringer', 'side']:
                    df.pivot(columns=['frame'], index=['stringer', 'side'], values=_key).\
                        to_excel(excel_writer=tmp, sheet_name=_key)
        else:
            df.to_excel(excel_writer=tmp)
    return filename


@error_function
@csv_reader_decarate
def from_xls_to_dict(excel_file: object, ref_fields: bool, prm_dct=['all']) -> dict:
    """
   excel_file: Excel file with parameters in each sheet
   ref_fields: include ref_fields (frame/stringer position) in result dict
   prm_dict: parameters which have to be included in result dict
   return [{'frame': '10', 'stringer': '8', 'side': 'RHS', 'id': 16408200,
   'cog_x': 1450.32602, 'cog_y': -58.5324, 'cog_z: 297.8979, 'comment': 'reference information or comments'}]
   """
    xl = pd.ExcelFile(excel_file)
    sheet_names = xl.sheet_names
    sheet_names.remove('Readme') if 'Readme' in sheet_names else None
    df = {name: xl.parse(name, index_col=[1, 0]) for name in sheet_names}
    parameter_list = []
    prm_lst = sheet_names if 'all' in prm_dct else prm_dct
    for ref1, column in df[prm_lst[0]].items():
        if column.notnull().any():
            for ref2, data in column.items():
                temp_dict = dict(zip(["side", "stringer", "frame"], [*ref2] + [ref1])) if ref_fields else dict()
                temp_dict.update({name: re.sub(r'\.0$', '', str(df[name][ref1][ref2]))
                                  for name in prm_lst if pd.notna(df[name][ref1][ref2])})
                if list(temp_dict.keys()) == ["side", "stringer", "frame"] or list(temp_dict.keys()) == []:
                    pass
                else:
                    parameter_list.append(temp_dict)
    # print(parameter_list)
    return parameter_list


def recur_unpack(lst: list, return_lst=None) -> list:
    # prepare list with unpacked internal lists [[1,2,3],4,[[5,6],7]] --> [1,2,3,4,5,6,7]
    return_lst = list() if not return_lst else return_lst
    for _val in lst:
        if type(_val) == list or type(_val) == tuple:
            return_lst = recur_unpack(_val, return_lst)
        else:
            return_lst.append(_val)
    return return_lst
