"""One small workspace record referencing editable scenes and existing receipts.

Assets/checkpoints remain files in the production; this does not copy media,
invent render approval, or promise restoration outside this workspace.
"""
import json
from pathlib import Path

from project_state import atomic_json, digest, differences, snapshot


def default_path(scene):
    return Path(scene).resolve().parent / '.geomotion-project.json'


def read(path):
    path = Path(path).resolve()
    if not path.exists():
        return None
    data = json.loads(path.read_text())
    if data.get('version') != 1 or data.get('kind') != 'geomotion-workspace':
        raise ValueError('Unsupported project workspace record')
    if data.get('mode') not in ('preview', 'final'):
        raise ValueError('Invalid saved delivery stage')
    if data['mode'] == 'final' and not data.get('final_requested'):
        raise ValueError('Saved final stage has no recorded authorization')
    return data


def select_mode(saved, requested=None, final_requested=False, return_to_preview=False):
    mode = requested or ('final' if final_requested else (saved or {}).get('mode', 'preview'))
    if mode not in ('preview', 'final'):
        raise ValueError('Invalid delivery mode')
    if (saved or {}).get('mode') == 'final' and mode == 'preview' and not return_to_preview:
        raise ValueError('Final stage is retained; use --return-to-preview only for an explicit user stage change')
    authorized = bool(final_requested or (saved or {}).get('final_requested'))
    if mode == 'final' and not authorized:
        raise ValueError('First final request requires --final-requested')
    return mode, authorized


def save(scene, path=None, *, mode=None, final_requested=False,
         return_to_preview=False, checkpoint=None, video=None, status='saved'):
    from execution import exclusive
    scene = Path(scene).resolve()
    path = Path(path).resolve() if path else default_path(scene)
    with exclusive(path.with_suffix(path.suffix + '.lock')):
        previous = read(path)
        if previous and previous.get('scene') and Path(previous['scene']).parent != scene.parent:
            raise ValueError('Workspace record belongs to another production directory')
        selected, authorized = select_mode(previous, mode, final_requested, return_to_preview)
        current = snapshot(scene)
        history = list((previous or {}).get('history', []))
        prior = (previous or {}).get('checkpoint')
        if prior and checkpoint and Path(prior) != Path(checkpoint).resolve() and prior not in history:
            history.append(prior)
        result = {**(previous or {}), 'version': 1, 'kind': 'geomotion-workspace',
                  'scene': str(scene), 'scene_sha256': digest(scene), 'inputs': current,
                  'mode': selected, 'final_requested': authorized, 'status': status,
                  'history': history}
        result.pop('active_composite', None)
        result.pop('pending_composite', None)
        if checkpoint:
            result['checkpoint'] = str(Path(checkpoint).resolve())
        if video:
            output = Path(video).resolve()
            receipt = output.with_suffix('.render.json')
            if not output.exists() or not receipt.exists():
                raise ValueError('Saved deliverable requires a real render receipt')
            binding = json.loads(receipt.read_text())
            from project_state import fingerprint
            if binding.get('sha256') != digest(output) or binding.get('fingerprint') != fingerprint(current, selected):
                raise ValueError('Deliverable does not match saved source and stage')
            result['last_render'] = {'video': str(output), 'sha256': binding['sha256'],
                                     'receipt': str(receipt), 'mode': selected,
                                     'fingerprint': binding['fingerprint']}
        atomic_json(path, result)
    return result


