from simple_cms.contrib.translated_model.models import Language

def languages(request):
	return {
		'languages': Language.objects.get_active(),
	}