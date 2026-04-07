from django import forms
from app.Project.models import (
    JournalEntry, 
    LabourCostTracker, 
    OverheadCostTracker, 
    SubcontractorCostTracker
)
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit

class ProfitabilityBaseForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        # Tailwind classes are handled by crispy-tailwind if configured, 
        # but we can add specific ones here if needed.

class JournalEntryForm(ProfitabilityBaseForm):
    def __init__(self, *args, **kwargs):
        project = kwargs.pop('project', None)
        super().__init__(*args, **kwargs)

    class Meta:
        model = JournalEntry
        fields = ['date', 'category', 'description', 'amount', 'transaction_type']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }

class LabourCostTrackerForm(ProfitabilityBaseForm):
    class Meta:
        model = LabourCostTracker
        fields = ['labour_entity', 'date', 'amount_of_days', 'salary']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }
    
    def __init__(self, *args, **kwargs):
        project = kwargs.pop('project', None)
        super().__init__(*args, **kwargs)
        if project:
            self.fields['labour_entity'].queryset = project.labourentity_entities.all()

class SubcontractorCostTrackerForm(ProfitabilityBaseForm):
    class Meta:
        model = SubcontractorCostTracker
        fields = ['subcontractor_entity', 'date', 'reference_no', 'amount_of_days', 'rate']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        project = kwargs.pop('project', None)
        super().__init__(*args, **kwargs)
        if project:
            self.fields['subcontractor_entity'].queryset = project.subcontractorentity_entities.all()

class OverheadCostTrackerForm(ProfitabilityBaseForm):
    class Meta:
        model = OverheadCostTracker
        fields = ['overhead_entity', 'date', 'amount_of_days', 'rate']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        project = kwargs.pop('project', None)
        super().__init__(*args, **kwargs)
        if project:
            self.fields['overhead_entity'].queryset = project.overheadentity_entities.all()
