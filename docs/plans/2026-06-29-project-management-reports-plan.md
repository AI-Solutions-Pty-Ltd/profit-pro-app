# Project Management Page Reports Integration Implementation Plan

> **For Antigravity:** REQUIRED WORKFLOW: Use `.agent/workflows/execute-plan.md` to execute this plan in single-flow mode.

**Goal:** Create functionality to select a project and view its cover page or valuation summary directly from the Project Management page.

**Architecture:** Update ProjectListView to pass all_projects in context, define ProjectCoverPageRedirectView and ProjectValuationSummaryRedirectView to resolve the correct payment certificate and redirect, and add selector controls and row action links to project_list.html.

**Tech Stack:** Python 3.13+, Django 5.2+, openpyxl, Tailwind CSS.

---

### Task 1: View Classes Implementation

**Files:**
- Modify: `app/Project/projects/project_views.py`
- Test: `app/Project/tests/test_views.py`

**Step 1: Write views code**
Append redirect views and modify context in `ProjectListView`.

```python
# In app/Project/projects/project_views.py:

    def get_context_data(self: "ProjectListView", **kwargs):
        """Add financial metrics to context."""
        context = super().get_context_data(**kwargs)
        context["filter_form"] = self.filter_form
        
        user = cast(Account, self.request.user)
        if user.is_superuser or user.is_staff:
            context["all_projects"] = Project.objects.all().order_by("-created_at")
        else:
            context["all_projects"] = user.get_projects.order_by("-created_at")
            
        return context


class ProjectCoverPageRedirectView(LoginRequiredMixin, View):
    """Finds the latest approved certificate for a project and redirects to its cover page."""
    def get(self, request, pk):
        project = get_object_or_404(Project, pk=pk)
        user = request.user
        if not (user.is_superuser or user.is_staff or project.users.filter(pk=user.pk).exists()):
            messages.error(request, "You do not have permission to access this project.")
            return redirect("project:project-list")

        cert = project.payment_certificates.filter(
            status="APPROVED"
        ).order_by("-certificate_number").first()
        
        if not cert:
            cert = project.payment_certificates.order_by("-certificate_number").first()
            
        if not cert:
            messages.error(request, "No payment certificates found for this project.")
            return redirect("project:project-list")
            
        return redirect("bill_of_quantities:payment-certificate-cover-page", project_pk=project.pk, pk=cert.pk)


class ProjectValuationSummaryRedirectView(LoginRequiredMixin, View):
    """Finds the latest approved certificate for a project and redirects to its valuation summary."""
    def get(self, request, pk):
        project = get_object_or_404(Project, pk=pk)
        user = request.user
        if not (user.is_superuser or user.is_staff or project.users.filter(pk=user.pk).exists()):
            messages.error(request, "You do not have permission to access this project.")
            return redirect("project:project-list")

        cert = project.payment_certificates.filter(
            status="APPROVED"
        ).order_by("-certificate_number").first()
        
        if not cert:
            cert = project.payment_certificates.order_by("-certificate_number").first()
            
        if not cert:
            messages.error(request, "No payment certificates found for this project.")
            return redirect("project:project-list")
            
        return redirect("bill_of_quantities:payment-certificate-valuation-summary", project_pk=project.pk, pk=cert.pk)
```

**Step 2: Commit**
Commit changes to project_views.py.

---

### Task 2: URL Routing

**Files:**
- Modify: `app/Project/projects/project_urls.py`

**Step 1: Write routing code**
Register cover-page and valuation-summary redirect URL patterns.

```python
# In app/Project/projects/project_urls.py:
    path(
        "<int:pk>/cover-page/",
        project_views.ProjectCoverPageRedirectView.as_view(),
        name="project-cover-page-redirect",
    ),
    path(
        "<int:pk>/valuation-summary/",
        project_views.ProjectValuationSummaryRedirectView.as_view(),
        name="project-valuation-summary-redirect",
    ),
```

**Step 2: Commit**
Commit changes to project_urls.py.

---

### Task 3: Template Integration

**Files:**
- Modify: `app/Project/templates/project/project_list.html`

**Step 1: Write select bar and actions code**
Add selector dropdown bar at the top of the Projects List header, and add Quick actions for Cover Page / Valuation Summary on each project row.

```html
<!-- Selector element in project_list.html: -->
        <div class="px-6 py-4 border-b border-gray-200 bg-gray-50/50">
            <div class="flex flex-col sm:flex-row sm:items-center gap-3">
                <label for="project-select" class="text-sm font-semibold text-gray-700">Quick View Project Reports:</label>
                <div class="flex flex-wrap items-center gap-2">
                    <select id="project-select" class="block w-64 pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md shadow-sm">
                        <option value="">-- Select a Project --</option>
                        {% for p in all_projects %}
                            <option value="{{ p.pk }}">{{ p.name }}</option>
                        {% endfor %}
                    </select>
                    <button id="quick-cover-btn" disabled class="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-xs font-semibold rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none disabled:opacity-50 disabled:cursor-not-allowed">
                        {% heroicon_outline "document" size="14" class="mr-1 text-indigo-600" %}
                        Cover Page
                    </button>
                    <button id="quick-valuation-btn" disabled class="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-xs font-semibold rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none disabled:opacity-50 disabled:cursor-not-allowed">
                        {% heroicon_outline "table-cells" size="14" class="mr-1 text-indigo-600" %}
                        Valuation Summary
                    </button>
                </div>
            </div>
        </div>

<!-- Row actions links in table: -->
                                    <a href="{% url 'project:project-cover-page-redirect' project.pk %}"
                                       class="inline-flex items-center px-2 py-1 text-xs font-medium text-gray-600 hover:text-indigo-600 hover:bg-indigo-50 rounded transition-colors"
                                       title="View Cover Page">
                                        {% heroicon_outline "document" size="16" %}
                                    </a>
                                    <a href="{% url 'project:project-valuation-summary-redirect' project.pk %}"
                                       class="inline-flex items-center px-2 py-1 text-xs font-medium text-gray-600 hover:text-indigo-600 hover:bg-indigo-50 rounded transition-colors"
                                       title="View Valuation Summary">
                                        {% heroicon_outline "table-cells" size="16" %}
                                    </a>
```

**Step 2: Commit**
Commit changes to project_list.html.

---

### Task 4: Unit Testing

**Files:**
- Modify: `app/Project/tests/test_views.py`

**Step 1: Write the test cases**
Add test assertions covering redirection views and correct status responses.

```python
    def test_project_cover_page_redirect_success(self, client):
        client.force_login(self.user)
        # Create certificate
        from app.BillOfQuantities.tests.factories import PaymentCertificateFactory
        cert = PaymentCertificateFactory(project=self.project, status="APPROVED")
        url = reverse("project:project-cover-page-redirect", kwargs={"pk": self.project.pk})
        response = client.get(url)
        assert response.status_code == 302
        
    def test_project_valuation_summary_redirect_success(self, client):
        client.force_login(self.user)
        from app.BillOfQuantities.tests.factories import PaymentCertificateFactory
        cert = PaymentCertificateFactory(project=self.project, status="APPROVED")
        url = reverse("project:project-valuation-summary-redirect", kwargs={"pk": self.project.pk})
        response = client.get(url)
        assert response.status_code == 302
```

**Step 2: Run verification**
Run: `.venv\Scripts\python.exe -m pytest app/Project/tests/test_views.py -v`
Expected: PASS
