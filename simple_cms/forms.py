from django import forms

class ArticleSearchForm(forms.Form):
    q = forms.CharField(min_length=3)
    
    def __init__(self, *args, **kwargs):
        super(ArticleSearchForm, self).__init__(*args, **kwargs)
        self.fields['q'].widget.attrs = {'class':'text', 'title':'Search by keyword...'}