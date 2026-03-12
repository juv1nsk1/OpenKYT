import os
import dotenv
import json
from typing import List, Dict, Any
from ollama import AsyncClient
from config import system_instruction
from history import get_history, save_history
from tools import check_address_forensics

dotenv.load_dotenv()

async def run_analysis(user_input: str, session_id: str):
    tools_map = {
        'check_address_forensics': check_address_forensics
    }

    client = AsyncClient(host=os.getenv("OLLAMA_HOST"))
    
    history: List[Dict[str, Any]] = get_history(session_id)
    if not history:
        history.append({'role': 'system', 'content': system_instruction})
    history.append({'role': 'user', 'content': user_input})      

    yield f"data: {json.dumps({'status': 'Thinking...', 'type': 'info'})}\n\n"

    response = await client.chat(
        model='llama3.1:8b',
        messages=history,
        tools=[{
            'type': 'function',
            'function': {
                'name': 'check_address_forensics',
                'description': 'Check Risk Score of an address',
                'parameters': {
                    'type': 'object',
                    'properties': {'address': {'type': 'string'}},
                    'required': ['address']
                }
            }
        }]
    )

    if response.get('message', {}).get('tool_calls'):
        for tool in response['message']['tool_calls']:
            name = tool['function']['name']
            args = tool['function']['arguments']
            
            if isinstance(args, dict) and 'object' in args:
                args = args['object']
            if isinstance(args, dict) and 'properties' in args:
                args = args['properties']

            yield f"data: {json.dumps({'status': f'Querying Cryosphere for {args.get("address")}...', 'type': 'tool'})}\n\n"
            
            result = await tools_map[name](**args)
            
            history.append(response['message'])
            history.append({'role': 'tool', 'content': str(result), 'name': name})

    yield f"data: {json.dumps({'status': 'Generating Forensic Report...', 'type': 'info'})}\n\n"
    yield f"data: {json.dumps({'token': '\n\n', 'type': 'text'})}\n\n"
    
    full_response_content = ""

    async for chunk in await client.chat(model='llama3.1:8b', messages=history, stream=True):
        token = chunk['message']['content']
        if token:
            full_response_content += token
            yield f"data: {json.dumps({'token': token, 'type': 'text'})}\n\n"
            

    history.append({'role': 'assistant', 'content': full_response_content})
    save_history(session_id, history) 
