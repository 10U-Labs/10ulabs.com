var Analytics = (function() {
    var API_BASE_URL = 'https://api.10ulabs.com';
    var FLUSH_INTERVAL_MS = 10000;
    var MAX_BATCH_SIZE = 25;

    var sessionId = null;
    var deviceId = null;
    var sessionContext = null;
    var eventQueue = [];
    var contextSent = false;
    var flushTimer = null;

    function generateUUID() {
        var result = 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
            var r = Math.random() * 16 | 0;
            var v = c === 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
        return result;
    }

    function hashString(str) {
        var hash = 0;
        for (var i = 0; i < str.length; i++) {
            var char = str.charCodeAt(i);
            hash = ((hash << 5) - hash) + char;
            hash = hash & hash;
        }
        var result = Math.abs(hash).toString(36);
        return result;
    }

    function getCanvasFingerprint() {
        var result = '';
        try {
            var canvas = document.createElement('canvas');
            canvas.width = 200;
            canvas.height = 50;
            var ctx = canvas.getContext('2d');
            ctx.textBaseline = 'top';
            ctx.font = '14px Arial';
            ctx.fillStyle = '#f60';
            ctx.fillRect(0, 0, 100, 50);
            ctx.fillStyle = '#069';
            ctx.fillText('10U Labs Fingerprint', 2, 15);
            ctx.fillStyle = 'rgba(102, 204, 0, 0.7)';
            ctx.fillText('Canvas Test', 4, 35);
            result = hashString(canvas.toDataURL());
        } catch (e) {
            result = 'canvas_error';
        }
        return result;
    }

    function getWebGLFingerprint() {
        var result = '';
        try {
            var canvas = document.createElement('canvas');
            var gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
            if (gl) {
                var debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
                var vendor = debugInfo ? gl.getParameter(debugInfo.UNMASKED_VENDOR_WEBGL) : 'unknown';
                var renderer = debugInfo ? gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL) : 'unknown';
                var version = gl.getParameter(gl.VERSION);
                var shadingVersion = gl.getParameter(gl.SHADING_LANGUAGE_VERSION);
                result = hashString(vendor + '|' + renderer + '|' + version + '|' + shadingVersion);
            } else {
                result = 'webgl_unsupported';
            }
        } catch (e) {
            result = 'webgl_error';
        }
        return result;
    }

    function getAudioFingerprint() {
        var result = '';
        try {
            var AudioContext = window.AudioContext || window.webkitAudioContext;
            if (AudioContext) {
                var context = new AudioContext();
                var oscillator = context.createOscillator();
                var analyser = context.createAnalyser();
                var gainNode = context.createGain();
                var scriptProcessor = context.createScriptProcessor(4096, 1, 1);
                gainNode.gain.value = 0;
                oscillator.type = 'triangle';
                oscillator.frequency.setValueAtTime(10000, context.currentTime);
                oscillator.connect(analyser);
                analyser.connect(scriptProcessor);
                scriptProcessor.connect(gainNode);
                gainNode.connect(context.destination);
                oscillator.start(0);
                var bins = new Float32Array(analyser.frequencyBinCount);
                analyser.getFloatFrequencyData(bins);
                var sum = 0;
                for (var i = 0; i < bins.length; i++) {
                    sum += bins[i];
                }
                oscillator.stop();
                context.close();
                result = hashString(sum.toString());
            } else {
                result = 'audio_unsupported';
            }
        } catch (e) {
            result = 'audio_error';
        }
        return result;
    }

    function getFontsFingerprint() {
        var result = '';
        try {
            var baseFonts = ['monospace', 'sans-serif', 'serif'];
            var testFonts = [
                'Arial', 'Arial Black', 'Comic Sans MS', 'Courier New', 'Georgia',
                'Impact', 'Lucida Console', 'Lucida Sans Unicode', 'Palatino Linotype',
                'Tahoma', 'Times New Roman', 'Trebuchet MS', 'Verdana'
            ];
            var testString = 'mmmmmmmmmmlli';
            var testSize = '72px';
            var span = document.createElement('span');
            span.style.position = 'absolute';
            span.style.left = '-9999px';
            span.style.fontSize = testSize;
            span.innerHTML = testString;
            document.body.appendChild(span);
            var baseWidths = {};
            for (var i = 0; i < baseFonts.length; i++) {
                span.style.fontFamily = baseFonts[i];
                baseWidths[baseFonts[i]] = span.offsetWidth;
            }
            var detected = [];
            for (var j = 0; j < testFonts.length; j++) {
                for (var k = 0; k < baseFonts.length; k++) {
                    span.style.fontFamily = '"' + testFonts[j] + '",' + baseFonts[k];
                    if (span.offsetWidth !== baseWidths[baseFonts[k]]) {
                        detected.push(testFonts[j]);
                        break;
                    }
                }
            }
            document.body.removeChild(span);
            result = hashString(detected.join(','));
        } catch (e) {
            result = 'fonts_error';
        }
        return result;
    }

    function computeDeviceId() {
        var canvasFp = getCanvasFingerprint();
        var webglFp = getWebGLFingerprint();
        var audioFp = getAudioFingerprint();
        var fontsFp = getFontsFingerprint();
        var screenInfo = window.screen.width + 'x' + window.screen.height + 'x' + window.screen.colorDepth;
        var timezone = new Date().getTimezoneOffset();
        var language = navigator.language || navigator.userLanguage || '';
        var hardwareConcurrency = navigator.hardwareConcurrency || 0;
        var deviceMemory = navigator.deviceMemory || 0;
        var combined = [
            canvasFp, webglFp, audioFp, fontsFp,
            screenInfo, timezone, language,
            hardwareConcurrency, deviceMemory
        ].join('|');
        var result = hashString(combined);
        return result;
    }

    function getSessionContext() {
        var connection = navigator.connection || navigator.mozConnection || navigator.webkitConnection || {};
        var context = {
            user_agent: navigator.userAgent,
            referrer: document.referrer || '',
            screen_width: window.screen.width,
            screen_height: window.screen.height,
            viewport_width: window.innerWidth,
            viewport_height: window.innerHeight,
            timezone_offset: new Date().getTimezoneOffset(),
            language: navigator.language || navigator.userLanguage || '',
            page_url: window.location.href,
            hardware_concurrency: navigator.hardwareConcurrency || null,
            device_memory: navigator.deviceMemory || null,
            max_touch_points: navigator.maxTouchPoints || 0,
            color_depth: window.screen.colorDepth,
            pixel_ratio: window.devicePixelRatio || 1,
            connection_type: connection.effectiveType || null,
            downlink_speed: connection.downlink || null,
            canvas_fingerprint: getCanvasFingerprint(),
            webgl_fingerprint: getWebGLFingerprint(),
            audio_fingerprint: getAudioFingerprint(),
            fonts_fingerprint: getFontsFingerprint()
        };
        return context;
    }

    function init() {
        sessionId = generateUUID();
        deviceId = computeDeviceId();
        sessionContext = getSessionContext();
        flushTimer = setInterval(function() {
            if (eventQueue.length > 0) {
                flush();
            }
        }, FLUSH_INTERVAL_MS);
        window.addEventListener('beforeunload', function() {
            flush(true);
        });
        window.addEventListener('pagehide', function() {
            flush(true);
        });
        track('session_started', {});
    }

    function track(eventType, data) {
        var event = {
            event_type: eventType,
            timestamp: new Date().toISOString()
        };
        if (data) {
            for (var key in data) {
                if (data.hasOwnProperty(key)) {
                    event[key] = data[key];
                }
            }
        }
        eventQueue.push(event);
        if (eventQueue.length >= MAX_BATCH_SIZE) {
            flush();
        }
    }

    function flush(useBeacon) {
        if (eventQueue.length === 0) {
            return;
        }
        var eventsToSend = eventQueue.splice(0, MAX_BATCH_SIZE);
        var payload = {
            session_id: sessionId,
            device_id: deviceId,
            events: eventsToSend
        };
        if (!contextSent) {
            payload.session_context = sessionContext;
            contextSent = true;
        }
        var body = JSON.stringify(payload);
        if (useBeacon && navigator.sendBeacon) {
            navigator.sendBeacon(API_BASE_URL + '/v1/rack-designer/events', body);
        } else {
            fetch(API_BASE_URL + '/v1/rack-designer/events', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: body,
                keepalive: true
            }).catch(function() {});
        }
    }

    function getSessionId() {
        return sessionId;
    }

    function getDeviceIdValue() {
        return deviceId;
    }

    init();

    return {
        track: track,
        flush: flush,
        getSessionId: getSessionId,
        getDeviceId: getDeviceIdValue
    };
})();
