"""This file and its contents are licensed under the Apache License 2.0. Please see the included NOTICE for copyright information and LICENSE for a copy of the license.

[pxs] Infer a labeling config from one sample record.

A template only renders when the fields it references exist in the data, and the
69 built-in templates use fields (text, image, audio, chat, prompt) that rarely
match a real dataset. Instead of asking the installer to author XML, bootstrap
reads one record from the source repository and picks a config by field shape.

Rules run from the most specific shape to the most generic. The last rule still
returns a usable screen (every text field displayed, one review choice), because
a config that renders is worth more than an error that asks for hand-written XML.
Only records with no displayable field at all fall through to ``no-rule``.
"""

import json
from xml.sax.saxutils import escape

#: Extensions that make a string an asset rather than plain text.
IMAGE_EXT = ('.jpg', '.jpeg', '.png', '.webp', '.bmp', '.gif', '.tif', '.tiff')
AUDIO_EXT = ('.mp3', '.wav', '.m4a', '.flac', '.ogg', '.opus')
PDF_EXT = ('.pdf',)

#: Field names users give each side of a pair, ordered by specificity.
PROMPT_KEYS = ('instruction', 'prompt', 'question', 'query', 'user', 'input_text', 'input')
RESPONSE_KEYS = ('output', 'response', 'answer', 'completion', 'reply', 'assistant', 'target', 'gpt')
CHAT_KEYS = ('chat', 'messages', 'conversation', 'dialogue', 'history')
IMAGE_KEYS = ('image', 'img', 'image_url', 'picture', 'photo', 'url')
AUDIO_KEYS = ('audio', 'audio_url', 'wav', 'speech', 'recording')
PDF_KEYS = ('pdf', 'document', 'file')
TEXT_KEYS = ('text', 'content', 'sentence', 'document', 'review', 'comment', 'passage')

#: Fields that already carry a label, used to pick a classification screen.
LABEL_KEYS = ('label', 'labels', 'class', 'category', 'tag', 'tags', 'sentiment', 'intent', 'topic')

#: Reading-comprehension and sentence-pair shapes.
CONTEXT_KEYS = ('context', 'passage', 'document', 'article', 'paragraph', 'premise')
PAIR_KEYS = (
    ('sentence1', 'sentence2'),
    ('text_a', 'text_b'),
    ('premise', 'hypothesis'),
    ('query', 'passage'),
)

#: Larger files are skipped instead of being read whole.
MAX_SAMPLE_BYTES = 5 * 1024 * 1024

#: How many text fields the generic fallback renders.
GENERIC_FIELDS = 4

QUALITY_CHOICES = '<Choice value="优秀"/><Choice value="一般"/><Choice value="较差"/>'
REVIEW_CHOICES = '<Choice value="正确"/><Choice value="需要修改"/>'
NLI_CHOICES = '<Choice value="蕴含"/><Choice value="中立"/><Choice value="矛盾"/>'


def _suffix(value):
    return value.lower().split('?')[0]


def _is_asset(value, extensions):
    return isinstance(value, str) and _suffix(value).endswith(extensions)


def _is_chat(value):
    """Only the ``role``/``content`` shape renders in the Chat tag."""
    if not isinstance(value, list) or not value or not isinstance(value[0], dict):
        return False
    head = value[:3]
    return all('role' in item and 'content' in item for item in head)


def classify_field(value):
    """Return chat / image / audio / pdf / text / complex / empty."""
    if _is_chat(value):
        return 'chat'
    if isinstance(value, (list, dict)):
        return 'complex'
    if _is_asset(value, IMAGE_EXT):
        return 'image'
    if _is_asset(value, AUDIO_EXT):
        return 'audio'
    if _is_asset(value, PDF_EXT):
        return 'pdf'
    if isinstance(value, str) and value.strip():
        return 'text'
    return 'empty'


def _by_name(keys, candidates):
    lowered = {key.lower(): key for key in keys}
    for candidate in candidates:
        if candidate in lowered:
            return lowered[candidate]
    return None


def _by_type(keys, kinds, wanted):
    return next((key for key in keys if kinds.get(key) == wanted), None)


def _has_label(keys):
    return _by_name(keys, LABEL_KEYS) is not None


def _text(value):
    return f'value="${escape(str(value))}"'


def _display(key, name):
    return f'<Header value="{escape(key)}"/><Text name="{name}" {_text(key)}/>'


