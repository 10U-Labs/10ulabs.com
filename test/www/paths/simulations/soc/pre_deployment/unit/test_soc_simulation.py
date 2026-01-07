"""Unit tests for soc simulation static files."""
from repo_utils import REPO_ROOT

SOC_DIR = REPO_ROOT / "src" / "www" / "paths" / "simulations" / "soc"


# === File Existence Tests ===


class TestSocFilesExist:
    """Tests for SOC simulation file existence."""

    def test_index_html_exists(self):
        """Test that index.html exists in soc directory."""
        assert (SOC_DIR / "index.html").exists()

    def test_styles_css_exists(self):
        """Test that styles.css exists in css directory."""
        assert (SOC_DIR / "css" / "styles.css").exists()

    def test_app_js_exists(self):
        """Test that app.js exists in js directory."""
        assert (SOC_DIR / "js" / "app.js").exists()

    def test_auth_js_exists(self):
        """Test that auth.js exists in js directory."""
        assert (SOC_DIR / "js" / "auth.js").exists()

    def test_config_js_exists(self):
        """Test that config.js exists in js directory."""
        assert (SOC_DIR / "js" / "config.js").exists()


# === HTML Structure Tests ===


class TestSocHTMLStructure:
    """Tests for SOC simulation HTML structure."""

    def test_index_html_has_doctype(self):
        """Test that index.html has DOCTYPE declaration."""
        content = (SOC_DIR / "index.html").read_text()
        assert "<!DOCTYPE html>" in content

    def test_index_html_has_html_lang(self):
        """Test that index.html has lang attribute on html element."""
        content = (SOC_DIR / "index.html").read_text()
        assert '<html lang="en">' in content

    def test_index_html_has_title(self):
        """Test that index.html has title element."""
        content = (SOC_DIR / "index.html").read_text()
        assert "<title>" in content

    def test_index_html_has_closing_title(self):
        """Test that index.html has closing title element."""
        content = (SOC_DIR / "index.html").read_text()
        assert "</title>" in content

    def test_index_html_has_meta_charset(self):
        """Test that index.html has charset meta tag."""
        content = (SOC_DIR / "index.html").read_text()
        assert 'charset="UTF-8"' in content

    def test_index_html_has_meta_viewport(self):
        """Test that index.html has viewport meta tag."""
        content = (SOC_DIR / "index.html").read_text()
        assert 'name="viewport"' in content

    def test_index_html_references_styles_css(self):
        """Test that index.html references styles.css."""
        content = (SOC_DIR / "index.html").read_text()
        assert 'href="css/styles.css"' in content

    def test_index_html_references_app_js(self):
        """Test that index.html references app.js."""
        content = (SOC_DIR / "index.html").read_text()
        assert 'src="js/app.js"' in content

    def test_index_html_references_auth_js(self):
        """Test that index.html references auth.js."""
        content = (SOC_DIR / "index.html").read_text()
        assert 'src="js/auth.js"' in content

    def test_index_html_references_config_js(self):
        """Test that index.html references config.js."""
        content = (SOC_DIR / "index.html").read_text()
        assert 'src="js/config.js"' in content


class TestSocHTMLAuthentication:
    """Tests for SOC simulation authentication HTML elements."""

    def test_index_html_has_login_screen(self):
        """Test that index.html has login screen element."""
        content = (SOC_DIR / "index.html").read_text()
        assert 'id="loginScreen"' in content

    def test_index_html_has_app_content(self):
        """Test that index.html has app content element."""
        content = (SOC_DIR / "index.html").read_text()
        assert 'id="appContent"' in content

    def test_index_html_has_google_signin_button(self):
        """Test that index.html has Google sign-in button element."""
        content = (SOC_DIR / "index.html").read_text()
        assert 'id="googleSignInButton"' in content

    def test_index_html_has_user_info(self):
        """Test that index.html has user info element."""
        content = (SOC_DIR / "index.html").read_text()
        assert 'id="userInfo"' in content


class TestSocHTMLGoogleIntegration:
    """Tests for SOC simulation Google Sign-In integration."""

    def test_index_html_has_google_accounts_script(self):
        """Test that index.html includes Google accounts script."""
        content = (SOC_DIR / "index.html").read_text()
        assert "accounts.google.com/gsi/client" in content


