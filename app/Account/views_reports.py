"""Dashboard and reports views for the Account app."""

from django.views.generic import TemplateView


class DashboardView(TemplateView):
    """Dashboard view showing portfolio metrics and project status."""

    template_name = "Account/dashboard.html"

    def get_context_data(self, **kwargs):
        """Add dashboard data to context."""
        context = super().get_context_data(**kwargs)

        # Stub data from the requirements
        context.update(
            {
                "report_date": "02/11/2025",
                "active_projects": 10,
                # Portfolio data
                "portfolio_data": {
                    "costs": {
                        "approved": 200000000.00,
                        "planned": 150000000.00,
                        "actual": 161100000.00,
                        "forecast": 203500000.00,
                    },
                    "schedule": {
                        "approved": 3000,
                        "planned": 2500,
                        "actual": 2385,
                        "forecast": 3076,
                    },
                    "compliance": {
                        "approved": 3000,
                        "planned": 2500,
                        "actual": 2456,
                        "forecast": 2970,
                    },
                },
                # Forecast calculations
                "forecast_variance": {
                    "costs": {
                        "amount": 3500000.00,
                        "percentage": 2,
                    },
                    "schedule": {
                        "amount": 76,
                        "percentage": 3,
                    },
                    "compliance": {
                        "amount": -30,
                        "percentage": -1,
                    },
                },
                # Performance metrics
                "performance_metrics": {
                    "progress_percentage": {
                        "costs": 81,
                        "schedule": 80,
                        "compliance": 82,
                    },
                    "performance_index": {
                        "costs": 1.1,
                        "schedule": 1.0,
                        "compliance": 0.98,
                    },
                    "overrun_savings": {
                        "costs": 7,
                        "schedule": -5,
                        "compliance": -2,
                    },
                },
                # Project status counts
                "project_status": {
                    "urgent_interventions": {
                        "costs": 4,
                        "schedule": 2,
                        "compliance": 3,
                    },
                    "requires_attention": {
                        "costs": 3,
                        "schedule": 3,
                        "compliance": 2,
                    },
                    "performing_as_planned": {
                        "costs": 3,
                        "schedule": 5,
                        "compliance": 5,
                    },
                },
                # Project status percentages
                "project_status_percentages": {
                    "urgent_interventions": {
                        "costs": 40,
                        "schedule": 20,
                        "compliance": 30,
                    },
                    "requires_attention": {
                        "costs": 30,
                        "schedule": 30,
                        "compliance": 20,
                    },
                    "performing_as_planned": {
                        "costs": 30,
                        "schedule": 50,
                        "compliance": 50,
                    },
                },
            }
        )

        return context


