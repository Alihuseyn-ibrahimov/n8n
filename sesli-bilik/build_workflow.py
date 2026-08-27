#!/usr/bin/env python3
"""Generate the n8n Voice Trivia workflow JSON."""

from __future__ import annotations

import json
from pathlib import Path

SYSTEM_MESSAGE = """Sən Telegram üzərindən Azərbaycan dilində səsli bilik yarışı (viktorina) aparan hakimsən.
Bütün reply_text sahəsi TTS ilə səsə çevriləcək — markdown, emoji, ulduz, hashtag istifadə etmə.
Cavabın YALNIZ bir JSON obyekti olmalıdır (əlavə mətn, izah və ya code fence yoxdur). JSON sözünü və aşağıdakı sahələri həmişə doldur.

Sahələr:
- status: "ask_topic" | "question" | "stats" | "finished" | "reset"
- reply_text: istifadəçiyə səslə oxunacaq Azərbaycan mətni
- score: indiyədək düzgün cavab sayı (0-10 tam ədəd)
- question_number: hazırda oynanan/soruşulan sualın nömrəsi (mövzu soruşulanda 0, birinci sualda 1, onuncu sualda 10)
- topic: mövzu adı
- difficulty: "asən" | "orta" | "çətin"
- is_correct: sual cavabı qiymətləndiriləndə true və ya false, digər hallarda null
- game_over: oyun bitibsə true, əks halda false

Oyun qaydaları:

1) Sıfırlama. İstifadəçi istənilən vaxt bunlardan birini desə: təmizlə, sıfırla, yenidən başla, reset, /start, /reset
   → status="reset", score=0, question_number=0, topic="", difficulty="", is_correct=null, game_over=false.
   reply_text oyunun sıfırlandığını desin və yenidən mövzu ilə çətinliyi soruşsun. Sual VERMƏ.

2) İlk mesaj / mövzu hələ seçilməyib. Yaddaş boşdursa və ya mövzu yoxdursa sual VERMƏ.
   → status="ask_topic", question_number=0, score=0, is_correct=null, game_over=false.
   Mövzu (məsələn tarix, coğrafiya, idman, elm, ümumi bilik) və səviyyəni (asən, orta, çətin) soruş.

3) Mövzu seçimi. İstifadəçi mövzu və/və ya səviyyə deyəndə 1-ci sualı ver.
   Aydın deyilsə default: topic="ümumi bilik", difficulty="orta".
   → status="question", question_number=1, score=0, is_correct=null, game_over=false.
   reply_text qısa təsdiq + birinci sual.

4) Cavab qiymətləndirmə. Aktiv suala cavab gələndə:
   - Semantik çevik ol: qısa, sinonim, kiçik orfoqrafiya səhvi qəbul oluna bilər.
   - Düzgündürsə score += 1, is_correct=true; səhvdirsə score eyni qalır, is_correct=false və qısa düzgün cavabı de.
   - Əgər cavab verilən sual 10-cu DEYİLSƏ: növbəti sualı eyni reply_text-ə əlavə et, question_number += 1, status="question", game_over=false.
   - Eyni sualı təkrarlama; yaddaşdakı əvvəlki suallara bax.

5) Oyunun sonu. 10-cu sualın cavabından sonra yeni sual VERMƏ.
   → status="finished", question_number=10, game_over=true, is_correct=true/false.
   reply_text-də yekun: "10 sualdan X-i düzgün cavablandırdınız" və qısa rəy.
   Yenidən oynamaq üçün mövzu seçməyi və ya sıfırlamağı təklif et.

6) Statistika sorğusu. "neçənci sualdayıq", "xalım nədir", "nəticəm", "hansı mövzudayıq" kimi status sualları CAVAB DEYİL.
   Qiymətləndirmə, score dəyişikliyi və sual dəyişikliyi YOXDUR.
   → status="stats", is_correct=null, game_over=false, eyni question_number və score.
   reply_text-də cari statistika (sual N/10, xal, mövzu, səviyyə) və əgər aktiv sual varsa onu təkrarla.

7) Suallar qısa və aydın olsun (bir cümləlik sual yetər). Cavab açığı tək fakt olsun.
   reply_text TTS üçün təbii danışıq dili olsun, 4000 simvoldan qısa.
"""

JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "status": {
            "type": "string",
            "description": "ask_topic, question, stats, finished və ya reset",
        },
        "reply_text": {"type": "string"},
        "score": {"type": "number"},
        "question_number": {"type": "number"},
        "topic": {"type": "string"},
        "difficulty": {"type": "string"},
        "is_correct": {"type": ["boolean", "null"]},
        "game_over": {"type": "boolean"},
    },
    "required": [
        "status",
        "reply_text",
        "score",
        "question_number",
        "topic",
        "difficulty",
        "game_over",
    ],
}

PARSE_JS = r"""
const trigger = $('Telegram Trigger').first().json;
const merged = $('Birləşdir').first().json;
const root = $input.first().json;
let data = root.output !== undefined ? root.output : root;

if (typeof data === 'string') {
  const trimmed = data.trim().replace(/^```(?:json)?\s*/i, '').replace(/\s*```$/i, '');
  try {
    data = JSON.parse(trimmed);
  } catch (error) {
    data = { status: 'ask_topic', reply_text: trimmed || 'Zəhmət olmasa təkrar edin.' };
  }
}

if (data && typeof data === 'object' && data.output && typeof data.output === 'object' && data.output.status) {
  data = data.output;
}

const allowed = ['ask_topic', 'question', 'stats', 'finished', 'reset'];
const status = allowed.includes(data.status) ? data.status : 'ask_topic';
let replyText = String(data.reply_text || 'Zəhmət olmasa təkrar edin.');
if (replyText.length > 4000) {
  replyText = replyText.slice(0, 4000);
}

const chatId = merged.chat_id || trigger.message?.chat?.id;
return [{
  json: {
    status,
    reply_text: replyText,
    score: Number.isFinite(Number(data.score)) ? Number(data.score) : 0,
    question_number: Number.isFinite(Number(data.question_number)) ? Number(data.question_number) : 0,
    topic: String(data.topic || 'ümumi bilik'),
    difficulty: String(data.difficulty || 'orta'),
    is_correct: data.is_correct === true ? true : data.is_correct === false ? false : null,
    game_over: Boolean(data.game_over) || status === 'finished',
    chat_id: String(chatId),
    session_key: merged.session_key || ('trivia_' + chatId),
    user_text: merged.user_text || '',
    source: merged.source || 'text',
  }
}];
""".strip()

TELEGRAM_CRED = {"telegramApi": {"id": "telegram-bot", "name": "Telegram Bot"}}
OPENAI_CRED = {"openAiApi": {"id": "openai-api", "name": "OpenAI"}}


def switch_rule(rule_id: str, value: str, output_key: str) -> dict:
    return {
        "conditions": {
            "options": {
                "caseSensitive": True,
                "leftValue": "",
                "typeValidation": "strict",
                "version": 2,
            },
            "conditions": [
                {
                    "id": rule_id,
                    "leftValue": "={{ $json.status }}",
                    "rightValue": value,
                    "operator": {"type": "string", "operation": "equals"},
                }
            ],
            "combinator": "and",
        },
        "renameOutput": True,
        "outputKey": output_key,
    }


def set_fields(assignments: list[tuple[str, str, str]], include_others: bool = True) -> dict:
    items = []
    for aid, name, value in assignments:
        items.append({"id": aid, "name": name, "value": value, "type": "string"})
    params: dict = {
        "assignments": {"assignments": items},
        "options": {},
    }
    if include_others:
        params["includeOtherFields"] = True
    return params