class TestSocHTMLResultsPanels:
    """Tests for SOC simulation results panels."""

    def test_index_html_has_results_panel(self):
        """Test that index.html has results panel element."""
        content = (SOC_DIR / "index.html").read_text()
        assert 'id="resultsPanel"' in content

    def test_index_html_has_error_panel(self):
        """Test that index.html has error panel element."""
        content = (SOC_DIR / "index.html").read_text()
        assert 'id="errorPanel"' in content

    def test_index_html_has_soc_grid(self):
        """Test that index.html has SOC grid element."""
        content = (SOC_DIR / "index.html").read_text()
        assert 'id="socGrid"' in content


class TestSocHTMLConfigurationDisplay:
    """Tests for SOC simulation configuration display elements."""

    def test_index_html_has_clock_speed_element(self):
        """Test that index.html has clock speed display element."""
        content = (SOC_DIR / "index.html").read_text()
        assert 'id="clockSpeed"' in content

    def test_index_html_has_ddr_element(self):
        """Test that index.html has DDR display element."""
        content = (SOC_DIR / "index.html").read_text()
        assert 'id="ddr"' in content

    def test_index_html_has_issue_width_element(self):
        """Test that index.html has issue width display element."""
        content = (SOC_DIR / "index.html").read_text()
        assert 'id="issueWidth"' in content

    def test_index_html_has_l1_size_element(self):
        """Test that index.html has L1 size display element."""
        content = (SOC_DIR / "index.html").read_text()
        assert 'id="l1Size"' in content

    def test_index_html_has_l2_size_element(self):
        """Test that index.html has L2 size display element."""
        content = (SOC_DIR / "index.html").read_text()
        assert 'id="l2Size"' in content

    def test_index_html_has_process_node_element(self):
        """Test that index.html has process node display element."""
        content = (SOC_DIR / "index.html").read_text()
        assert 'id="processNode"' in content

    def test_index_html_has_rob_entries_element(self):
        """Test that index.html has ROB entries display element."""
        content = (SOC_DIR / "index.html").read_text()
        assert 'id="robEntries"' in content


# === config.js Tests ===


class TestConfigJSContent:
    """Tests for config.js content."""

    def test_config_js_has_google_client_id(self):
        """Test that config.js has GOOGLE_CLIENT_ID."""
        content = (SOC_DIR / "js" / "config.js").read_text()
        assert "GOOGLE_CLIENT_ID" in content

    def test_config_js_google_client_id_is_var(self):
        """Test that GOOGLE_CLIENT_ID is declared as var."""
        content = (SOC_DIR / "js" / "config.js").read_text()
        assert "var GOOGLE_CLIENT_ID" in content


# === auth.js Tests ===


class TestAuthJSStorageKeys:
    """Tests for auth.js storage key constants."""

    def test_auth_js_has_auth_storage_key(self):
        """Test that auth.js has AUTH_STORAGE_KEY."""
        content = (SOC_DIR / "js" / "auth.js").read_text()
        assert "AUTH_STORAGE_KEY" in content

    def test_auth_js_has_user_storage_key(self):
        """Test that auth.js has USER_STORAGE_KEY."""
        content = (SOC_DIR / "js" / "auth.js").read_text()
        assert "USER_STORAGE_KEY" in content


class TestAuthJSTokenFunctions:
    """Tests for auth.js token management functions."""

    def test_auth_js_has_get_stored_token_function(self):
        """Test that auth.js has getStoredToken function."""
        content = (SOC_DIR / "js" / "auth.js").read_text()
        assert "function getStoredToken(" in content

    def test_auth_js_has_store_token_function(self):
        """Test that auth.js has storeToken function."""
        content = (SOC_DIR / "js" / "auth.js").read_text()
        assert "function storeToken(" in content

    def test_auth_js_has_get_stored_user_function(self):
        """Test that auth.js has getStoredUser function."""
        content = (SOC_DIR / "js" / "auth.js").read_text()
        assert "function getStoredUser(" in content

    def test_auth_js_has_store_user_function(self):
        """Test that auth.js has storeUser function."""
        content = (SOC_DIR / "js" / "auth.js").read_text()
        assert "function storeUser(" in content

    def test_auth_js_has_clear_stored_auth_function(self):
        """Test that auth.js has clearStoredAuth function."""
        content = (SOC_DIR / "js" / "auth.js").read_text()
        assert "function clearStoredAuth(" in content

    def test_auth_js_has_get_access_token_function(self):
        """Test that auth.js has getAccessToken function."""
        content = (SOC_DIR / "js" / "auth.js").read_text()
        assert "function getAccessToken(" in content


