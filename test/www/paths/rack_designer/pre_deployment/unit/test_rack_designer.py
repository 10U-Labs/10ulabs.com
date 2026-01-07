"""Unit tests for rack_designer static files."""
from repo_utils import REPO_ROOT

RACK_DESIGNER_DIR = REPO_ROOT / "src" / "www" / "paths" / "rack_designer"
GOOGLE_ANALYTICS_ID = "G-8YJFQC2EGV"
GTAG_SCRIPT_URL = f"https://www.googletagmanager.com/gtag/js?id={GOOGLE_ANALYTICS_ID}"
GTAG_CONFIG = f"gtag('config', '{GOOGLE_ANALYTICS_ID}')"
ADSENSE_CLIENT_ID = "ca-pub-7173129895205323"


class TestRackDesignerFilesExist:
    """Tests for rack_designer file existence."""

    def test_index_html_exists(self):
        """Test that index.html exists in rack_designer directory."""
        assert (RACK_DESIGNER_DIR / "index.html").exists()

    def test_styles_css_exists(self):
        """Test that styles.css exists in css directory."""
        assert (RACK_DESIGNER_DIR / "css" / "styles.css").exists()

    def test_app_js_exists(self):
        """Test that app.js exists in js directory."""
        assert (RACK_DESIGNER_DIR / "js" / "app.js").exists()

    def test_analytics_js_exists(self):
        """Test that analytics.js exists in js directory."""
        assert (RACK_DESIGNER_DIR / "js" / "analytics.js").exists()


class TestRackDesignerGoogleAnalytics:
    """Tests for Google Analytics integration in rack_designer."""

    def test_index_html_has_gtag_script(self):
        """Test that index.html includes gtag script."""
        content = (RACK_DESIGNER_DIR / "index.html").read_text()
        assert GTAG_SCRIPT_URL in content

    def test_index_html_has_gtag_config(self):
        """Test that index.html includes gtag config."""
        content = (RACK_DESIGNER_DIR / "index.html").read_text()
        assert GTAG_CONFIG in content


class TestRackDesignerGoogleAdSense:
    """Tests for Google AdSense integration in rack_designer."""

    def test_index_html_has_adsense_client(self):
        """Test that index.html includes AdSense client ID."""
        content = (RACK_DESIGNER_DIR / "index.html").read_text()
        assert ADSENSE_CLIENT_ID in content

    def test_index_html_has_adsbygoogle_script(self):
        """Test that index.html includes adsbygoogle script."""
        content = (RACK_DESIGNER_DIR / "index.html").read_text()
        assert "pagead2.googlesyndication.com/pagead/js/adsbygoogle.js" in content


class TestRackDesignerHTMLStructure:
    """Tests for rack_designer HTML structure."""

    def test_index_html_has_doctype(self):
        """Test that index.html has DOCTYPE declaration."""
        content = (RACK_DESIGNER_DIR / "index.html").read_text()
        assert "<!DOCTYPE html>" in content

    def test_index_html_has_html_lang(self):
        """Test that index.html has lang attribute on html element."""
        content = (RACK_DESIGNER_DIR / "index.html").read_text()
        assert '<html lang="en">' in content

    def test_index_html_has_title(self):
        """Test that index.html has title element."""
        content = (RACK_DESIGNER_DIR / "index.html").read_text()
        assert "<title>" in content and "</title>" in content

    def test_index_html_has_meta_charset(self):
        """Test that index.html has charset meta tag."""
        content = (RACK_DESIGNER_DIR / "index.html").read_text()
        assert 'charset="UTF-8"' in content

    def test_index_html_has_meta_viewport(self):
        """Test that index.html has viewport meta tag."""
        content = (RACK_DESIGNER_DIR / "index.html").read_text()
        assert 'name="viewport"' in content

    def test_index_html_has_meta_description(self):
        """Test that index.html has description meta tag."""
        content = (RACK_DESIGNER_DIR / "index.html").read_text()
        assert 'name="description"' in content

    def test_index_html_references_styles_css(self):
        """Test that index.html references styles.css."""
        content = (RACK_DESIGNER_DIR / "index.html").read_text()
        assert 'href="css/styles.css"' in content

    def test_index_html_references_app_js(self):
        """Test that index.html references app.js."""
        content = (RACK_DESIGNER_DIR / "index.html").read_text()
        assert 'src="js/app.js"' in content

    def test_index_html_references_analytics_js(self):
        """Test that index.html references analytics.js."""
        content = (RACK_DESIGNER_DIR / "index.html").read_text()
        assert 'src="js/analytics.js"' in content


