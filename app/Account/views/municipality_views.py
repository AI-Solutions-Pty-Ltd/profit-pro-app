from django.db.models import Q
from django.views.generic import ListView

from app.Account.forms import MunicipalityFilterForm
from app.Account.models import Municipality


class MunicipalityListView(ListView):
    model = Municipality
    template_name = "account/municipality_list.html"
    context_object_name = "municipalities"
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()
        self.form = MunicipalityFilterForm(self.request.GET)

        if self.form.is_valid():
            search_query = self.form.cleaned_data.get("search")
            province_filter = self.form.cleaned_data.get("province")
            district_filter = self.form.cleaned_data.get("district")

            if search_query:
                queryset = queryset.filter(
                    Q(province__icontains=search_query)
                    | Q(municipality_name__icontains=search_query)
                    | Q(code__icontains=search_query)
                    | Q(district__icontains=search_query)
                )
            if province_filter:
                queryset = queryset.filter(province=province_filter)
            if district_filter:
                queryset = queryset.filter(district=district_filter)

        return queryset.order_by("province", "municipality_name")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = self.form
        return context