class TestAuthJSTokenParsing:
    """Tests for auth.js token parsing functions."""

    def test_auth_js_has_parse_id_token_function(self):
        """Test that auth.js has parseIdToken function."""
        content = (SOC_DIR / "js" / "auth.js").read_text()
        assert "function parseIdToken(" in content


class TestAuthJSDisplayFunctions:
    """Tests for auth.js display management functions."""

    def test_auth_js_has_show_login_screen_function(self):
        """Test that auth.js has showLoginScreen function."""
        content = (SOC_DIR / "js" / "auth.js").read_text()
        assert "function showLoginScreen(" in content

    def test_auth_js_has_show_app_content_function(self):
        """Test that auth.js has showAppContent function."""
        content = (SOC_DIR / "js" / "auth.js").read_text()
        assert "function showAppContent(" in content

    def test_auth_js_has_update_user_display_function(self):
        """Test that auth.js has updateUserDisplay function."""
        content = (SOC_DIR / "js" / "auth.js").read_text()
        assert "function updateUserDisplay(" in content


class TestAuthJSGoogleIntegration:
    """Tests for auth.js Google Sign-In integration."""

    def test_auth_js_has_handle_credential_response_function(self):
        """Test that auth.js has handleCredentialResponse function."""
        content = (SOC_DIR / "js" / "auth.js").read_text()
        assert "function handleCredentialResponse(" in content

    def test_auth_js_has_sign_out_function(self):
        """Test that auth.js has signOut function."""
        content = (SOC_DIR / "js" / "auth.js").read_text()
        assert "function signOut(" in content

    def test_auth_js_has_init_google_sign_in_function(self):
        """Test that auth.js has initGoogleSignIn function."""
        content = (SOC_DIR / "js" / "auth.js").read_text()
        assert "function initGoogleSignIn(" in content

    def test_auth_js_has_init_auth_function(self):
        """Test that auth.js has initAuth function."""
        content = (SOC_DIR / "js" / "auth.js").read_text()
        assert "function initAuth(" in content

    def test_auth_js_has_on_google_library_load_function(self):
        """Test that auth.js has onGoogleLibraryLoad function."""
        content = (SOC_DIR / "js" / "auth.js").read_text()
        assert "function onGoogleLibraryLoad(" in content


class TestAuthJSSessionStorage:
    """Tests for auth.js session storage usage."""

    def test_auth_js_uses_session_storage_get_item(self):
        """Test that auth.js uses sessionStorage.getItem."""
        content = (SOC_DIR / "js" / "auth.js").read_text()
        assert "sessionStorage.getItem(" in content

    def test_auth_js_uses_session_storage_set_item(self):
        """Test that auth.js uses sessionStorage.setItem."""
        content = (SOC_DIR / "js" / "auth.js").read_text()
        assert "sessionStorage.setItem(" in content

    def test_auth_js_uses_session_storage_remove_item(self):
        """Test that auth.js uses sessionStorage.removeItem."""
        content = (SOC_DIR / "js" / "auth.js").read_text()
        assert "sessionStorage.removeItem(" in content


class TestAuthJSTokenExpiration:
    """Tests for auth.js token expiration handling."""

    def test_auth_js_checks_token_expiration(self):
        """Test that auth.js checks token expiration."""
        content = (SOC_DIR / "js" / "auth.js").read_text()
        assert "expires_at" in content

    def test_auth_js_uses_date_now_for_expiration(self):
        """Test that auth.js uses Date.now() for expiration check."""
        content = (SOC_DIR / "js" / "auth.js").read_text()
        assert "Date.now()" in content