class TestRackDesignerPrivacyLink:
    """Tests for privacy notice link in rack_designer."""

    def test_index_html_has_privacy_link(self):
        """Test that index.html has privacy notice link."""
        content = (RACK_DESIGNER_DIR / "index.html").read_text()
        assert 'href="/privacy.html"' in content


class TestRackDesignerAnalyticsJS:
    """Tests for analytics.js file content."""

    def test_analytics_js_has_api_base_url(self):
        """Test that analytics.js has API base URL."""
        content = (RACK_DESIGNER_DIR / "js" / "analytics.js").read_text()
        assert "API_BASE_URL" in content

    def test_analytics_js_has_track_function(self):
        """Test that analytics.js has track function."""
        content = (RACK_DESIGNER_DIR / "js" / "analytics.js").read_text()
        assert "function track(" in content

    def test_analytics_js_has_flush_function(self):
        """Test that analytics.js has flush function."""
        content = (RACK_DESIGNER_DIR / "js" / "analytics.js").read_text()
        assert "function flush(" in content

    def test_analytics_js_exports_track(self):
        """Test that analytics.js exports track function."""
        content = (RACK_DESIGNER_DIR / "js" / "analytics.js").read_text()
        assert "track: track" in content

    def test_analytics_js_exports_flush(self):
        """Test that analytics.js exports flush function."""
        content = (RACK_DESIGNER_DIR / "js" / "analytics.js").read_text()
        assert "flush: flush" in content


class TestRackDesignerAppJS:
    """Tests for app.js file content."""

    def test_app_js_is_not_empty(self):
        """Test that app.js is not empty."""
        content = (RACK_DESIGNER_DIR / "js" / "app.js").read_text()
        assert len(content.strip()) > 0


class TestRackDesignerStylesCSS:
    """Tests for styles.css file content."""

    def test_styles_css_is_not_empty(self):
        """Test that styles.css is not empty."""
        content = (RACK_DESIGNER_DIR / "css" / "styles.css").read_text()
        assert len(content.strip()) > 0


# === Comprehensive app.js Tests ===


class TestAppJSGlobalVariables:
    """Tests for app.js global variables."""

    def test_app_js_has_rack_height_variable(self):
        """Test that app.js has rackHeight variable."""
        content = (RACK_DESIGNER_DIR / "js" / "app.js").read_text()
        assert "let rackHeight" in content or "var rackHeight" in content

    def test_app_js_has_rack_count_variable(self):
        """Test that app.js has rackCount variable."""
        content = (RACK_DESIGNER_DIR / "js" / "app.js").read_text()
        assert "let rackCount" in content or "var rackCount" in content

    def test_app_js_has_placed_parts_variable(self):
        """Test that app.js has placedParts variable."""
        content = (RACK_DESIGNER_DIR / "js" / "app.js").read_text()
        assert "let placedParts" in content or "var placedParts" in content

    def test_app_js_has_selected_part_id_variable(self):
        """Test that app.js has selectedPartId variable."""
        content = (RACK_DESIGNER_DIR / "js" / "app.js").read_text()
        assert "let selectedPartId" in content or "var selectedPartId" in content

    def test_app_js_has_default_colors_object(self):
        """Test that app.js has defaultColors object."""
        content = (RACK_DESIGNER_DIR / "js" / "app.js").read_text()
        assert "const defaultColors" in content or "var defaultColors" in content


class TestAppJSCoreFunctions:
    """Tests for app.js core functions."""

    def test_app_js_has_init_racks_function(self):
        """Test that app.js has initRacks function."""
        content = (RACK_DESIGNER_DIR / "js" / "app.js").read_text()
        assert "function initRacks(" in content

    def test_app_js_has_render_parts_function(self):
        """Test that app.js has renderParts function."""
        content = (RACK_DESIGNER_DIR / "js" / "app.js").read_text()
        assert "function renderParts(" in content

    def test_app_js_has_add_part_function(self):
        """Test that app.js has addPart function."""
        content = (RACK_DESIGNER_DIR / "js" / "app.js").read_text()
        assert "function addPart(" in content

    def test_app_js_has_remove_part_function(self):
        """Test that app.js has removePart function."""
        content = (RACK_DESIGNER_DIR / "js" / "app.js").read_text()
        assert "function removePart(" in content

    def test_app_js_has_move_part_function(self):
        """Test that app.js has movePart function."""
        content = (RACK_DESIGNER_DIR / "js" / "app.js").read_text()
        assert "function movePart(" in content

    def test_app_js_has_select_part_function(self):
        """Test that app.js has selectPart function."""
        content = (RACK_DESIGNER_DIR / "js" / "app.js").read_text()
        assert "function selectPart(" in content

    def test_app_js_has_deselect_part_function(self):
        """Test that app.js has deselectPart function."""
        content = (RACK_DESIGNER_DIR / "js" / "app.js").read_text()
        assert "function deselectPart(" in content


