with open('openapi.yml', 'r') as f:
    lines = f.readlines()

new_lines = []
skip_next = False

for i, line in enumerate(lines):
    if skip_next:
        skip_next = False
        continue

    new_lines.append(line)

    current_path = None
    for j in range(i, max(0, i-10), -1):
        if lines[j].strip().startswith('/'):
            current_path = lines[j].strip().rstrip(':')
            break

    if line.strip() in ['post:', 'get:', 'delete:', 'put:']:
        if current_path and current_path not in ['/health', '/v1/echo']:
            j = i + 1
            while j < len(lines) and 'x-amazon-apigateway-api-key-required' not in lines[j]:
                new_lines.append(lines[j])
                if lines[j].strip() == '- Runners' or lines[j].strip().startswith('- Image for'):
                    new_lines.append('      x-amazon-apigateway-api-key-required: true\n')
                    break
                if 'responses:' in lines[j]:
                    break
                j += 1

            while i + 1 < len(lines) and j > i + 1:
                i += 1
                if i + 1 < len(lines):
                    skip_next = True
                    break

with open('openapi.yml', 'w') as f:
    f.writelines(new_lines)

print("Done adding API key requirements")