class CostPerformanceView(TemplateView):
    """Cost Performance report view showing detailed project cost metrics."""

    template_name = "Account/cost_performance.html"

    def get_context_data(self, **kwargs):
        """Add cost performance data to context."""
        context = super().get_context_data(**kwargs)

        # Project cost data from the requirements
        projects = [
            {
                "id": 1,
                "name": "Project 1",
                "approved_contract_amount": 20000000.00,
                "planned_cumulative_work": 15000000.00,
                "actual_cumulative_work": 18000000.00,
                "forecast_cost_at_completion": 22000000.00,
                "overrun_saving": 2000000.00,
                "percent_overrun_saving": 10,
                "actual_as_percent_approved": 90,
                "cost_performance_index": 1.20,
                "percent_variance_actual_planned": 20,
                "lead_consultant": "Consultant 1",
                "contractor": "Contractor 1",
                "status": "urgent_intervention",  # variance > 5%
            },
            {
                "id": 2,
                "name": "Project 2",
                "approved_contract_amount": 20000000.00,
                "planned_cumulative_work": 15000000.00,
                "actual_cumulative_work": 18000000.00,
                "forecast_cost_at_completion": 20500000.00,
                "overrun_saving": 500000.00,
                "percent_overrun_saving": 3,
                "actual_as_percent_approved": 90,
                "cost_performance_index": 1.20,
                "percent_variance_actual_planned": 20,
                "lead_consultant": "Consultant 2",
                "contractor": "Contractor 2",
                "status": "requires_attention",  # variance > 0% but < 5%
            },
            {
                "id": 3,
                "name": "Project 3",
                "approved_contract_amount": 20000000.00,
                "planned_cumulative_work": 15000000.00,
                "actual_cumulative_work": 15200000.00,
                "forecast_cost_at_completion": 20500000.00,
                "overrun_saving": 500000.00,
                "percent_overrun_saving": 3,
                "actual_as_percent_approved": 76,
                "cost_performance_index": 1.01,
                "percent_variance_actual_planned": 1,
                "lead_consultant": "Consultant 3",
                "contractor": "Contractor 3",
                "status": "requires_attention",  # variance > 0% but < 5%
            },
            {
                "id": 4,
                "name": "Project 4",
                "approved_contract_amount": 20000000.00,
                "planned_cumulative_work": 15000000.00,
                "actual_cumulative_work": 14500000.00,
                "forecast_cost_at_completion": 19500000.00,
                "overrun_saving": -500000.00,
                "percent_overrun_saving": -3,
                "actual_as_percent_approved": 73,
                "cost_performance_index": 0.97,
                "percent_variance_actual_planned": -3,
                "lead_consultant": "Consultant 4",
                "contractor": "Contractor 4",
                "status": "performing_as_planned",  # variance < 0%
            },
            {
                "id": 5,
                "name": "Project 5",
                "approved_contract_amount": 20000000.00,
                "planned_cumulative_work": 15000000.00,
                "actual_cumulative_work": 14500000.00,
                "forecast_cost_at_completion": 19500000.00,
                "overrun_saving": -500000.00,
                "percent_overrun_saving": -3,
                "actual_as_percent_approved": 73,
                "cost_performance_index": 0.97,
                "percent_variance_actual_planned": -3,
                "lead_consultant": "Consultant 5",
                "contractor": "Contractor 5",
                "status": "performing_as_planned",  # variance < 0%
            },
            {
                "id": 6,
                "name": "Project 6",
                "approved_contract_amount": 20000000.00,
                "planned_cumulative_work": 15000000.00,
                "actual_cumulative_work": 14500000.00,
                "forecast_cost_at_completion": 19500000.00,
                "overrun_saving": -500000.00,
                "percent_overrun_saving": -3,
                "actual_as_percent_approved": 73,
                "cost_performance_index": 0.97,
                "percent_variance_actual_planned": -3,
                "lead_consultant": "Consultant 6",
                "contractor": "Contractor 6",
                "status": "performing_as_planned",  # variance < 0%
            },
            {
                "id": 7,
                "name": "Project 7",
                "approved_contract_amount": 20000000.00,
                "planned_cumulative_work": 15000000.00,
                "actual_cumulative_work": 18000000.00,
                "forecast_cost_at_completion": 20500000.00,
                "overrun_saving": 500000.00,
                "percent_overrun_saving": 3,
                "actual_as_percent_approved": 90,
                "cost_performance_index": 1.20,
                "percent_variance_actual_planned": 20,
                "lead_consultant": "Consultant 7",
                "contractor": "Contractor 7",
                "status": "requires_attention",  # variance > 0% but < 5%
            },
            {
                "id": 8,
                "name": "Project 8",
                "approved_contract_amount": 20000000.00,
                "planned_cumulative_work": 15000000.00,
                "actual_cumulative_work": 18000000.00,
                "forecast_cost_at_completion": 20500000.00,
                "overrun_saving": 500000.00,
                "percent_overrun_saving": 3,
                "actual_as_percent_approved": 90,
                "cost_performance_index": 1.20,
                "percent_variance_actual_planned": 20,
                "lead_consultant": "Consultant 8",
                "contractor": "Contractor 8",
                "status": "requires_attention",  # variance > 0% but < 5%
            },
            {
                "id": 9,
                "name": "Project 9",
                "approved_contract_amount": 20000000.00,
                "planned_cumulative_work": 15000000.00,
                "actual_cumulative_work": 15200000.00,
                "forecast_cost_at_completion": 20500000.00,
                "overrun_saving": 500000.00,
                "percent_overrun_saving": 3,
                "actual_as_percent_approved": 76,
                "cost_performance_index": 1.01,
                "percent_variance_actual_planned": 1,
                "lead_consultant": "Consultant 9",
                "contractor": "Contractor 9",
                "status": "requires_attention",  # variance > 0% but < 5%
            },
            {
                "id": 10,
                "name": "Project 10",
                "approved_contract_amount": 20000000.00,
                "planned_cumulative_work": 15000000.00,
                "actual_cumulative_work": 15200000.00,
                "forecast_cost_at_completion": 20500000.00,
                "overrun_saving": 500000.00,
                "percent_overrun_saving": 3,
                "actual_as_percent_approved": 76,
                "cost_performance_index": 1.01,
                "percent_variance_actual_planned": 1,
                "lead_consultant": "Consultant 10",
                "contractor": "Contractor 10",
                "status": "requires_attention",  # variance > 0% but < 5%
            },
        ]

        # Calculate totals
        totals = {
            "approved_contract_amount": sum(
                p["approved_contract_amount"] for p in projects
            ),
            "planned_cumulative_work": sum(
                p["planned_cumulative_work"] for p in projects
            ),
            "actual_cumulative_work": sum(
                p["actual_cumulative_work"] for p in projects
            ),
            "forecast_cost_at_completion": sum(
                p["forecast_cost_at_completion"] for p in projects
            ),
            "overrun_saving": sum(p["overrun_saving"] for p in projects),
            "percent_overrun_saving": 2,  # From requirements
            "actual_as_percent_approved": 81,  # From requirements
            "cost_performance_index": 1.07,  # From requirements
            "percent_variance_actual_planned": 7,  # From requirements
        }

        # Count projects by status
        status_counts = {
            "urgent_intervention": len(
                [p for p in projects if p["status"] == "urgent_intervention"]
            ),
            "requires_attention": len(
                [p for p in projects if p["status"] == "requires_attention"]
            ),
            "performing_as_planned": len(
                [p for p in projects if p["status"] == "performing_as_planned"]
            ),
        }

        context.update(
            {
                "report_date": "02/11/2025",
                "projects": projects,
                "totals": totals,
                "status_counts": status_counts,
            }
        )

        return context