class TestAppJSDragAndDropFunctions:
    """Tests for app.js drag and drop functions."""

    def test_app_js_has_handle_drag_start_function(self):
        """Test that app.js has handleDragStart function."""
        content = (RACK_DESIGNER_DIR / "js" / "app.js").read_text()
        assert "function handleDragStart(" in content

    def test_app_js_has_handle_drag_end_function(self):
        """Test that app.js has handleDragEnd function."""
        content = (RACK_DESIGNER_DIR / "js" / "app.js").read_text()
        assert "function handleDragEnd(" in content

    def test_app_js_has_handle_drag_over_function(self):
        """Test that app.js has handleDragOver function."""
        content = (RACK_DESIGNER_DIR / "js" / "app.js").read_text()
        assert "function handleDragOver(" in content

    def test_app_js_has_handle_drag_leave_function(self):
        """Test that app.js has handleDragLeave function."""
        content = (RACK_DESIGNER_DIR / "js" / "app.js").read_text()
        assert "function handleDragLeave(" in content

    def test_app_js_has_handle_drop_function(self):
        """Test that app.js has handleDrop function."""
        content = (RACK_DESIGNER_DIR / "js" / "app.js").read_text()
        assert "function handleDrop(" in content


class TestAppJSValidationFunctions:
    """Tests for app.js validation functions."""

    def test_app_js_has_can_place_part_function(self):
        """Test that app.js has canPlacePart function."""
        content = (RACK_DESIGNER_DIR / "js" / "app.js").read_text()
        assert "function canPlacePart(" in content

    def test_app_js_has_is_valid_placement_function(self):
        """Test that app.js has isValidPlacement function."""
        content = (RACK_DESIGNER_DIR / "js" / "app.js").read_text()
        assert "function isValidPlacement(" in content

    def test_app_js_has_get_affected_slots_function(self):
        """Test that app.js has getAffectedSlots function."""
        content = (RACK_DESIGNER_DIR / "js" / "app.js").read_text()
        assert "function getAffectedSlots(" in content


class TestAppJSUpdateFunctions:
    """Tests for app.js update functions."""

    def test_app_js_has_update_part_name_function(self):
        """Test that app.js has updatePartName function."""
        content = (RACK_DESIGNER_DIR / "js" / "app.js").read_text()
        assert "function updatePartName(" in content

    def test_app_js_has_update_part_color_function(self):
        """Test that app.js has updatePartColor function."""
        content = (RACK_DESIGNER_DIR / "js" / "app.js").read_text()
        assert "function updatePartColor(" in content

    def test_app_js_has_update_part_height_function(self):
        """Test that app.js has updatePartHeight function."""
        content = (RACK_DESIGNER_DIR / "js" / "app.js").read_text()
        assert "function updatePartHeight(" in content

    def test_app_js_has_update_height_function(self):
        """Test that app.js has updateHeight function."""
        content = (RACK_DESIGNER_DIR / "js" / "app.js").read_text()
        assert "function updateHeight(" in content

    def test_app_js_has_update_rack_count_function(self):
        """Test that app.js has updateRackCount function."""
        content = (RACK_DESIGNER_DIR / "js" / "app.js").read_text()
        assert "function updateRackCount(" in content


class TestAppJSConfigurationFunctions:
    """Tests for app.js configuration save/load functions."""

    def test_app_js_has_get_configuration_function(self):
        """Test that app.js has getConfiguration function."""
        content = (RACK_DESIGNER_DIR / "js" / "app.js").read_text()
        assert "function getConfiguration(" in content

    def test_app_js_has_load_configuration_function(self):
        """Test that app.js has loadConfiguration function."""
        content = (RACK_DESIGNER_DIR / "js" / "app.js").read_text()
        assert "function loadConfiguration(" in content

    def test_app_js_has_save_configuration_function(self):
        """Test that app.js has saveConfiguration function."""
        content = (RACK_DESIGNER_DIR / "js" / "app.js").read_text()
        assert "function saveConfiguration(" in content

    def test_app_js_has_load_configuration_from_url_function(self):
        """Test that app.js has loadConfigurationFromUrl function."""
        content = (RACK_DESIGNER_DIR / "js" / "app.js").read_text()
        assert "function loadConfigurationFromUrl(" in content

    def test_app_js_has_show_share_modal_function(self):
        """Test that app.js has showShareModal function."""
        content = (RACK_DESIGNER_DIR / "js" / "app.js").read_text()
        assert "function showShareModal(" in content