class TestAuthJSGoogleAccountsAPI:
    """Tests for auth.js Google accounts API usage."""

    def test_auth_js_uses_google_accounts_id_initialize(self):
        """Test that auth.js uses google.accounts.id.initialize."""
        content = (SOC_DIR / "js" / "auth.js").read_text()
        assert "google.accounts.id.initialize(" in content

    def test_auth_js_uses_google_accounts_id_render_button(self):
        """Test that auth.js uses google.accounts.id.renderButton."""
        content = (SOC_DIR / "js" / "auth.js").read_text()
        assert "google.accounts.id.renderButton(" in content

    def test_auth_js_uses_google_accounts_id_prompt(self):
        """Test that auth.js uses google.accounts.id.prompt."""
        content = (SOC_DIR / "js" / "auth.js").read_text()
        assert "google.accounts.id.prompt(" in content

    def test_auth_js_uses_google_accounts_id_disable_auto_select(self):
        """Test that auth.js uses google.accounts.id.disableAutoSelect."""
        content = (SOC_DIR / "js" / "auth.js").read_text()
        assert "google.accounts.id.disableAutoSelect(" in content


# === app.js Tests ===


class TestAppJSGlobalVariables:
    """Tests for app.js global variables."""

    def test_app_js_has_api_base_url(self):
        """Test that app.js has API_BASE_URL."""
        content = (SOC_DIR / "js" / "app.js").read_text()
        assert "API_BASE_URL" in content

    def test_app_js_has_personas_array(self):
        """Test that app.js has PERSONAS array."""
        content = (SOC_DIR / "js" / "app.js").read_text()
        assert "PERSONAS" in content

    def test_app_js_has_persona_labels_object(self):
        """Test that app.js has PERSONA_LABELS object."""
        content = (SOC_DIR / "js" / "app.js").read_text()
        assert "PERSONA_LABELS" in content

    def test_app_js_has_soc_config_loaded_variable(self):
        """Test that app.js has socConfigLoaded variable."""
        content = (SOC_DIR / "js" / "app.js").read_text()
        assert "socConfigLoaded" in content


class TestAppJSPersonaConfiguration:
    """Tests for app.js persona configuration."""

    def test_app_js_has_desktop64_persona(self):
        """Test that app.js has desktop64 persona."""
        content = (SOC_DIR / "js" / "app.js").read_text()
        assert "'desktop64'" in content

    def test_app_js_has_mobile64_persona(self):
        """Test that app.js has mobile64 persona."""
        content = (SOC_DIR / "js" / "app.js").read_text()
        assert "'mobile64'" in content

    def test_app_js_has_riscv_persona(self):
        """Test that app.js has riscv persona."""
        content = (SOC_DIR / "js" / "app.js").read_text()
        assert "'riscv'" in content


class TestAppJSAPIConfiguration:
    """Tests for app.js API configuration."""

    def test_app_js_api_url_is_correct(self):
        """Test that app.js uses correct API URL."""
        content = (SOC_DIR / "js" / "app.js").read_text()
        assert "https://api.10ulabs.com" in content

    def test_app_js_has_soc_simulations_endpoint(self):
        """Test that app.js has soc-simulations endpoint."""
        content = (SOC_DIR / "js" / "app.js").read_text()
        assert "/v1/soc-simulations" in content


class TestAppJSUtilityFunctions:
    """Tests for app.js utility functions."""

    def test_app_js_has_get_api_base_url_function(self):
        """Test that app.js has getApiBaseUrl function."""
        content = (SOC_DIR / "js" / "app.js").read_text()
        assert "function getApiBaseUrl(" in content

    def test_app_js_has_format_number_function(self):
        """Test that app.js has formatNumber function."""
        content = (SOC_DIR / "js" / "app.js").read_text()
        assert "function formatNumber(" in content

    def test_app_js_has_format_performance_function(self):
        """Test that app.js has formatPerformance function."""
        content = (SOC_DIR / "js" / "app.js").read_text()
        assert "function formatPerformance(" in content


