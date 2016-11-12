import pytest
from _pytest.monkeypatch import monkeypatch


@pytest.fixture(scope="session")
def monkeypatch_session(request):
    mp = monkeypatch(request)
    request.addfinalizer(mp.undo)
    return mp


@pytest.fixture(scope='session')
def aws_config(monkeypatch_session):
    monkeypatch_session.setenv('AWS_DEFAULT_REGION', 'us-east-1')
    monkeypatch_session.setenv('AWS_ACCESS_KEY_ID', 'AKIAIOSFODNN7EXAMPLE')
    monkeypatch_session.setenv(
        'AWS_SECRET_ACCESS_KEY',
        'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY'
    )