class TestAppJSUtilityFunctions:
    """Tests for app.js utility functions."""

    def test_app_js_has_get_part_name_function(self):
        """Test that app.js has getPartName function."""
        content = (RACK_DESIGNER_DIR / "js" / "app.js").read_text()
        assert "function getPartName(" in content

    def test_app_js_has_adjust_brightness_function(self):
        """Test that app.js has adjustBrightness function."""
        content = (RACK_DESIGNER_DIR / "js" / "app.js").read_text()
        assert "function adjustBrightness(" in content

    def test_app_js_has_reset_all_racks_function(self):
        """Test that app.js has resetAllRacks function."""
        content = (RACK_DESIGNER_DIR / "js" / "app.js").read_text()
        assert "function resetAllRacks(" in content


class TestAppJSAPIIntegration:
    """Tests for app.js API integration."""

    def test_app_js_has_api_base_url(self):
        """Test that app.js has API_BASE_URL constant."""
        content = (RACK_DESIGNER_DIR / "js" / "app.js").read_text()
        assert "API_BASE_URL" in content

    def test_app_js_api_url_is_correct(self):
        """Test that app.js uses correct API URL."""
        content = (RACK_DESIGNER_DIR / "js" / "app.js").read_text()
        assert "https://api.10ulabs.com" in content

    def test_app_js_has_rack_configurations_endpoint(self):
        """Test that app.js has rack-configurations endpoint."""
        content = (RACK_DESIGNER_DIR / "js" / "app.js").read_text()
        assert "/v1/rack-configurations" in content


class TestAppJSAnalyticsIntegration:
    """Tests for app.js Analytics integration."""

    def test_app_js_tracks_drag_started(self):
        """Test that app.js tracks drag_started events."""
        content = (RACK_DESIGNER_DIR / "js" / "app.js").read_text()
        assert "Analytics.track('drag_started'" in content

    def test_app_js_tracks_drag_ended(self):
        """Test that app.js tracks drag_ended events."""
        content = (RACK_DESIGNER_DIR / "js" / "app.js").read_text()
        assert "Analytics.track('drag_ended'" in content

    def test_app_js_tracks_part_added(self):
        """Test that app.js tracks part_added events."""
        content = (RACK_DESIGNER_DIR / "js" / "app.js").read_text()
        assert "Analytics.track('part_added'" in content

    def test_app_js_tracks_part_removed(self):
        """Test that app.js tracks part_removed events."""
        content = (RACK_DESIGNER_DIR / "js" / "app.js").read_text()
        assert "Analytics.track('part_removed'" in content

    def test_app_js_tracks_part_moved(self):
        """Test that app.js tracks part_moved events."""
        content = (RACK_DESIGNER_DIR / "js" / "app.js").read_text()
        assert "Analytics.track('part_moved'" in content

    def test_app_js_tracks_part_selected(self):
        """Test that app.js tracks part_selected events."""
        content = (RACK_DESIGNER_DIR / "js" / "app.js").read_text()
        assert "Analytics.track('part_selected'" in content

    def test_app_js_tracks_configuration_saved(self):
        """Test that app.js tracks configuration_saved events."""
        content = (RACK_DESIGNER_DIR / "js" / "app.js").read_text()
        assert "Analytics.track('configuration_saved'" in content

    def test_app_js_tracks_config_loaded(self):
        """Test that app.js tracks config_loaded events."""
        content = (RACK_DESIGNER_DIR / "js" / "app.js").read_text()
        assert "Analytics.track('config_loaded'" in content