class SchedulePerformanceView(TemplateView):
    """Schedule Performance report view showing detailed project schedule metrics."""

    template_name = "Account/schedule_performance.html"

    def get_context_data(self, **kwargs):
        """Add schedule performance data to context."""
        context = super().get_context_data(**kwargs)

        # Project schedule data from the requirements
        projects = [
            {
                "id": 1,
                "name": "Project 1",
                "approved_contract_days": 300,
                "planned_cumulative_days": 250,
                "actual_cumulative_days": 255,
                "forecast_days_at_completion": 299,
                "overrun_saving": -1,
                "percent_overrun_saving": 0,
                "actual_as_percent_approved": 85,
                "schedule_performance_index": 1.02,
                "percent_variance_actual_planned": 2,
                "lead_consultant": "Consultant 1",
                "contractor": "Contractor 1",
                "status": "requires_attention",  # variance > 0% but < 5%
            },
            {
                "id": 2,
                "name": "Project 2",
                "approved_contract_days": 300,
                "planned_cumulative_days": 250,
                "actual_cumulative_days": 230,
                "forecast_days_at_completion": 301,
                "overrun_saving": 1,
                "percent_overrun_saving": 0,
                "actual_as_percent_approved": 77,
                "schedule_performance_index": 0.92,
                "percent_variance_actual_planned": -8,
                "lead_consultant": "Consultant 2",
                "contractor": "Contractor 2",
                "status": "requires_attention",  # variance > 0% but < 5%
            },
            {
                "id": 3,
                "name": "Project 3",
                "approved_contract_days": 300,
                "planned_cumulative_days": 250,
                "actual_cumulative_days": 260,
                "forecast_days_at_completion": 350,
                "overrun_saving": 50,
                "percent_overrun_saving": 17,
                "actual_as_percent_approved": 87,
                "schedule_performance_index": 1.04,
                "percent_variance_actual_planned": 4,
                "lead_consultant": "Consultant 3",
                "contractor": "Contractor 3",
                "status": "urgent_intervention",  # variance > 5%
            },
            {
                "id": 4,
                "name": "Project 4",
                "approved_contract_days": 300,
                "planned_cumulative_days": 250,
                "actual_cumulative_days": 230,
                "forecast_days_at_completion": 295,
                "overrun_saving": -5,
                "percent_overrun_saving": -2,
                "actual_as_percent_approved": 77,
                "schedule_performance_index": 0.92,
                "percent_variance_actual_planned": -8,
                "lead_consultant": "Consultant 4",
                "contractor": "Contractor 4",
                "status": "performing_as_planned",  # variance < 0%
            },
            {
                "id": 5,
                "name": "Project 5",
                "approved_contract_days": 300,
                "planned_cumulative_days": 250,
                "actual_cumulative_days": 230,
                "forecast_days_at_completion": 295,
                "overrun_saving": -5,
                "percent_overrun_saving": -2,
                "actual_as_percent_approved": 77,
                "schedule_performance_index": 0.92,
                "percent_variance_actual_planned": -8,
                "lead_consultant": "Consultant 5",
                "contractor": "Contractor 5",
                "status": "performing_as_planned",  # variance < 0%
            },
            {
                "id": 6,
                "name": "Project 6",
                "approved_contract_days": 300,
                "planned_cumulative_days": 250,
                "actual_cumulative_days": 230,
                "forecast_days_at_completion": 295,
                "overrun_saving": -5,
                "percent_overrun_saving": -2,
                "actual_as_percent_approved": 77,
                "schedule_performance_index": 0.92,
                "percent_variance_actual_planned": -8,
                "lead_consultant": "Consultant 6",
                "contractor": "Contractor 6",
                "status": "performing_as_planned",  # variance < 0%
            },
            {
                "id": 7,
                "name": "Project 7",
                "approved_contract_days": 300,
                "planned_cumulative_days": 250,
                "actual_cumulative_days": 230,
                "forecast_days_at_completion": 295,
                "overrun_saving": -5,
                "percent_overrun_saving": -2,
                "actual_as_percent_approved": 77,
                "schedule_performance_index": 0.92,
                "percent_variance_actual_planned": -8,
                "lead_consultant": "Consultant 7",
                "contractor": "Contractor 7",
                "status": "performing_as_planned",  # variance < 0%
            },
            {
                "id": 8,
                "name": "Project 8",
                "approved_contract_days": 300,
                "planned_cumulative_days": 250,
                "actual_cumulative_days": 230,
                "forecast_days_at_completion": 295,
                "overrun_saving": -5,
                "percent_overrun_saving": -2,
                "actual_as_percent_approved": 77,
                "schedule_performance_index": 0.92,
                "percent_variance_actual_planned": -8,
                "lead_consultant": "Consultant 8",
                "contractor": "Contractor 8",
                "status": "performing_as_planned",  # variance < 0%
            },
            {
                "id": 9,
                "name": "Project 9",
                "approved_contract_days": 300,
                "planned_cumulative_days": 250,
                "actual_cumulative_days": 260,
                "forecast_days_at_completion": 350,
                "overrun_saving": 50,
                "percent_overrun_saving": 17,
                "actual_as_percent_approved": 87,
                "schedule_performance_index": 1.04,
                "percent_variance_actual_planned": 4,
                "lead_consultant": "Consultant 9",
                "contractor": "Contractor 9",
                "status": "urgent_intervention",  # variance > 5%
            },
            {
                "id": 10,
                "name": "Project 10",
                "approved_contract_days": 300,
                "planned_cumulative_days": 250,
                "actual_cumulative_days": 230,
                "forecast_days_at_completion": 301,
                "overrun_saving": 1,
                "percent_overrun_saving": 0,
                "actual_as_percent_approved": 77,
                "schedule_performance_index": 0.92,
                "percent_variance_actual_planned": -8,
                "lead_consultant": "Consultant 10",
                "contractor": "Contractor 10",
                "status": "requires_attention",  # variance > 0% but < 5%
            },
        ]

        # Calculate totals
        totals = {
            "approved_contract_days": sum(
                p["approved_contract_days"] for p in projects
            ),
            "planned_cumulative_days": sum(
                p["planned_cumulative_days"] for p in projects
            ),
            "actual_cumulative_days": sum(
                p["actual_cumulative_days"] for p in projects
            ),
            "forecast_days_at_completion": sum(
                p["forecast_days_at_completion"] for p in projects
            ),
            "overrun_saving": sum(p["overrun_saving"] for p in projects),
            "percent_overrun_saving": 3,  # From requirements
            "actual_as_percent_approved": 80,  # From requirements
            "schedule_performance_index": 0.95,  # From requirements
            "percent_variance_actual_planned": -5,  # From requirements
        }

        # Count projects by status
        status_counts = {
            "urgent_intervention": len(
                [p for p in projects if p["status"] == "urgent_intervention"]
            ),
            "requires_attention": len(
                [p for p in projects if p["status"] == "requires_attention"]
            ),
            "performing_as_planned": len(
                [p for p in projects if p["status"] == "performing_as_planned"]
            ),
        }

        context.update(
            {
                "report_date": "02/11/2025",
                "projects": projects,
                "totals": totals,
                "status_counts": status_counts,
            }
        )

        return context


