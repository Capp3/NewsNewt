"""Pytest configuration and fixtures."""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def test_client():
    """Create a test client for the FastAPI app."""
    from newsnewt.api import app

    return TestClient(app)


@pytest.fixture
def sample_bbc_html():
    """Sample BBC article HTML for testing."""
    return """
<!DOCTYPE html>
<html>
<head>
    <title>Ukraine calls for Trump-Zelensky meeting</title>
</head>
<body>
    <article>
        <h1>Ukraine calls for Trump-Zelensky meeting before US president takes office</h1>
        <div class="article-body">
            <p>Ukraine's foreign minister has called for a meeting between President Volodymyr Zelensky 
            and US President-elect Donald Trump before he takes office in January.</p>
            <p>Andriy Sybiha told the BBC a face-to-face meeting would be "crucial" to agree a "plan 
            to achieve a just peace" between Ukraine and Russia.</p>
            <p>Trump has previously claimed he could end the war in Ukraine "in one day", although he 
            has not publicly outlined how he would do this.</p>
        </div>
    </article>
</body>
</html>
"""


@pytest.fixture
def sample_article_url():
    """Sample article URL for testing."""
    return "https://www.bbc.co.uk/news/articles/cy95jvw57v2o"
