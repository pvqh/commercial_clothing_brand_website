from django.contrib import admin


class LabelledTabularInline(admin.TabularInline):
    """Tabular inline cells have no <label>; this names every control for screen readers.

    Without it the staff edit pages fail WCAG 2.2 "form controls have labels" (Principle II).
    """

    def get_formset(self, request, obj=None, **kwargs):
        formset_class = super().get_formset(request, obj, **kwargs)

        class LabelledFormSet(formset_class):
            def add_fields(self, form, index):
                super().add_fields(form, index)
                for field in form.fields.values():
                    widget = getattr(field.widget, "widget", field.widget)
                    widget.attrs.setdefault("aria-label", str(field.label))

        return LabelledFormSet