class TestAppJSConfigUpdateFunction:
    """Tests for app.js SOC config update function."""

    def test_app_js_has_update_soc_config_function(self):
        """Test that app.js has updateSocConfig function."""
        content = (SOC_DIR / "js" / "app.js").read_text()
        assert "function updateSocConfig(" in content


class TestAppJSCardCreationFunctions:
    """Tests for app.js card creation functions."""

    def test_app_js_has_create_soc_card_function(self):
        """Test that app.js has createSocCard function."""
        content = (SOC_DIR / "js" / "app.js").read_text()
        assert "function createSocCard(" in content

    def test_app_js_has_create_diagram_card_function(self):
        """Test that app.js has createDiagramCard function."""
        content = (SOC_DIR / "js" / "app.js").read_text()
        assert "function createDiagramCard(" in content


class TestAppJSDiagramFunctions:
    """Tests for app.js diagram creation functions."""

    def test_app_js_has_create_core_diagram_svg_function(self):
        """Test that app.js has createCoreDiagramSvg function."""
        content = (SOC_DIR / "js" / "app.js").read_text()
        assert "function createCoreDiagramSvg(" in content

    def test_app_js_has_create_non_tri_mode_diagram_function(self):
        """Test that app.js has createNonTriModeDiagram function."""
        content = (SOC_DIR / "js" / "app.js").read_text()
        assert "function createNonTriModeDiagram(" in content

    def test_app_js_has_create_tri_mode_diagrams_function(self):
        """Test that app.js has createTriModeDiagrams function."""
        content = (SOC_DIR / "js" / "app.js").read_text()
        assert "function createTriModeDiagrams(" in content


class TestAppJSResultsFunctions:
    """Tests for app.js results display functions."""

    def test_app_js_has_show_results_function(self):
        """Test that app.js has showResults function."""
        content = (SOC_DIR / "js" / "app.js").read_text()
        assert "function showResults(" in content

    def test_app_js_has_show_error_function(self):
        """Test that app.js has showError function."""
        content = (SOC_DIR / "js" / "app.js").read_text()
        assert "function showError(" in content


class TestAppJSAPIFunctions:
    """Tests for app.js API functions."""

    def test_app_js_has_fetch_simulation_function(self):
        """Test that app.js has fetchSimulation function."""
        content = (SOC_DIR / "js" / "app.js").read_text()
        assert "function fetchSimulation(" in content

    def test_app_js_has_load_all_simulations_function(self):
        """Test that app.js has loadAllSimulations function."""
        content = (SOC_DIR / "js" / "app.js").read_text()
        assert "function loadAllSimulations(" in content


class TestAppJSAuthIntegration:
    """Tests for app.js authentication integration."""

    def test_app_js_uses_get_access_token(self):
        """Test that app.js uses getAccessToken function."""
        content = (SOC_DIR / "js" / "app.js").read_text()
        assert "getAccessToken" in content

    def test_app_js_uses_clear_stored_auth(self):
        """Test that app.js uses clearStoredAuth function."""
        content = (SOC_DIR / "js" / "app.js").read_text()
        assert "clearStoredAuth" in content

    def test_app_js_sets_authorization_header(self):
        """Test that app.js sets Authorization header."""
        content = (SOC_DIR / "js" / "app.js").read_text()
        assert "'Authorization'" in content


class TestAppJSHTTP401Handling:
    """Tests for app.js HTTP 401 handling."""

    def test_app_js_checks_401_status(self):
        """Test that app.js checks for 401 status."""
        content = (SOC_DIR / "js" / "app.js").read_text()
        assert "401" in content

    def test_app_js_reloads_on_401(self):
        """Test that app.js reloads window on 401."""
        content = (SOC_DIR / "js" / "app.js").read_text()
        assert "window.location.reload()" in content


class TestAppJSLocalhostDetection:
    """Tests for app.js localhost detection."""

    def test_app_js_detects_localhost(self):
        """Test that app.js detects localhost."""
        content = (SOC_DIR / "js" / "app.js").read_text()
        assert "'localhost'" in content

    def test_app_js_detects_127_0_0_1(self):
        """Test that app.js detects 127.0.0.1."""
        content = (SOC_DIR / "js" / "app.js").read_text()
        assert "'127.0.0.1'" in content

    def test_app_js_has_localhost_api_url(self):
        """Test that app.js has localhost API URL."""
        content = (SOC_DIR / "js" / "app.js").read_text()
        assert "http://localhost:3000" in content


