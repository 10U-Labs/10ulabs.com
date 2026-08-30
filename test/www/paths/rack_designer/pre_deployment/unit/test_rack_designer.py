import re

from repo_utils import REPO_ROOT

RACK_DESIGNER_DIR = REPO_ROOT / "src" / "www" / "paths" / "rack_designer"
GOOGLE_ANALYTICS_ID = "G-8YJFQC2EGV"
GTAG_SCRIPT_URL = f"https://www.googletagmanager.com/gtag/js?id={GOOGLE_ANALYTICS_ID}"
GTAG_CONFIG = f"gtag('config', '{GOOGLE_ANALYTICS_ID}')"
ADSENSE_CLIENT_ID = "ca-pub-7173129895205323"
INLINE_HANDLER = re.compile(r'\son[a-z]+="([A-Za-z_$][\w$]*)\(')


class TestRackDesignerFilesExist:
    def test_index_html_exists(self):
        assert (RACK_DESIGNER_DIR / "index.html").exists()

    def test_styles_css_exists(self):
        assert (RACK_DESIGNER_DIR / "css" / "styles.css").exists()

    def test_app_js_exists(self):
        assert (RACK_DESIGNER_DIR / "js" / "app.js").exists()

    def test_analytics_js_exists(self):
        assert (RACK_DESIGNER_DIR / "js" / "analytics.js").exists()


class TestRackDesignerGoogleAnalytics:
    def test_index_html_has_gtag_script(self):
        content = (RACK_DESIGNER_DIR / "index.html").read_text()
        assert GTAG_SCRIPT_URL in content

    def test_index_html_has_gtag_config(self):
        content = (RACK_DESIGNER_DIR / "index.html").read_text()
        assert GTAG_CONFIG in content


class TestRackDesignerGoogleAdSense:
    def test_index_html_has_adsense_client(self):
        content = (RACK_DESIGNER_DIR / "index.html").read_text()
        assert ADSENSE_CLIENT_ID in content

    def test_index_html_has_adsbygoogle_script(self):
        content = (RACK_DESIGNER_DIR / "index.html").read_text()
        assert "pagead2.googlesyndication.com/pagead/js/adsbygoogle.js" in content


class TestRackDesignerHTMLStructure:
    def test_index_html_has_doctype(self):
        content = (RACK_DESIGNER_DIR / "index.html").read_text()
        assert "<!DOCTYPE html>" in content

    def test_index_html_has_html_lang(self):
        content = (RACK_DESIGNER_DIR / "index.html").read_text()
        assert '<html lang="en">' in content

    def test_index_html_has_title(self):
        content = (RACK_DESIGNER_DIR / "index.html").read_text()
        assert "<title>" in content

    def test_index_html_has_title_close_tag(self):
        content = (RACK_DESIGNER_DIR / "index.html").read_text()
        assert "</title>" in content

    def test_index_html_has_meta_charset(self):
        content = (RACK_DESIGNER_DIR / "index.html").read_text()
        assert 'charset="UTF-8"' in content

    def test_index_html_has_meta_viewport(self):
        content = (RACK_DESIGNER_DIR / "index.html").read_text()
        assert 'name="viewport"' in content

    def test_index_html_has_meta_description(self):
        content = (RACK_DESIGNER_DIR / "index.html").read_text()
        assert 'name="description"' in content

    def test_index_html_references_styles_css(self):
        content = (RACK_DESIGNER_DIR / "index.html").read_text()
        assert 'href="css/styles.css"' in content

    def test_index_html_references_app_js(self):
        content = (RACK_DESIGNER_DIR / "index.html").read_text()
        assert 'src="js/app.js"' in content

    def test_index_html_references_analytics_js(self):
        content = (RACK_DESIGNER_DIR / "index.html").read_text()
        assert 'src="js/analytics.js"' in content

    def test_index_html_has_privacy_link(self):
        content = (RACK_DESIGNER_DIR / "index.html").read_text()
        assert 'href="/privacy.html"' in content