nodes = [
    {
        "parameters": {
            "content": "## 1. Giriş kanalı\nTelegram həm mətn, həm səs qəbul edir.\nSəs → fayl endir → Whisper (az) → mətn.\nMətn birbaşa gedir.\n**Birləşdir (Merge, append)** — yalnız bir budaq gəlsə belə davam edir.",
            "height": 320,
            "width": 520,
            "color": 5,
        },
        "id": "note-giris",
        "name": "Qeyd: giriş",
        "type": "n8n-nodes-base.stickyNote",
        "typeVersion": 1,
        "position": [-80, 40],
    },
    {
        "parameters": {
            "content": "## 2. Oyun agenti\nLangChain Agent + OpenAI Chat Model.\nWindow Buffer Memory session key = `trivia_{chat_id}`.\nÇıxış Structured Output Parser ilə JSON-dur; Code node sahələri sabitləyir.",
            "height": 300,
            "width": 460,
            "color": 6,
        },
        "id": "note-agent",
        "name": "Qeyd: agent",
        "type": "n8n-nodes-base.stickyNote",
        "typeVersion": 1,
        "position": [1180, 40],
    },
    {
        "parameters": {
            "content": "## 3. Marşrut + TTS + yaddaş\nSwitch: mövzu sorğusu / yeni sual / statistika / oyun bitdi / təmizləndi.\nBitdi və sıfırlama → Chat Memory Manager bütün mesajları silir.\nSonra TTS və Telegram audio.",
            "height": 300,
            "width": 480,
            "color": 4,
        },
        "id": "note-route",
        "name": "Qeyd: marşrut",
        "type": "n8n-nodes-base.stickyNote",
        "typeVersion": 1,
        "position": [2100, 40],
    },
    {
        "parameters": {
            "updates": ["message"],
            "additionalFields": {},
        },
        "id": "node-tg-trigger",
        "name": "Telegram Trigger",
        "type": "n8n-nodes-base.telegramTrigger",
        "typeVersion": 1.1,
        "position": [0, 400],
        "webhookId": "a7c3e91b-4d2f-4b6a-9e10-8c2f1d0b4e7a",
        "credentials": TELEGRAM_CRED,
    },
    {
        "parameters": {
            "conditions": {
                "options": {
                    "caseSensitive": True,
                    "leftValue": "",
                    "typeValidation": "loose",
                    "version": 2,
                },
                "conditions": [
                    {
                        "id": "cond-voice",
                        "leftValue": "={{ !!($json.message.voice || $json.message.audio) }}",
                        "rightValue": "",
                        "operator": {
                            "type": "boolean",
                            "operation": "true",
                            "singleValue": True,
                        },
                    }
                ],
                "combinator": "and",
            },
            "looseTypeValidation": True,
            "options": {},
        },
        "id": "node-if-voice",
        "name": "Səs mesajıdır?",
        "type": "n8n-nodes-base.if",
        "typeVersion": 2.2,
        "position": [240, 400],
    },
    {
        "parameters": {
            "resource": "file",
            "operation": "get",
            "fileId": "={{ $json.message.voice?.file_id || $json.message.audio?.file_id }}",
            "download": True,
            "additionalFields": {"mimeType": "audio/ogg"},
        },
        "id": "node-tg-getfile",
        "name": "Səs faylını endir",
        "type": "n8n-nodes-base.telegram",
        "typeVersion": 1.2,
        "position": [500, 220],
        "credentials": TELEGRAM_CRED,
    },
    {
        "parameters": {
            "resource": "audio",
            "operation": "transcribe",
            "binaryPropertyName": "data",
            "options": {"language": "az"},
        },
        "id": "node-whisper",
        "name": "Whisper (STT)",
        "type": "@n8n/n8n-nodes-langchain.openAi",
        "typeVersion": 1.8,
        "position": [740, 220],
        "credentials": OPENAI_CRED,
    },
    {
        "parameters": set_fields(
            [
                (
                    "asg-voice-text",
                    "user_text",
                    "={{ $json.text }}",
                ),
                (
                    "asg-voice-chat",
                    "chat_id",
                    "={{ String($('Telegram Trigger').item.json.message.chat.id) }}",
                ),
                (
                    "asg-voice-session",
                    "session_key",
                    "={{ 'trivia_' + String($('Telegram Trigger').item.json.message.chat.id) }}",
                ),
                ("asg-voice-source", "source", "voice"),
            ],
            include_others=False,
        ),
        "id": "node-set-voice",
        "name": "Səs → mətn",
        "type": "n8n-nodes-base.set",
        "typeVersion": 3.4,
        "position": [980, 220],
    },
    {
        "parameters": set_fields(
            [
                (
                    "asg-text-text",
                    "user_text",
                    "={{ $json.message.text || $json.message.caption || '' }}",
                ),
                (
                    "asg-text-chat",
                    "chat_id",
                    "={{ String($json.message.chat.id) }}",
                ),
                (
                    "asg-text-session",
                    "session_key",
                    "={{ 'trivia_' + String($json.message.chat.id) }}",
                ),
                ("asg-text-source", "source", "text"),
            ],
            include_others=False,
        ),
        "id": "node-set-text",
        "name": "Mətn mesajı",
        "type": "n8n-nodes-base.set",
        "typeVersion": 3.4,
        "position": [740, 580],
    },
    {
        "parameters": {
            "mode": "append",
            "numberInputs": 2,
        },
        "id": "node-merge",
        "name": "Birləşdir",
        "type": "n8n-nodes-base.merge",
        "typeVersion": 3.1,
        "position": [1220, 400],
    },
    {
        "parameters": {
            "promptType": "define",
            "text": "={{ $json.user_text }}",
            "hasOutputParser": True,
            "options": {
                "systemMessage": SYSTEM_MESSAGE,
                "maxIterations": 4,
            },
        },
        "id": "node-agent",
        "name": "Viktorina agenti",
        "type": "@n8n/n8n-nodes-langchain.agent",
        "typeVersion": 2.2,
        "position": [1480, 400],
    },
    {
        "parameters": {
            "model": {
                "__rl": True,
                "value": "gpt-4o-mini",
                "mode": "id",
            },
            "options": {
                "temperature": 0.4,
                "responseFormat": "json_object",
            },
        },
        "id": "node-llm",
        "name": "OpenAI Chat Model",
        "type": "@n8n/n8n-nodes-langchain.lmChatOpenAi",
        "typeVersion": 1.2,
        "position": [1380, 660],
        "credentials": OPENAI_CRED,
    },
    {
        "parameters": {
            "sessionIdType": "customKey",
            "sessionKey": "={{ 'trivia_' + String($('Telegram Trigger').item.json.message.chat.id) }}",
            "contextWindowLength": 30,
        },
        "id": "node-memory-agent",
        "name": "Söhbət yaddaşı",
        "type": "@n8n/n8n-nodes-langchain.memoryBufferWindow",
        "typeVersion": 1.3,
        "position": [1540, 660],
    },
    {
        "parameters": {
            "schemaType": "manual",
            "inputSchema": json.dumps(JSON_SCHEMA, ensure_ascii=False, indent=2),
            "autoFix": False,
        },
        "id": "node-parser",
        "name": "Structured Output Parser",
        "type": "@n8n/n8n-nodes-langchain.outputParserStructured",
        "typeVersion": 1.2,
        "position": [1720, 660],
    },
    {
        "parameters": {"jsCode": PARSE_JS},
        "id": "node-code",
        "name": "JSON-i ayır",
        "type": "n8n-nodes-base.code",
        "typeVersion": 2,
        "position": [1760, 400],
    },
    {
        "parameters": {
            "mode": "rules",
            "rules": {
                "values": [
                    switch_rule("rule-ask", "ask_topic", "mövzu_sorğusu"),
                    switch_rule("rule-q", "question", "yeni_sual"),
                    switch_rule("rule-stats", "stats", "statistika"),
                    switch_rule("rule-done", "finished", "oyun_bitdi"),
                    switch_rule("rule-reset", "reset", "təmizləndi"),
                ]
            },
            "options": {
                "fallbackOutput": "extra",
                "renameFallbackOutput": "digər",
            },
        },
        "id": "node-switch",
        "name": "Vəziyyətə görə yönləndir",
        "type": "n8n-nodes-base.switch",
        "typeVersion": 3.2,
        "position": [2000, 400],
    },
    {
        "parameters": {
            "mode": "delete",
            "deleteMode": "all",
        },
        "id": "node-memory-mgr",
        "name": "Yaddaşı təmizlə",
        "type": "@n8n/n8n-nodes-langchain.memoryManager",
        "typeVersion": 1.1,
        "position": [2280, 640],
    },
    {
        "parameters": {
            "sessionIdType": "customKey",
            "sessionKey": "={{ 'trivia_' + String($('Telegram Trigger').item.json.message.chat.id) }}",
            "contextWindowLength": 30,
        },
        "id": "node-memory-clear",
        "name": "Yaddaş (silmək üçün)",
        "type": "@n8n/n8n-nodes-langchain.memoryBufferWindow",
        "typeVersion": 1.3,
        "position": [2280, 860],
    },
    {
        "parameters": {
            "resource": "audio",
            "operation": "generate",
            "input": "={{ $('JSON-i ayır').item.json.reply_text }}",
            "voice": "nova",
            "options": {
                "response_format": "mp3",
                "binaryPropertyOutput": "data",
            },
        },
        "id": "node-tts",
        "name": "Səsə çevir (TTS)",
        "type": "@n8n/n8n-nodes-langchain.openAi",
        "typeVersion": 1.8,
        "position": [2560, 400],
        "credentials": OPENAI_CRED,
    },
    {
        "parameters": {
            "resource": "message",
            "operation": "sendAudio",
            "chatId": "={{ $('JSON-i ayır').item.json.chat_id }}",
            "binaryData": True,
            "binaryPropertyName": "data",
            "additionalFields": {
                "caption": "=Sual {{ $('JSON-i ayır').item.json.question_number }}/10 · Xal: {{ $('JSON-i ayır').item.json.score }}",
                "title": "Səsli Bilik Yarışı",
            },
        },
        "id": "node-tg-audio",
        "name": "Audio göndər",
        "type": "n8n-nodes-base.telegram",
        "typeVersion": 1.2,
        "position": [2820, 400],
        "credentials": TELEGRAM_CRED,
    },
]

