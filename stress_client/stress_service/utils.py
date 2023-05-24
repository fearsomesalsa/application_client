import pandas as pd
from gfem_app.model import Upload
from django.db.models.query import QuerySet
from stress_client.settings import CONFIG
from .stress import cs_utils


def uid_generate(file: object, uid=100) -> QuerySet[Upload]:
    '''
    file object: path to excel file with typical data from database
    new_filename: sheet with new uid mapping and parameters with new uid list on sheet data
    uid: integer offset for new uid
    '''
    if file._name.endswith('xlsx'):
        xl = pd.ExcelFile(file)
        sheet_names = xl.sheet_names
        sheet_names.remove('Readme') if 'Readme' in sheet_names else None
        df = {name: xl.parse(name, index_col=[1, 0]) for name in sheet_names}
        final_dct, unique_lst = {}, []
        df_common = pd.concat([pd.DataFrame(df[index].stack(), columns=(index,)) for index in df.keys()], axis=1)
        groups = df_common.groupby(list(df_common.columns))
        df_final = pd.DataFrame()
        for name, gr in groups:
            uid += 1
            unique_lst.append(dict(zip(list(gr.columns)+['uid'], list(name) + [uid])))
            gr['uid'] = uid
            df_final = pd.concat([df_final, gr['uid']])
        df_reset_index = pd.DataFrame.from_records(df_final.index,
                                                   columns=['side', 'stringer', 'frame'], index=df_final.index)
        filename = file._name.replace('.xlsx', '_map.xlsx')
        with pd.ExcelWriter(fr'media/{filename}', mode='w') as writer:
            df_final.join(df_reset_index).pivot(columns=['frame'], index=['stringer', 'side'], values=0).\
                to_excel(excel_writer=writer, sheet_name='uid')
            pd.DataFrame.from_dict(unique_lst).to_excel(excel_writer=writer, sheet_name='data')
        db_file = Upload.objects.create(upload=filename)
        file_out = Upload.objects.get(id=db_file.id)
    return file_out


def cs_converter(db_cs_lst: list) -> list:
    """
    db_cs_lst: cross-section parameters list ([{'side': 'LHS', 'stringer': 1, 'frame': 10, 'uid': '11010110', 'type':
    'Stringer', 'section_type': 'L-Section', 'height': '40', 'th_1': '4.2', 'width': '30', 'th_2': '2.5', 'alpha':
    '0', 'coord_x': '150', 'coord_y': '45', 'coord_z': '55.1', 'comment': 'Stringer test'},])
    """
    sections = []
    for item in db_cs_lst:
        section_config = CONFIG['DATA_BASE']['Section']['dynamic_fields']['type'].get(item['type'])
        if not section_config:
            raise AttributeError('Wrong section name')
        if db_cs_lst[0]['type'] == 'FEM-Polygon':
            _points_number = int(db_cs_lst[0].pop('points'))
            dct = [(db_cs_lst[0].pop(f'y_{idx}'), db_cs_lst[0].pop(f'z_{idx}')) for idx in range(_points_number)]
        else:
            dct = {k: float(item.pop(k)) for k in list(item.keys()) if k in section_config or
                   k in CONFIG['CALCULATION_TYPE']['CROSS-SECTION']['STANDARD-PART']['Parameters']}
            # print(dct)
        # print(dct)
        SECTION = cs_utils.__dict__.get(CONFIG['VOCABULARY'][item['type']])
        if SECTION:
            section = SECTION(dct)
        else:
            raise AttributeError('Wrong section name')
        item.update(section.output)
        sections.append(item)
    picture = None if len(db_cs_lst) > 1 else section.plot
    return sections, picture