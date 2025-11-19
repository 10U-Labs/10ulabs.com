import os
import yaml


def handler(_event, _context):
    openapi_spec_path = os.path.join(os.path.dirname(__file__), '..', '..', 'openapi.yml')

    with open(openapi_spec_path, 'r', encoding='utf-8') as f:
        openapi_spec = yaml.safe_load(f)

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>10U Labs API Documentation</title>
    <link rel="stylesheet" type="text/css" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css">
    <style>
        body {{
            margin: 0;
            padding: 0;
        }}
    </style>
</head>
<body>
    <div id="swagger-ui"></div>
    <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-standalone-preset.js"></script>
    <script>
        window.onload = function() {{
            const spec = {yaml.dump(openapi_spec).replace('${DocsHandlerArn}', 'lambda-arn').replace('${HealthHandlerArn}', 'lambda-arn').replace('${EchoHandlerArn}', 'lambda-arn')};

            const ui = SwaggerUIBundle({{
                spec: spec,
                dom_id: '#swagger-ui',
                deepLinking: true,
                presets: [
                    SwaggerUIBundle.presets.apis,
                    SwaggerUIStandalonePreset
                ],
                plugins: [
                    SwaggerUIBundle.plugins.DownloadUrl
                ],
                layout: "StandaloneLayout"
            }});

            window.ui = ui;
        }};
    </script>
</body>
</html>'''

    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'text/html',
            'Access-Control-Allow-Origin': '*'
        },
        'body': html
    }
