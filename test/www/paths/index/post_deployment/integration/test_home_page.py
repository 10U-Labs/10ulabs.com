def test_home_page_returns_200(home_page_response):
    assert home_page_response.status_code == 200


def test_home_page_returns_html(home_page_response):
    assert 'text/html' in home_page_response.headers.get('Content-Type', '')


def test_home_page_has_content(home_page_response):
    assert len(home_page_response.text) > 0


def test_home_page_contains_company_name(home_page_response):
    assert '10U Labs' in home_page_response.text


def test_home_page_contains_tagline(home_page_response):
    assert 'flexible computing hardware' in home_page_response.text


def test_home_page_contains_contact_section(home_page_response):
    assert 'id="contact"' in home_page_response.text


def test_home_page_contains_products_section(home_page_response):
    assert 'id="products"' in home_page_response.text


def test_home_page_contains_about_section(home_page_response):
    assert 'id="about"' in home_page_response.text


def test_home_page_contains_contact_form(home_page_response):
    assert 'Send Message' in home_page_response.text


def test_home_page_contains_cpus_card(home_page_response):
    assert 'CPUs' in home_page_response.text


def test_home_page_contains_cpu_sockets_card(home_page_response):
    assert 'CPU Sockets' in home_page_response.text


def test_home_page_contains_motherboards_card(home_page_response):
    assert 'Motherboards' in home_page_response.text


def test_home_page_contains_privacy_link(home_page_response):
    assert 'privacy.html' in home_page_response.text


def test_home_page_contains_copyright(home_page_response):
    assert 'Copyright' in home_page_response.text


def test_home_page_contains_copyright_year(home_page_response):
    assert '2025' in home_page_response.text