class TestRackDesignerAnalyticsJS:
    def test_analytics_js_has_api_base_url(self):
        content = (RACK_DESIGNER_DIR / "js" / "analytics.js").read_text()
        assert "API_BASE_URL" in content

    def test_analytics_js_has_track_function(self):
        content = (RACK_DESIGNER_DIR / "js" / "analytics.js").read_text()
        assert "function track(" in content

    def test_analytics_js_has_flush_function(self):
        content = (RACK_DESIGNER_DIR / "js" / "analytics.js").read_text()
        assert "function flush(" in content

    def test_analytics_js_exports_track(self):
        content = (RACK_DESIGNER_DIR / "js" / "analytics.js").read_text()
        assert "track: track" in content

    def test_analytics_js_exports_flush(self):
        content = (RACK_DESIGNER_DIR / "js" / "analytics.js").read_text()
        assert "flush: flush" in content


class TestRackDesignerStaticAssets:
    def test_app_js_is_not_empty(self):
        content = (RACK_DESIGNER_DIR / "js" / "app.js").read_text()
        assert len(content.strip()) > 0

    def test_styles_css_is_not_empty(self):
        content = (RACK_DESIGNER_DIR / "css" / "styles.css").read_text()
        assert len(content.strip()) > 0


class TestAppJSGlobalVariables:
    def test_app_js_has_rack_height_variable(self):
        content = (RACK_DESIGNER_DIR / "js" / "app.js").read_text()
        assert "let rackHeight" in content or "var rackHeight" in content

    def test_app_js_has_rack_count_variable(self):
        content = (RACK_DESIGNER_DIR / "js" / "app.js").read_text()
        assert "let rackCount" in content or "var rackCount" in content

    def test_app_js_has_placed_parts_variable(self):
        content = (RACK_DESIGNER_DIR / "js" / "app.js").read_text()
        assert "let placedParts" in content or "var placedParts" in content

    def test_app_js_has_selected_part_id_variable(self):
        content = (RACK_DESIGNER_DIR / "js" / "app.js").read_text()
        assert "let selectedPartId" in content or "var selectedPartId" in content

    def test_app_js_has_default_colors_object(self):
        content = (RACK_DESIGNER_DIR / "js" / "app.js").read_text()
        assert "const defaultColors" in content or "var defaultColors" in content


class TestAppJSCoreFunctions:
    def test_app_js_has_init_racks_function(self):
        content = (RACK_DESIGNER_DIR / "js" / "app.js").read_text()
        assert "function initRacks(" in content

    def test_app_js_has_render_parts_function(self):
        content = (RACK_DESIGNER_DIR / "js" / "app.js").read_text()
        assert "function renderParts(" in content

    def test_app_js_has_add_part_function(self):
        content = (RACK_DESIGNER_DIR / "js" / "app.js").read_text()
        assert "function addPart(" in content

    def test_app_js_has_remove_part_function(self):
        content = (RACK_DESIGNER_DIR / "js" / "app.js").read_text()
        assert "function removePart(" in content

    def test_app_js_has_move_part_function(self):
        content = (RACK_DESIGNER_DIR / "js" / "app.js").read_text()
        assert "function movePart(" in content

    def test_app_js_has_select_part_function(self):
        content = (RACK_DESIGNER_DIR / "js" / "app.js").read_text()
        assert "function selectPart(" in content

    def test_app_js_has_deselect_part_function(self):
        content = (RACK_DESIGNER_DIR / "js" / "app.js").read_text()
        assert "function deselectPart(" in content


class TestAppJSDragAndDropFunctions:
    def test_app_js_has_handle_drag_start_function(self):
        content = (RACK_DESIGNER_DIR / "js" / "app.js").read_text()
        assert "function handleDragStart(" in content

    def test_app_js_has_handle_drag_end_function(self):
        content = (RACK_DESIGNER_DIR / "js" / "app.js").read_text()
        assert "function handleDragEnd(" in content

    def test_app_js_has_handle_drag_over_function(self):
        content = (RACK_DESIGNER_DIR / "js" / "app.js").read_text()
        assert "function handleDragOver(" in content

    def test_app_js_has_handle_drag_leave_function(self):
        content = (RACK_DESIGNER_DIR / "js" / "app.js").read_text()
        assert "function handleDragLeave(" in content

    def test_app_js_has_handle_drop_function(self):
        content = (RACK_DESIGNER_DIR / "js" / "app.js").read_text()
        assert "function handleDrop(" in content