def load(path):
    data = read(path)
    if data is None:
        raise FileNotFoundError('No saved project workspace: ' + str(path))
    result = dict(data)
    result['active_kind'] = ('composite' if data.get('active_composite') else
                             'composite_pending' if data.get('pending_composite') else 'scene')
    current = None
    if data.get('scene'):
        scene = Path(data['scene'])
        try:
            current = snapshot(scene)
            result['source_changes'] = differences(data['inputs'], current)
            result['source_available'] = True
        except OSError as error:
            result.update(source_available=False, source_error=str(error), source_changes=None)
    else:
        result.update(source_available=False, source_changes=None)
    video = data.get('last_render')
    if video:
        from project_state import fingerprint
        file = Path(video['video'])
        result['last_render_available'] = file.exists() and digest(file) == video['sha256']
        result['last_render_current'] = bool(result['last_render_available'] and
            result['source_available'] and fingerprint(current, video['mode']) == video.get('fingerprint')
            and video['mode'] == data['mode'])
    result['checkpoint_available'] = bool(data.get('checkpoint') and
        (Path(data['checkpoint'])/'checkpoint.json').is_file())
    if data.get('active_composite'):
        edit = data['active_composite']
        video = Path(edit['video'])
        receipt_file = Path(edit['receipt'])
        result['composite_available'] = bool(video.exists() and receipt_file.exists()
            and digest(video) == edit['sha256'] and digest(receipt_file) == edit['receipt_sha256'])
        result['composite_sources_current'] = bool(result['composite_available'] and
            all(Path(p).is_file() and digest(p) == sha for p, sha in edit['dependencies'].items()))
        if result['composite_sources_current']:
            from config import DEFAULTS
            receipt = json.loads(receipt_file.read_text())
            result['composite_sources_current'] = receipt['profile'] == DEFAULTS['export'][receipt['mode']]
    result['active_sources_current'] = (result.get('composite_sources_current', False)
        if result['active_kind'] == 'composite' else bool(result['active_kind']=='scene' and
        result['source_available'] and not result['source_changes']))
    if data.get('pending_composite'):
        result['pending_checkpoint_available'] = (
            Path(data['pending_composite']['checkpoint'])/'composite-checkpoint.json').is_file()
    return result


def begin_composite(recipe, output, checkpoint, *, path=None, mode='final', final_requested=False):
    """Save recovery paths before expensive work; not an artifact approval."""
    from execution import exclusive
    recipe = Path(recipe).resolve()
    path = Path(path).resolve() if path else default_path(recipe)
    with exclusive(path.with_suffix(path.suffix+'.lock')):
        previous = read(path)
        selected, authorized = select_mode(previous, mode, final_requested)
        result = {**(previous or {}), 'version':1, 'kind':'geomotion-workspace',
            'mode':selected, 'final_requested':authorized, 'status':'compositing',
            'pending_composite':{'recipe':str(recipe),'output':str(Path(output).resolve()),
                                 'checkpoint':str(Path(checkpoint).resolve())}}
        atomic_json(path,result)
    return result


def mark_status(path, status):
    from execution import exclusive
    path = Path(path).resolve()
    with exclusive(path.with_suffix(path.suffix+'.lock')):
        result = read(path)
        if result:
            result['status'] = status
            atomic_json(path,result)


def save_composite(recipe, output, checkpoint, *, path=None, mode='final', final_requested=False):
    """Reference the compositor's own proof; never manufacture a scene receipt."""
    from execution import exclusive
    recipe, output, checkpoint = (Path(p).resolve() for p in (recipe, output, checkpoint))
    path = Path(path).resolve() if path else default_path(recipe)
    receipt_file = output.with_suffix('.composite.json')
    receipt = json.loads(receipt_file.read_text())
    if receipt.get('kind') != 'native_overlay_composite' or receipt.get('sha256') != digest(output):
        raise ValueError('Current composite proof is required')
    source = receipt['source']
    if source['recipe'] != str(recipe) or receipt['mode'] != mode:
        raise ValueError('Composite proof does not match recipe/stage')
    dependencies = {str(recipe): source['recipe_sha256'], source['base_video']: source['base_sha256'],
        str(Path(source['base_checkpoint'])/'checkpoint.json'): source['checkpoint_sha256'],
        str(Path(source['base_video']).with_suffix('.render.json')): source['base_render_receipt_sha256'],
        **source['assets'], **{str(Path(__file__).with_name(p)): sha for p, sha in receipt['code'].items()},
        **{str(Path(source['base_checkpoint'])/(key+'.mp4')): item['source_sha256']
           for key, item in receipt['segments'].items()}}
    if any(not Path(p).is_file() or digest(p) != sha for p, sha in dependencies.items()):
        raise ValueError('Composite source proof is stale')
    with exclusive(path.with_suffix(path.suffix+'.lock')):
        saved = read(path)
        selected, authorized = select_mode(saved, mode, final_requested)
        result = {**(saved or {}), 'version': 1, 'kind': 'geomotion-workspace',
            'mode': selected, 'final_requested': authorized, 'status': 'composite_review_required',
            'active_composite': {'recipe': str(recipe), 'video': str(output), 'checkpoint': str(checkpoint),
                'receipt': str(receipt_file), 'receipt_sha256': digest(receipt_file),
                'sha256': receipt['sha256'], 'dependencies': dependencies}}
        result.pop('pending_composite',None)
        atomic_json(path, result)
    return result
