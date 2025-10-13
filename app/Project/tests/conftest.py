import pytest

from app.Project.tests.factories import ClientFactory, ProjectFactory


@pytest.fixture
def project_client():
    return ClientFactory()


@pytest.fixture
def project(project_client):
    return ProjectFactory(client=project_client)