class TestAppJSValidationFunctions:
    def test_app_js_has_can_place_part_function(self):
        content = (RACK_DESIGNER_DIR / "js" / "app.js").read_text()
        assert "function canPlacePart(" in content

    def test_app_js_has_is_valid_placement_function(self):
        content = (RACK_DESIGNER_DIR / "js" / "app.js").read_text()
        assert "function isValidPlacement(" in content

    def test_app_js_has_get_affected_slots_function(self):
        content = (RACK_DESIGNER_DIR / "js" / "app.js").read_text()
        assert "function getAffectedSlots(" in content


class TestAppJSUpdateFunctions:
    def test_app_js_has_update_part_name_function(self):
        content = (RACK_DESIGNER_DIR / "js" / "app.js").read_text()
        assert "function updatePartName(" in content

    def test_app_js_has_update_part_color_function(self):
        content = (RACK_DESIGNER_DIR / "js" / "app.js").read_text()
        assert "function updatePartColor(" in content

    def test_app_js_has_update_part_height_function(self):
        content = (RACK_DESIGNER_DIR / "js" / "app.js").read_text()
        assert "function updatePartHeight(" in content

    def test_app_js_has_update_height_function(self):
        content = (RACK_DESIGNER_DIR / "js" / "app.js").read_text()
        assert "function updateHeight(" in content

    def test_app_js_has_update_rack_count_function(self):
        content = (RACK_DESIGNER_DIR / "js" / "app.js").read_text()
        assert "function updateRackCount(" in content


class TestAppJSConfigurationFunctions:
    def test_app_js_has_get_configuration_function(self):
        content = (RACK_DESIGNER_DIR / "js" / "app.js").read_text()
        assert "function getConfiguration(" in content

    def test_app_js_has_load_configuration_function(self):
        content = (RACK_DESIGNER_DIR / "js" / "app.js").read_text()
        assert "function loadConfiguration(" in content

    def test_app_js_has_save_configuration_function(self):
        content = (RACK_DESIGNER_DIR / "js" / "app.js").read_text()
        assert "function saveConfiguration(" in content

    def test_app_js_has_load_configuration_from_url_function(self):
        content = (RACK_DESIGNER_DIR / "js" / "app.js").read_text()
        assert "function loadConfigurationFromUrl(" in content

    def test_app_js_has_show_share_modal_function(self):
        content = (RACK_DESIGNER_DIR / "js" / "app.js").read_text()
        assert "function showShareModal(" in content


class TestAppJSUtilityFunctions:
    def test_app_js_has_get_part_name_function(self):
        content = (RACK_DESIGNER_DIR / "js" / "app.js").read_text()
        assert "function getPartName(" in content

    def test_app_js_has_adjust_brightness_function(self):
        content = (RACK_DESIGNER_DIR / "js" / "app.js").read_text()
        assert "function adjustBrightness(" in content

    def test_app_js_has_reset_all_racks_function(self):
        content = (RACK_DESIGNER_DIR / "js" / "app.js").read_text()
        assert "function resetAllRacks(" in content


class TestAppJSAPIIntegration:
    def test_app_js_has_api_base_url(self):
        content = (RACK_DESIGNER_DIR / "js" / "app.js").read_text()
        assert "API_BASE_URL" in content

    def test_app_js_api_url_is_correct(self):
        content = (RACK_DESIGNER_DIR / "js" / "app.js").read_text()
        assert "https://api.10ulabs.com" in content

    def test_app_js_has_rack_configurations_endpoint(self):
        content = (RACK_DESIGNER_DIR / "js" / "app.js").read_text()
        assert "/v1/rack-configurations" in content


