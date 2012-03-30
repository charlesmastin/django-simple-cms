def action_set_active(modeladmin, request, queryset):
    queryset.update(active=True)

action_set_active.short_description = 'Make published'

def action_set_inactive(modeladmin, request, queryset):
    queryset.update(active=False)

action_set_inactive.short_description = 'Make un-published'