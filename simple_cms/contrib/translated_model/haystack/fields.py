from haystack.fields import CharField
from haystack.exceptions import SearchFieldError


from django.template import loader, Context

class MultiLanguageCharField(CharField):
    def _prepare_template(self, obj, language):
        if self.instance_name is None and self.template_name is None:
            raise SearchFieldError("This field requires either its instance_name variable to be populated or an explicit template_name in order to load the correct template.")

        if self.template_name is not None:
            template_names = self.template_name

            if not isinstance(template_names, (list, tuple)):
                template_names = [template_names]
        else:
            template_names = ['search/indexes/%s/%s_%s.txt' % (obj._meta.app_label, obj._meta.module_name, self.instance_name)]
        t = loader.select_template(template_names)
        return t.render(Context({'object': obj, 'language': language}))