def infer_label_config(record):
    """Return ``(config, reason)``; ``config`` is None when the record is unusable."""
    keys = list(record.keys())
    kinds = {key: classify_field(record[key]) for key in keys}
    text_keys = [key for key in keys if kinds[key] == 'text']

    chat = _by_type(keys, kinds, 'chat') or _by_name(keys, CHAT_KEYS)
    if chat and kinds.get(chat) == 'chat':
        return (
            f'<View><Chat name="dialog" value="${chat}"/>'
            f'<Choices name="quality" toName="dialog">{QUALITY_CHOICES}</Choices></View>',
            f'chat:{chat}',
        )

    pdf = _by_type(keys, kinds, 'pdf') or _by_name(keys, PDF_KEYS)
    if pdf and kinds.get(pdf) == 'pdf':
        return (
            f'<View><Pdf name="doc" value="${pdf}"/>'
            f'<Choices name="review" toName="doc">{REVIEW_CHOICES}</Choices></View>',
            f'pdf:{pdf}',
        )

    image = _by_type(keys, kinds, 'image') or _by_name(keys, IMAGE_KEYS)
    if image and kinds.get(image) == 'image':
        if _has_label(keys):
            label = _by_name(keys, LABEL_KEYS)
            return (
                f'<View><Image name="pic" value="${image}"/>'
                f'<Choices name="label" toName="pic" value="${label}">{REVIEW_CHOICES}</Choices></View>',
                f'image-classification:{image}',
            )
        return (
            f'<View><Image name="pic" value="${image}"/>'
            f'<RectangleLabels name="boxes" toName="pic"><Label value="目标"/></RectangleLabels></View>',
            f'image-detection:{image}',
        )

    audio = _by_type(keys, kinds, 'audio') or _by_name(keys, AUDIO_KEYS)
    if audio and kinds.get(audio) == 'audio':
        return (
            f'<View><Audio name="clip" value="${audio}"/>'
            f'<TextArea name="transcript" toName="clip" editable="true"/></View>',
            f'audio:{audio}',
        )

    for left, right in PAIR_KEYS:
        a, b = _by_name(keys, (left,)), _by_name(keys, (right,))
        if a and b and a != b and kinds.get(a) == 'text' and kinds.get(b) == 'text':
            return (
                f'<View>{_display(a, "left")}{_display(b, "right")}'
                f'<Choices name="relation" toName="left">{NLI_CHOICES}</Choices></View>',
                f'pair:{a}/{b}',
            )

    prompt = _by_name(keys, PROMPT_KEYS)
    response = _by_name(keys, RESPONSE_KEYS)
    if prompt and response and prompt != response and kinds.get(prompt) == 'text' and kinds.get(response) == 'text':
        return (
            f'<View><Header value="提问"/><Text name="prompt" {_text(prompt)}/>'
            f'<Header value="模型回复"/><Text name="reply" {_text(response)}/>'
            f'<Choices name="grade" toName="reply">{QUALITY_CHOICES}</Choices></View>',
            f'qa-pair:{prompt}/{response}',
        )

    text = _by_name(keys, TEXT_KEYS) or (text_keys[0] if text_keys else None)
    if text:
        if _has_label(keys):
            label = _by_name(keys, LABEL_KEYS)
            return (
                f'<View><Text name="text" {_text(text)}/>'
                f'<Choices name="label" toName="text" value="${label}">{REVIEW_CHOICES}</Choices></View>',
                f'text-classification:{text}',
            )
        return (
            f'<View><Text name="text" {_text(text)}/>'
            f'<Choices name="label" toName="text"><Choice value="类别 A"/><Choice value="类别 B"/></Choices></View>',
            f'text:{text}',
        )

    # Generic fallback: show the text fields we have, offer one review choice.
    fields = text_keys[:GENERIC_FIELDS]
    if fields:
        body = ''.join(_display(key, f'field{index}') for index, key in enumerate(fields, start=1))
        return (
            f'<View>{body}<Choices name="review" toName="field1">{REVIEW_CHOICES}</Choices></View>',
            f'generic:{"/".join(fields)}',
        )

    return None, 'no-rule'


def describe_fields(record):
    """Human readable ``key: kind`` list used in error messages."""
    return ', '.join(f'{key}: {classify_field(value)}' for key, value in record.items())


def _parse_sample(blob):
    text = blob.decode('utf-8', 'replace').strip()
    try:
        data = json.loads(text)
        if isinstance(data, list):
            return data[0] if data else None
        return data
    except json.JSONDecodeError:
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                return json.loads(line)
            except json.JSONDecodeError:
                continue
    return None


def fetch_sample(client):
    """Return ``(path, record)`` for the first parsable record, or ``(None, None)``."""
    for obj in client.list_files(recursive=True):
        if not obj.path.lower().endswith(('.json', '.jsonl')):
            continue
        size = getattr(obj, 'size', 0) or 0
        if size > MAX_SAMPLE_BYTES:
            continue
        record = _parse_sample(client.read_bytes(obj.path))
        if isinstance(record, dict) and record:
            return obj.path, record
    return None, None
