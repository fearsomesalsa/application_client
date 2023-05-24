from django import forms
from .model import *
import re

TYPE_FIELD = {'float': forms.FloatField, 'str': forms.CharField}

def validate_with_condition(value):
    if re.search(r"^[=><]{1,2}[ ]\w+", value) or value == '' or value == '---Select_table---' or \
            re.search(r"^[a-zA-Z0-9]+\Z", value) or \
            re.search(r"^between[ ][+-]?((\d+\.?\d*)|(\.\d+))[ ][+-]?((\d+\.?\d*)|(\.\d+))", value):
        return
    else:
        raise forms.ValidationError(
            "Запрос должен начинаться с (<, >=, <=, >, between, etc.) + пробел + значение. Либо значение без пробелов.",
            params={'value': value},
        )


class BaseDynamicForm(forms.Form):
    def __init__(self, *args, **kwargs):
        _condition = True
        for arg in args:
            if 'static_fields' in arg:
                dynamic_fields = arg.pop('static_fields')
            if 'validate' in arg:
                _condition = arg.pop('validate')
            type_fields = arg.pop('type_fields') if 'type_fields' in arg else 'str'
        validator = [validate_with_condition] if _condition else []
        super(BaseDynamicForm, self).__init__(*args, **kwargs)
        for key, val in dynamic_fields.items():
            self.fields[key] = TYPE_FIELD[type_fields](validators=validator, help_text=val, required=False)


class UploadForm(forms.ModelForm):
    class Meta:
        model = Upload
        fields = '__all__'


# class FileSaveForm(forms.Form):
#     file_type = forms.TypedChoiceField()