connections = {
    "Telegram Trigger": {
        "main": [[{"node": "Səs mesajıdır?", "type": "main", "index": 0}]]
    },
    "Səs mesajıdır?": {
        "main": [
            [{"node": "Səs faylını endir", "type": "main", "index": 0}],
            [{"node": "Mətn mesajı", "type": "main", "index": 0}],
        ]
    },
    "Səs faylını endir": {
        "main": [[{"node": "Whisper (STT)", "type": "main", "index": 0}]]
    },
    "Whisper (STT)": {
        "main": [[{"node": "Səs → mətn", "type": "main", "index": 0}]]
    },
    "Səs → mətn": {
        "main": [[{"node": "Birləşdir", "type": "main", "index": 0}]]
    },
    "Mətn mesajı": {
        "main": [[{"node": "Birləşdir", "type": "main", "index": 1}]]
    },
    "Birləşdir": {
        "main": [[{"node": "Viktorina agenti", "type": "main", "index": 0}]]
    },
    "Viktorina agenti": {
        "main": [[{"node": "JSON-i ayır", "type": "main", "index": 0}]]
    },
    "JSON-i ayır": {
        "main": [[{"node": "Vəziyyətə görə yönləndir", "type": "main", "index": 0}]]
    },
    "Vəziyyətə görə yönləndir": {
        "main": [
            [{"node": "Səsə çevir (TTS)", "type": "main", "index": 0}],
            [{"node": "Səsə çevir (TTS)", "type": "main", "index": 0}],
            [{"node": "Səsə çevir (TTS)", "type": "main", "index": 0}],
            [{"node": "Yaddaşı təmizlə", "type": "main", "index": 0}],
            [{"node": "Yaddaşı təmizlə", "type": "main", "index": 0}],
            [{"node": "Səsə çevir (TTS)", "type": "main", "index": 0}],
        ]
    },
    "Yaddaşı təmizlə": {
        "main": [[{"node": "Səsə çevir (TTS)", "type": "main", "index": 0}]]
    },
    "Səsə çevir (TTS)": {
        "main": [[{"node": "Audio göndər", "type": "main", "index": 0}]]
    },
    "OpenAI Chat Model": {
        "ai_languageModel": [
            [{"node": "Viktorina agenti", "type": "ai_languageModel", "index": 0}]
        ]
    },
    "Söhbət yaddaşı": {
        "ai_memory": [[{"node": "Viktorina agenti", "type": "ai_memory", "index": 0}]]
    },
    "Structured Output Parser": {
        "ai_outputParser": [
            [{"node": "Viktorina agenti", "type": "ai_outputParser", "index": 0}]
        ]
    },
    "Yaddaş (silmək üçün)": {
        "ai_memory": [[{"node": "Yaddaşı təmizlə", "type": "ai_memory", "index": 0}]]
    },
}

workflow = {
    "createdAt": "2026-08-27T16:00:00.000Z",
    "updatedAt": "2026-08-27T16:00:00.000Z",
    "id": "n8nSesliBilikYarisi01",
    "name": "Səsli Bilik Yarışı (Telegram)",
    "active": False,
    "nodes": nodes,
    "connections": connections,
    "settings": {"executionOrder": "v1"},
    "staticData": None,
    "meta": {"templateCredsSetupCompleted": False},
    "pinData": {},
    "versionId": "c1e8b4a0-9d27-4f1e-8a55-0b91c3d2e4f6",
    "triggerCount": 0,
    "tags": [],
}


def main() -> None:
    out = Path(__file__).resolve().parent.parent / "n8n/demo-data/workflows/n8nSesliBilikYarisi01.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(workflow, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {out} ({len(nodes)} nodes)")


if __name__ == "__main__":
    main()