class TestAppJSAnalyticsIntegration:
    def test_app_js_tracks_drag_started(self):
        content = (RACK_DESIGNER_DIR / "js" / "app.js").read_text()
        assert "Analytics.track('drag_started'" in content

    def test_app_js_tracks_drag_ended(self):
        content = (RACK_DESIGNER_DIR / "js" / "app.js").read_text()
        assert "Analytics.track('drag_ended'" in content

    def test_app_js_tracks_part_added(self):
        content = (RACK_DESIGNER_DIR / "js" / "app.js").read_text()
        assert "Analytics.track('part_added'" in content

    def test_app_js_tracks_part_removed(self):
        content = (RACK_DESIGNER_DIR / "js" / "app.js").read_text()
        assert "Analytics.track('part_removed'" in content

    def test_app_js_tracks_part_moved(self):
        content = (RACK_DESIGNER_DIR / "js" / "app.js").read_text()
        assert "Analytics.track('part_moved'" in content

    def test_app_js_tracks_part_selected(self):
        content = (RACK_DESIGNER_DIR / "js" / "app.js").read_text()
        assert "Analytics.track('part_selected'" in content

    def test_app_js_tracks_configuration_saved(self):
        content = (RACK_DESIGNER_DIR / "js" / "app.js").read_text()
        assert "Analytics.track('configuration_saved'" in content

    def test_app_js_tracks_config_loaded(self):
        content = (RACK_DESIGNER_DIR / "js" / "app.js").read_text()
        assert "Analytics.track('config_loaded'" in content


class TestAppJSDefaultColors:
    def test_app_js_has_server_color(self):
        content = (RACK_DESIGNER_DIR / "js" / "app.js").read_text()
        assert "'server':" in content

    def test_app_js_has_switch_color(self):
        content = (RACK_DESIGNER_DIR / "js" / "app.js").read_text()
        assert "'switch':" in content

    def test_app_js_has_ups_color(self):
        content = (RACK_DESIGNER_DIR / "js" / "app.js").read_text()
        assert "'ups':" in content

    def test_app_js_has_pdu_color(self):
        content = (RACK_DESIGNER_DIR / "js" / "app.js").read_text()
        assert "'pdu':" in content

    def test_app_js_has_nas_color(self):
        content = (RACK_DESIGNER_DIR / "js" / "app.js").read_text()
        assert "'nas':" in content


class TestAnalyticsJSConfiguration:
    def test_analytics_js_has_flush_interval(self):
        content = (RACK_DESIGNER_DIR / "js" / "analytics.js").read_text()
        assert "FLUSH_INTERVAL_MS" in content

    def test_analytics_js_has_max_batch_size(self):
        content = (RACK_DESIGNER_DIR / "js" / "analytics.js").read_text()
        assert "MAX_BATCH_SIZE" in content

    def test_analytics_js_has_session_id_variable(self):
        content = (RACK_DESIGNER_DIR / "js" / "analytics.js").read_text()
        assert "sessionId" in content

    def test_analytics_js_has_device_id_variable(self):
        content = (RACK_DESIGNER_DIR / "js" / "analytics.js").read_text()
        assert "deviceId" in content

    def test_analytics_js_has_event_queue_variable(self):
        content = (RACK_DESIGNER_DIR / "js" / "analytics.js").read_text()
        assert "eventQueue" in content


class TestAnalyticsJSFingerprintFunctions:
    def test_analytics_js_has_generate_uuid_function(self):
        content = (RACK_DESIGNER_DIR / "js" / "analytics.js").read_text()
        assert "function generateUUID(" in content

    def test_analytics_js_has_hash_string_function(self):
        content = (RACK_DESIGNER_DIR / "js" / "analytics.js").read_text()
        assert "function hashString(" in content

    def test_analytics_js_has_canvas_fingerprint_function(self):
        content = (RACK_DESIGNER_DIR / "js" / "analytics.js").read_text()
        assert "function getCanvasFingerprint(" in content

    def test_analytics_js_has_webgl_fingerprint_function(self):
        content = (RACK_DESIGNER_DIR / "js" / "analytics.js").read_text()
        assert "function getWebGLFingerprint(" in content

    def test_analytics_js_has_audio_fingerprint_function(self):
        content = (RACK_DESIGNER_DIR / "js" / "analytics.js").read_text()
        assert "function getAudioFingerprint(" in content

    def test_analytics_js_has_fonts_fingerprint_function(self):
        content = (RACK_DESIGNER_DIR / "js" / "analytics.js").read_text()
        assert "function getFontsFingerprint(" in content

    def test_analytics_js_has_compute_device_id_function(self):
        content = (RACK_DESIGNER_DIR / "js" / "analytics.js").read_text()
        assert "function computeDeviceId(" in content