class TestAppJSSVGDiagram:
    """Tests for app.js SVG diagram creation."""

    def test_app_js_uses_svg_namespace(self):
        """Test that app.js uses SVG namespace."""
        content = (SOC_DIR / "js" / "app.js").read_text()
        assert "http://www.w3.org/2000/svg" in content

    def test_app_js_creates_svg_element(self):
        """Test that app.js creates SVG element."""
        content = (SOC_DIR / "js" / "app.js").read_text()
        assert "createElementNS" in content

    def test_app_js_creates_rect_elements(self):
        """Test that app.js creates rect elements for blocks."""
        content = (SOC_DIR / "js" / "app.js").read_text()
        assert "'rect'" in content

    def test_app_js_creates_text_elements(self):
        """Test that app.js creates text elements for labels."""
        content = (SOC_DIR / "js" / "app.js").read_text()
        assert "'text'" in content

    def test_app_js_creates_path_elements(self):
        """Test that app.js creates path elements for arrows."""
        content = (SOC_DIR / "js" / "app.js").read_text()
        assert "'path'" in content


class TestAppJSPromiseHandling:
    """Tests for app.js Promise handling."""

    def test_app_js_uses_fetch(self):
        """Test that app.js uses fetch API."""
        content = (SOC_DIR / "js" / "app.js").read_text()
        assert "fetch(" in content

    def test_app_js_uses_promise_all(self):
        """Test that app.js uses Promise.all."""
        content = (SOC_DIR / "js" / "app.js").read_text()
        assert "Promise.all(" in content

    def test_app_js_uses_then(self):
        """Test that app.js uses .then() for promises."""
        content = (SOC_DIR / "js" / "app.js").read_text()
        assert ".then(" in content

    def test_app_js_uses_catch(self):
        """Test that app.js uses .catch() for error handling."""
        content = (SOC_DIR / "js" / "app.js").read_text()
        assert ".catch(" in content


# === styles.css Tests ===


class TestStylesCSSContent:
    """Tests for styles.css content."""

    def test_styles_css_is_not_empty(self):
        """Test that styles.css is not empty."""
        content = (SOC_DIR / "css" / "styles.css").read_text()
        assert len(content.strip()) > 0


class TestStylesCSSClasses:
    """Tests for styles.css CSS classes."""

    def test_styles_css_has_soc_card_class(self):
        """Test that styles.css has soc-card class."""
        content = (SOC_DIR / "css" / "styles.css").read_text()
        assert ".soc-card" in content

    def test_styles_css_has_diagram_card_class(self):
        """Test that styles.css has diagram-card class."""
        content = (SOC_DIR / "css" / "styles.css").read_text()
        assert ".diagram-card" in content

    def test_styles_css_has_login_screen_class(self):
        """Test that styles.css has login-screen class or styling."""
        content = (SOC_DIR / "css" / "styles.css").read_text()
        assert "#loginScreen" in content or ".login-" in content


class TestStylesCSSResponsive:
    """Tests for styles.css responsive design."""

    def test_styles_css_has_media_query(self):
        """Test that styles.css has media query for responsiveness."""
        content = (SOC_DIR / "css" / "styles.css").read_text()
        assert "@media" in content


# === Static Asset Tests ===


class TestSocStaticAssets:
    """Tests for SOC simulation static assets."""

    def test_app_js_is_not_empty(self):
        """Test that app.js is not empty."""
        content = (SOC_DIR / "js" / "app.js").read_text()
        assert len(content.strip()) > 0

    def test_auth_js_is_not_empty(self):
        """Test that auth.js is not empty."""
        content = (SOC_DIR / "js" / "auth.js").read_text()
        assert len(content.strip()) > 0

    def test_config_js_is_not_empty(self):
        """Test that config.js is not empty."""
        content = (SOC_DIR / "js" / "config.js").read_text()
        assert len(content.strip()) > 0