class TestAppJSDefaultColors:
    """Tests for app.js default colors configuration."""

    def test_app_js_has_server_color(self):
        """Test that app.js has server color defined."""
        content = (RACK_DESIGNER_DIR / "js" / "app.js").read_text()
        assert "'server':" in content

    def test_app_js_has_switch_color(self):
        """Test that app.js has switch color defined."""
        content = (RACK_DESIGNER_DIR / "js" / "app.js").read_text()
        assert "'switch':" in content

    def test_app_js_has_ups_color(self):
        """Test that app.js has ups color defined."""
        content = (RACK_DESIGNER_DIR / "js" / "app.js").read_text()
        assert "'ups':" in content

    def test_app_js_has_pdu_color(self):
        """Test that app.js has pdu color defined."""
        content = (RACK_DESIGNER_DIR / "js" / "app.js").read_text()
        assert "'pdu':" in content

    def test_app_js_has_nas_color(self):
        """Test that app.js has nas color defined."""
        content = (RACK_DESIGNER_DIR / "js" / "app.js").read_text()
        assert "'nas':" in content


# === Comprehensive analytics.js Tests ===


class TestAnalyticsJSConfiguration:
    """Tests for analytics.js configuration."""

    def test_analytics_js_has_flush_interval(self):
        """Test that analytics.js has FLUSH_INTERVAL_MS."""
        content = (RACK_DESIGNER_DIR / "js" / "analytics.js").read_text()
        assert "FLUSH_INTERVAL_MS" in content

    def test_analytics_js_has_max_batch_size(self):
        """Test that analytics.js has MAX_BATCH_SIZE."""
        content = (RACK_DESIGNER_DIR / "js" / "analytics.js").read_text()
        assert "MAX_BATCH_SIZE" in content

    def test_analytics_js_has_session_id_variable(self):
        """Test that analytics.js has sessionId variable."""
        content = (RACK_DESIGNER_DIR / "js" / "analytics.js").read_text()
        assert "sessionId" in content

    def test_analytics_js_has_device_id_variable(self):
        """Test that analytics.js has deviceId variable."""
        content = (RACK_DESIGNER_DIR / "js" / "analytics.js").read_text()
        assert "deviceId" in content

    def test_analytics_js_has_event_queue_variable(self):
        """Test that analytics.js has eventQueue variable."""
        content = (RACK_DESIGNER_DIR / "js" / "analytics.js").read_text()
        assert "eventQueue" in content


class TestAnalyticsJSFingerprintFunctions:
    """Tests for analytics.js fingerprinting functions."""

    def test_analytics_js_has_generate_uuid_function(self):
        """Test that analytics.js has generateUUID function."""
        content = (RACK_DESIGNER_DIR / "js" / "analytics.js").read_text()
        assert "function generateUUID(" in content

    def test_analytics_js_has_hash_string_function(self):
        """Test that analytics.js has hashString function."""
        content = (RACK_DESIGNER_DIR / "js" / "analytics.js").read_text()
        assert "function hashString(" in content

    def test_analytics_js_has_canvas_fingerprint_function(self):
        """Test that analytics.js has getCanvasFingerprint function."""
        content = (RACK_DESIGNER_DIR / "js" / "analytics.js").read_text()
        assert "function getCanvasFingerprint(" in content

    def test_analytics_js_has_webgl_fingerprint_function(self):
        """Test that analytics.js has getWebGLFingerprint function."""
        content = (RACK_DESIGNER_DIR / "js" / "analytics.js").read_text()
        assert "function getWebGLFingerprint(" in content

    def test_analytics_js_has_audio_fingerprint_function(self):
        """Test that analytics.js has getAudioFingerprint function."""
        content = (RACK_DESIGNER_DIR / "js" / "analytics.js").read_text()
        assert "function getAudioFingerprint(" in content

    def test_analytics_js_has_fonts_fingerprint_function(self):
        """Test that analytics.js has getFontsFingerprint function."""
        content = (RACK_DESIGNER_DIR / "js" / "analytics.js").read_text()
        assert "function getFontsFingerprint(" in content

    def test_analytics_js_has_compute_device_id_function(self):
        """Test that analytics.js has computeDeviceId function."""
        content = (RACK_DESIGNER_DIR / "js" / "analytics.js").read_text()
        assert "function computeDeviceId(" in content


class TestAnalyticsJSCoreFunctions:
    """Tests for analytics.js core functions."""

    def test_analytics_js_has_init_function(self):
        """Test that analytics.js has init function."""
        content = (RACK_DESIGNER_DIR / "js" / "analytics.js").read_text()
        assert "function init(" in content

    def test_analytics_js_has_get_session_context_function(self):
        """Test that analytics.js has getSessionContext function."""
        content = (RACK_DESIGNER_DIR / "js" / "analytics.js").read_text()
        assert "function getSessionContext(" in content

    def test_analytics_js_has_get_session_id_function(self):
        """Test that analytics.js has getSessionId function."""
        content = (RACK_DESIGNER_DIR / "js" / "analytics.js").read_text()
        assert "function getSessionId(" in content

    def test_analytics_js_has_get_device_id_value_function(self):
        """Test that analytics.js has getDeviceIdValue function."""
        content = (RACK_DESIGNER_DIR / "js" / "analytics.js").read_text()
        assert "function getDeviceIdValue(" in content