class TestAnalyticsJSCoreFunctions:
    def test_analytics_js_has_init_function(self):
        content = (RACK_DESIGNER_DIR / "js" / "analytics.js").read_text()
        assert "function init(" in content

    def test_analytics_js_has_get_session_context_function(self):
        content = (RACK_DESIGNER_DIR / "js" / "analytics.js").read_text()
        assert "function getSessionContext(" in content

    def test_analytics_js_has_get_session_id_function(self):
        content = (RACK_DESIGNER_DIR / "js" / "analytics.js").read_text()
        assert "function getSessionId(" in content

    def test_analytics_js_has_get_device_id_value_function(self):
        content = (RACK_DESIGNER_DIR / "js" / "analytics.js").read_text()
        assert "function getDeviceIdValue(" in content


class TestAnalyticsJSExports:
    def test_analytics_js_exports_get_session_id(self):
        content = (RACK_DESIGNER_DIR / "js" / "analytics.js").read_text()
        assert "getSessionId: getSessionId" in content

    def test_analytics_js_exports_get_device_id(self):
        content = (RACK_DESIGNER_DIR / "js" / "analytics.js").read_text()
        assert "getDeviceId: getDeviceIdValue" in content


class TestAnalyticsJSAPIIntegration:
    def test_analytics_js_uses_sessions_endpoint(self):
        content = (RACK_DESIGNER_DIR / "js" / "analytics.js").read_text()
        assert "/v1/sessions/" in content

    def test_analytics_js_uses_events_endpoint(self):
        content = (RACK_DESIGNER_DIR / "js" / "analytics.js").read_text()
        assert "/events" in content


class TestAnalyticsJSEventHandling:
    def test_analytics_js_handles_beforeunload(self):
        content = (RACK_DESIGNER_DIR / "js" / "analytics.js").read_text()
        assert "'beforeunload'" in content

    def test_analytics_js_handles_pagehide(self):
        content = (RACK_DESIGNER_DIR / "js" / "analytics.js").read_text()
        assert "'pagehide'" in content

    def test_analytics_js_uses_sendbeacon(self):
        content = (RACK_DESIGNER_DIR / "js" / "analytics.js").read_text()
        assert "sendBeacon" in content

    def test_analytics_js_tracks_session_started(self):
        content = (RACK_DESIGNER_DIR / "js" / "analytics.js").read_text()
        assert "'session_started'" in content


class TestAnalyticsJSSessionContext:
    def test_analytics_js_collects_user_agent(self):
        content = (RACK_DESIGNER_DIR / "js" / "analytics.js").read_text()
        assert "user_agent:" in content

    def test_analytics_js_collects_referrer(self):
        content = (RACK_DESIGNER_DIR / "js" / "analytics.js").read_text()
        assert "referrer:" in content

    def test_analytics_js_collects_screen_width(self):
        content = (RACK_DESIGNER_DIR / "js" / "analytics.js").read_text()
        assert "screen_width:" in content

    def test_analytics_js_collects_screen_height(self):
        content = (RACK_DESIGNER_DIR / "js" / "analytics.js").read_text()
        assert "screen_height:" in content

    def test_analytics_js_collects_viewport_width(self):
        content = (RACK_DESIGNER_DIR / "js" / "analytics.js").read_text()
        assert "viewport_width:" in content

    def test_analytics_js_collects_viewport_height(self):
        content = (RACK_DESIGNER_DIR / "js" / "analytics.js").read_text()
        assert "viewport_height:" in content

    def test_analytics_js_collects_timezone(self):
        content = (RACK_DESIGNER_DIR / "js" / "analytics.js").read_text()
        assert "timezone_offset:" in content

    def test_analytics_js_collects_language(self):
        content = (RACK_DESIGNER_DIR / "js" / "analytics.js").read_text()
        assert "language:" in content


class TestRackDesignerInlineHandlers:
    def test_every_inline_handler_is_assigned_on_window(self):
        html = (RACK_DESIGNER_DIR / "index.html").read_text()
        app_js = (RACK_DESIGNER_DIR / "js" / "app.js").read_text()
        for handler in INLINE_HANDLER.findall(html):
            assert f"window.{handler} = {handler};" in app_js

    def test_index_html_has_inline_handlers_to_check(self):
        html = (RACK_DESIGNER_DIR / "index.html").read_text()
        assert INLINE_HANDLER.findall(html)
