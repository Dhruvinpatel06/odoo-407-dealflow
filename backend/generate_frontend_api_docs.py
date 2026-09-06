"""
Generate comprehensive Frontend API reference from FastAPI OpenAPI specification.
"""
import json
from app.main import app

spec = app.openapi()
components = spec.get('components', {}).get('schemas', {})

def get_type_str(schema):
    if not schema:
        return 'any'
    if '$ref' in schema:
        ref_name = schema['$ref'].split('/')[-1]
        ref_schema = components.get(ref_name, {})
        if 'enum' in ref_schema:
            return f"enum: {ref_schema['enum']}"
        return ref_name
    t = schema.get('type')
    if t == 'array':
        items = schema.get('items', {})
        return f"List[{get_type_str(items)}]"
    if 'anyOf' in schema:
        types = [get_type_str(x) for x in schema['anyOf'] if x.get('type') != 'null']
        is_nullable = any(x.get('type') == 'null' for x in schema['anyOf'])
        res = " | ".join(types)
        return f"Optional[{res}]" if is_nullable else res
    fmt = schema.get('format')
    if fmt:
        return f"{t} ({fmt})"
    return t or 'any'

def extract_schema_fields(schema, depth=0):
    if not schema or depth > 4:
        return {}
    if '$ref' in schema:
        ref_name = schema['$ref'].split('/')[-1]
        schema = components.get(ref_name, {})
    
    if schema.get('type') == 'array':
        return [extract_schema_fields(schema.get('items', {}), depth + 1)]
    
    props = schema.get('properties', {})
    required = set(schema.get('required', []))
    fields = {}
    for name, prop in props.items():
        is_req = name in required
        typ = get_type_str(prop)
        desc = prop.get('description', '')
        
        # Check for nested schema
        nested = None
        if '$ref' in prop:
            nested_ref = prop['$ref'].split('/')[-1]
            n_schema = components.get(nested_ref, {})
            if n_schema.get('type') == 'object' or 'properties' in n_schema:
                nested = extract_schema_fields(n_schema, depth + 1)
        elif prop.get('type') == 'array' and '$ref' in prop.get('items', {}):
            nested_ref = prop['items']['$ref'].split('/')[-1]
            n_schema = components.get(nested_ref, {})
            if n_schema.get('type') == 'object' or 'properties' in n_schema:
                nested = [extract_schema_fields(n_schema, depth + 1)]
        
        fields[name] = {
            'type': typ,
            'required': is_req,
            'description': desc,
            'default': prop.get('default'),
            'nested': nested
        }
    return fields

# Group endpoints by tag
grouped = {}
for path, path_item in spec.get('paths', {}).items():
    for method, op in path_item.items():
        if method.lower() not in ['get', 'post', 'put', 'patch', 'delete']:
            continue
        tags = op.get('tags') or ['General']
        tag = tags[0]
        
        # Params
        params = []
        for p in op.get('parameters', []):
            params.append({
                'name': p.get('name'),
                'in': p.get('in'), # query or path
                'required': p.get('required', False),
                'type': get_type_str(p.get('schema', {})),
                'description': p.get('description', '')
            })
            
        # Request body
        body_fields = None
        req_body = op.get('requestBody', {})
        if req_body:
            content = req_body.get('content', {})
            json_media = content.get('application/json', {})
            schema = json_media.get('schema')
            if schema:
                body_fields = extract_schema_fields(schema)
                
        grouped.setdefault(tag, []).append({
            'method': method.upper(),
            'path': path,
            'summary': op.get('summary', ''),
            'description': op.get('description', ''),
            'params': params,
            'body': body_fields
        })

# Output markdown
lines = []
lines.append("# DealFlow360 API Reference for Frontend\n")
lines.append(f"**Base URL**: `http://127.0.0.1:8000` (API Prefix: `/api/v1`)\n")
lines.append("## Authentication Notes\n")
lines.append("- Protected endpoints require Header: `Authorization: Bearer <access_token>`")
lines.append("- Refresh token is maintained via HttpOnly cookie `refresh_token` or auth refresh endpoint.")
lines.append("- Date/time formats are ISO 8601 strings (e.g., `2026-09-06T12:00:00Z`). UUIDs are standard RFC 4122 strings.\n")

for tag in sorted(grouped.keys()):
    endpoints = grouped[tag]
    lines.append(f"\n## {tag.upper()} ({len(endpoints)} endpoints)\n")
    for ep in endpoints:
        lines.append(f"### `{ep['method']}` {ep['path']}")
        if ep['summary']:
            lines.append(f"**Summary**: {ep['summary']}")
        if ep['description']:
            lines.append(f"**Description**: {ep['description'].strip()}")
            
        # Params
        path_params = [p for p in ep['params'] if p['in'] == 'path']
        query_params = [p for p in ep['params'] if p['in'] == 'query']
        
        if path_params:
            lines.append("\n**Path Parameters**:")
            for p in path_params:
                lines.append(f"- `{p['name']}` ({p['type']}): {p['description'] or 'Resource identifier'}")
                
        if query_params:
            lines.append("\n**Query Parameters**:")
            for p in query_params:
                req_str = "Required" if p['required'] else "Optional"
                lines.append(f"- `{p['name']}` ({p['type']}, {req_str}): {p['description']}")
                
        # Body
        if ep['body'] is not None:
            lines.append("\n**Request Body (JSON)**:")
            lines.append("```json")
            lines.append(json.dumps(ep['body'], indent=2))
            lines.append("```")
        lines.append("\n---")

with open('FRONTEND_API_DOCS.md', 'w', encoding='utf-8') as f:
    f.write("\n".join(lines))

print("Successfully written FRONTEND_API_DOCS.md with", sum(len(v) for v in grouped.values()), "endpoints.")