class TestAnalyticsJSExports:
    """Tests for analytics.js module exports."""

    def test_analytics_js_exports_get_session_id(self):
        """Test that analytics.js exports getSessionId."""
        content = (RACK_DESIGNER_DIR / "js" / "analytics.js").read_text()
        assert "getSessionId: getSessionId" in content

    def test_analytics_js_exports_get_device_id(self):
        """Test that analytics.js exports getDeviceId."""
        content = (RACK_DESIGNER_DIR / "js" / "analytics.js").read_text()
        assert "getDeviceId: getDeviceIdValue" in content


class TestAnalyticsJSAPIIntegration:
    """Tests for analytics.js API integration."""

    def test_analytics_js_uses_sessions_endpoint(self):
        """Test that analytics.js uses sessions endpoint."""
        content = (RACK_DESIGNER_DIR / "js" / "analytics.js").read_text()
        assert "/v1/sessions/" in content

    def test_analytics_js_uses_events_endpoint(self):
        """Test that analytics.js uses events endpoint."""
        content = (RACK_DESIGNER_DIR / "js" / "analytics.js").read_text()
        assert "/events" in content


class TestAnalyticsJSEventHandling:
    """Tests for analytics.js event handling."""

    def test_analytics_js_handles_beforeunload(self):
        """Test that analytics.js handles beforeunload event."""
        content = (RACK_DESIGNER_DIR / "js" / "analytics.js").read_text()
        assert "'beforeunload'" in content

    def test_analytics_js_handles_pagehide(self):
        """Test that analytics.js handles pagehide event."""
        content = (RACK_DESIGNER_DIR / "js" / "analytics.js").read_text()
        assert "'pagehide'" in content

    def test_analytics_js_uses_sendbeacon(self):
        """Test that analytics.js uses sendBeacon for reliable delivery."""
        content = (RACK_DESIGNER_DIR / "js" / "analytics.js").read_text()
        assert "sendBeacon" in content

    def test_analytics_js_tracks_session_started(self):
        """Test that analytics.js tracks session_started event."""
        content = (RACK_DESIGNER_DIR / "js" / "analytics.js").read_text()
        assert "'session_started'" in content


class TestAnalyticsJSSessionContext:
    """Tests for analytics.js session context."""

    def test_analytics_js_collects_user_agent(self):
        """Test that analytics.js collects user_agent."""
        content = (RACK_DESIGNER_DIR / "js" / "analytics.js").read_text()
        assert "user_agent:" in content

    def test_analytics_js_collects_referrer(self):
        """Test that analytics.js collects referrer."""
        content = (RACK_DESIGNER_DIR / "js" / "analytics.js").read_text()
        assert "referrer:" in content

    def test_analytics_js_collects_screen_width(self):
        """Test that analytics.js collects screen width."""
        content = (RACK_DESIGNER_DIR / "js" / "analytics.js").read_text()
        assert "screen_width:" in content

    def test_analytics_js_collects_screen_height(self):
        """Test that analytics.js collects screen height."""
        content = (RACK_DESIGNER_DIR / "js" / "analytics.js").read_text()
        assert "screen_height:" in content

    def test_analytics_js_collects_viewport_width(self):
        """Test that analytics.js collects viewport width."""
        content = (RACK_DESIGNER_DIR / "js" / "analytics.js").read_text()
        assert "viewport_width:" in content

    def test_analytics_js_collects_viewport_height(self):
        """Test that analytics.js collects viewport height."""
        content = (RACK_DESIGNER_DIR / "js" / "analytics.js").read_text()
        assert "viewport_height:" in content

    def test_analytics_js_collects_timezone(self):
        """Test that analytics.js collects timezone."""
        content = (RACK_DESIGNER_DIR / "js" / "analytics.js").read_text()
        assert "timezone_offset:" in content

    def test_analytics_js_collects_language(self):
        """Test that analytics.js collects language."""
        content = (RACK_DESIGNER_DIR / "js" / "analytics.js").read_text()
        assert "language:" in content