class ComplianceView(TemplateView):
    """Compliance report view showing detailed project contractual compliance metrics."""

    template_name = "Account/compliance.html"

    def get_context_data(self, **kwargs):
        """Add compliance data to context."""
        context = super().get_context_data(**kwargs)

        # Project compliance data from the requirements
        projects = [
            {
                "id": 1,
                "name": "Project 1",
                "number_contractual_obligations": 300,
                "planned_completed_obligations": 250,
                "actual_completed_obligations": 230,
                "forecast_obligations_at_completion": 285,
                "unmet_obligations": -15,
                "percent_unmet_obligations": -5,
                "actual_as_percent_approved": 77,
                "contractual_performance_index": 0.92,
                "percent_variance_actual_planned": -8,
                "lead_consultant": "Consultant 1",
                "contractor": "Contractor 1",
                "status": "performing_as_planned",  # variance < 0%
            },
            {
                "id": 2,
                "name": "Project 2",
                "number_contractual_obligations": 300,
                "planned_completed_obligations": 250,
                "actual_completed_obligations": 230,
                "forecast_obligations_at_completion": 285,
                "unmet_obligations": -15,
                "percent_unmet_obligations": -5,
                "actual_as_percent_approved": 77,
                "contractual_performance_index": 0.92,
                "percent_variance_actual_planned": -8,
                "lead_consultant": "Consultant 2",
                "contractor": "Contractor 2",
                "status": "performing_as_planned",  # variance < 0%
            },
            {
                "id": 3,
                "name": "Project 3",
                "number_contractual_obligations": 300,
                "planned_completed_obligations": 250,
                "actual_completed_obligations": 252,
                "forecast_obligations_at_completion": 305,
                "unmet_obligations": 5,
                "percent_unmet_obligations": 2,
                "actual_as_percent_approved": 84,
                "contractual_performance_index": 1.01,
                "percent_variance_actual_planned": 1,
                "lead_consultant": "Consultant 3",
                "contractor": "Contractor 3",
                "status": "requires_attention",  # variance > 0% but < 5%
            },
            {
                "id": 4,
                "name": "Project 4",
                "number_contractual_obligations": 300,
                "planned_completed_obligations": 250,
                "actual_completed_obligations": 230,
                "forecast_obligations_at_completion": 285,
                "unmet_obligations": -15,
                "percent_unmet_obligations": -5,
                "actual_as_percent_approved": 77,
                "contractual_performance_index": 0.92,
                "percent_variance_actual_planned": -8,
                "lead_consultant": "Consultant 4",
                "contractor": "Contractor 4",
                "status": "performing_as_planned",  # variance < 0%
            },
            {
                "id": 5,
                "name": "Project 5",
                "number_contractual_obligations": 300,
                "planned_completed_obligations": 250,
                "actual_completed_obligations": 270,
                "forecast_obligations_at_completion": 310,
                "unmet_obligations": 10,
                "percent_unmet_obligations": 3,
                "actual_as_percent_approved": 90,
                "contractual_performance_index": 1.08,
                "percent_variance_actual_planned": 8,
                "lead_consultant": "Consultant 5",
                "contractor": "Contractor 5",
                "status": "urgent_intervention",  # variance > 5%
            },
            {
                "id": 6,
                "name": "Project 6",
                "number_contractual_obligations": 300,
                "planned_completed_obligations": 250,
                "actual_completed_obligations": 230,
                "forecast_obligations_at_completion": 285,
                "unmet_obligations": -15,
                "percent_unmet_obligations": -5,
                "actual_as_percent_approved": 77,
                "contractual_performance_index": 0.92,
                "percent_variance_actual_planned": -8,
                "lead_consultant": "Consultant 6",
                "contractor": "Contractor 6",
                "status": "performing_as_planned",  # variance < 0%
            },
            {
                "id": 7,
                "name": "Project 7",
                "number_contractual_obligations": 300,
                "planned_completed_obligations": 250,
                "actual_completed_obligations": 252,
                "forecast_obligations_at_completion": 305,
                "unmet_obligations": 5,
                "percent_unmet_obligations": 2,
                "actual_as_percent_approved": 84,
                "contractual_performance_index": 1.01,
                "percent_variance_actual_planned": 1,
                "lead_consultant": "Consultant 7",
                "contractor": "Contractor 7",
                "status": "requires_attention",  # variance > 0% but < 5%
            },
            {
                "id": 8,
                "name": "Project 8",
                "number_contractual_obligations": 300,
                "planned_completed_obligations": 250,
                "actual_completed_obligations": 230,
                "forecast_obligations_at_completion": 285,
                "unmet_obligations": -15,
                "percent_unmet_obligations": -5,
                "actual_as_percent_approved": 77,
                "contractual_performance_index": 0.92,
                "percent_variance_actual_planned": -8,
                "lead_consultant": "Consultant 8",
                "contractor": "Contractor 8",
                "status": "performing_as_planned",  # variance < 0%
            },
            {
                "id": 9,
                "name": "Project 9",
                "number_contractual_obligations": 300,
                "planned_completed_obligations": 250,
                "actual_completed_obligations": 280,
                "forecast_obligations_at_completion": 320,
                "unmet_obligations": 20,
                "percent_unmet_obligations": 7,
                "actual_as_percent_approved": 93,
                "contractual_performance_index": 1.12,
                "percent_variance_actual_planned": 12,
                "lead_consultant": "Consultant 9",
                "contractor": "Contractor 9",
                "status": "urgent_intervention",  # variance > 5%
            },
            {
                "id": 10,
                "name": "Project 10",
                "number_contractual_obligations": 300,
                "planned_completed_obligations": 250,
                "actual_completed_obligations": 252,
                "forecast_obligations_at_completion": 305,
                "unmet_obligations": 5,
                "percent_unmet_obligations": 2,
                "actual_as_percent_approved": 84,
                "contractual_performance_index": 1.01,
                "percent_variance_actual_planned": 1,
                "lead_consultant": "Consultant 10",
                "contractor": "Contractor 10",
                "status": "requires_attention",  # variance > 0% but < 5%
            },
        ]

        # Calculate totals
        totals = {
            "number_contractual_obligations": sum(
                p["number_contractual_obligations"] for p in projects
            ),
            "planned_completed_obligations": sum(
                p["planned_completed_obligations"] for p in projects
            ),
            "actual_completed_obligations": sum(
                p["actual_completed_obligations"] for p in projects
            ),
            "forecast_obligations_at_completion": sum(
                p["forecast_obligations_at_completion"] for p in projects
            ),
            "unmet_obligations": sum(p["unmet_obligations"] for p in projects),
            "percent_unmet_obligations": -1,  # From requirements
            "actual_as_percent_approved": 82,  # From requirements
            "contractual_performance_index": 0.98,  # From requirements
            "percent_variance_actual_planned": -2,  # From requirements
        }

        # Count projects by status
        status_counts = {
            "urgent_intervention": len(
                [p for p in projects if p["status"] == "urgent_intervention"]
            ),
            "requires_attention": len(
                [p for p in projects if p["status"] == "requires_attention"]
            ),
            "performing_as_planned": len(
                [p for p in projects if p["status"] == "performing_as_planned"]
            ),
        }

        context.update(
            {
                "report_date": "02/11/2025",
                "projects": projects,
                "totals": totals,
                "status_counts": status_counts,
            }
        )

        return context
