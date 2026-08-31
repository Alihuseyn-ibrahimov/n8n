import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_PATH = ROOT / "n8n/demo-data/workflows/n8nSesliBilikYarisi01.json"

REQUIRED_TYPES = {
    "n8n-nodes-base.telegramTrigger",
    "n8n-nodes-base.telegram",
    "n8n-nodes-base.if",
    "n8n-nodes-base.switch",
    "n8n-nodes-base.merge",
    "@n8n/n8n-nodes-langchain.openAi",
    "@n8n/n8n-nodes-langchain.agent",
    "@n8n/n8n-nodes-langchain.lmChatOpenAi",
    "@n8n/n8n-nodes-langchain.memoryBufferWindow",
    "n8n-nodes-base.code",
    "@n8n/n8n-nodes-langchain.memoryManager",
    "@n8n/n8n-nodes-langchain.outputParserStructured",
}


class WorkflowGraphTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.wf = json.loads(WORKFLOW_PATH.read_text(encoding="utf-8"))
        cls.nodes = {n["name"]: n for n in cls.wf["nodes"]}
        cls.conns = cls.wf["connections"]

    def test_required_node_types_present(self):
        types = {n["type"] for n in self.wf["nodes"] if n["type"] != "n8n-nodes-base.stickyNote"}
        missing = REQUIRED_TYPES - types
        self.assertFalse(missing, f"missing node types: {missing}")

    def test_two_telegram_action_nodes(self):
        telegram = [n for n in self.wf["nodes"] if n["type"] == "n8n-nodes-base.telegram"]
        self.assertTrue(
            any(
                n["parameters"].get("resource") == "file"
                and n["parameters"].get("operation") == "get"
                for n in telegram
            ),
            "Get File node is required",
        )
        self.assertTrue(any(n["parameters"].get("operation") == "sendAudio" for n in telegram))

    def test_whisper_uses_azerbaijani(self):
        whisper = self.nodes["Whisper (STT)"]
        self.assertEqual(whisper["parameters"]["resource"], "audio")
        self.assertEqual(whisper["parameters"]["operation"], "transcribe")
        self.assertEqual(whisper["parameters"]["options"]["language"], "az")

    def test_tts_generates_audio(self):
        tts = self.nodes["Səsə çevir (TTS)"]
        self.assertEqual(tts["parameters"]["resource"], "audio")
        self.assertEqual(tts["parameters"]["operation"], "generate")
        self.assertIn("JSON-i ayır", tts["parameters"]["input"])

    def test_merge_appends_exclusive_branches(self):
        merge = self.nodes["Birləşdir"]
        self.assertEqual(merge["parameters"]["mode"], "append")
        self.assertEqual(self.conns["Səs → mətn"]["main"][0][0]["index"], 0)
        self.assertEqual(self.conns["Mətn mesajı"]["main"][0][0]["index"], 1)

    def test_text_and_voice_join_at_merge(self):
        self.assertEqual(self.conns["Səs mesajıdır?"]["main"][0][0]["node"], "Səs faylını endir")
        self.assertEqual(self.conns["Səs mesajıdır?"]["main"][1][0]["node"], "Mətn mesajı")
        self.assertEqual(self.conns["Səs faylını endir"]["main"][0][0]["node"], "Whisper (STT)")
        self.assertEqual(self.conns["Birləşdir"]["main"][0][0]["node"], "Viktorina agenti")

    def test_agent_structured_output_and_memory(self):
        agent = self.nodes["Viktorina agenti"]
        self.assertTrue(agent["parameters"]["hasOutputParser"])
        self.assertIn("JSON obyekti", agent["parameters"]["options"]["systemMessage"])
        memory = self.nodes["Söhbət yaddaşı"]
        self.assertEqual(memory["parameters"]["sessionIdType"], "customKey")
        self.assertIn("message.chat.id", memory["parameters"]["sessionKey"])
        self.assertEqual(
            self.conns["Söhbət yaddaşı"]["ai_memory"][0][0]["node"],
            "Viktorina agenti",
        )
        self.assertEqual(
            self.conns["Structured Output Parser"]["ai_outputParser"][0][0]["node"],
            "Viktorina agenti",
        )

    def test_switch_routes_five_game_states(self):
        switch = self.nodes["Vəziyyətə görə yönləndir"]
        keys = [rule["outputKey"] for rule in switch["parameters"]["rules"]["values"]]
        self.assertEqual(
            keys,
            ["mövzu_sorğusu", "yeni_sual", "statistika", "oyun_bitdi", "təmizləndi"],
        )
        outputs = self.conns["Vəziyyətə görə yönləndir"]["main"]
        self.assertEqual(outputs[0][0]["node"], "Səsə çevir (TTS)")
        self.assertEqual(outputs[1][0]["node"], "Səsə çevir (TTS)")
        self.assertEqual(outputs[2][0]["node"], "Səsə çevir (TTS)")
        self.assertEqual(outputs[3][0]["node"], "Yaddaşı təmizlə")
        self.assertEqual(outputs[4][0]["node"], "Yaddaşı təmizlə")

    def test_memory_manager_clears_all_on_end_or_reset(self):
        manager = self.nodes["Yaddaşı təmizlə"]
        self.assertEqual(manager["parameters"]["mode"], "delete")
        self.assertEqual(manager["parameters"]["deleteMode"], "all")
        self.assertEqual(
            self.conns["Yaddaş (silmək üçün)"]["ai_memory"][0][0]["node"],
            "Yaddaşı təmizlə",
        )
        clear = self.nodes["Yaddaş (silmək üçün)"]
        self.assertEqual(clear["parameters"]["sessionKey"], self.nodes["Söhbət yaddaşı"]["parameters"]["sessionKey"])
        self.assertEqual(self.conns["Yaddaşı təmizlə"]["main"][0][0]["node"], "Səsə çevir (TTS)")

    def test_code_node_allows_all_statuses(self):
        code = self.nodes["JSON-i ayır"]["parameters"]["jsCode"]
        for status in ("ask_topic", "question", "stats", "finished", "reset"):
            self.assertIn(f"'{status}'", code)
        self.assertIn("$('Birləşdir')", code)
        self.assertIn("chat_id", code)

    def test_audio_is_sent_back_to_same_chat(self):
        send = self.nodes["Audio göndər"]
        self.assertEqual(send["parameters"]["operation"], "sendAudio")
        self.assertTrue(send["parameters"]["binaryData"])
        self.assertIn("chat_id", send["parameters"]["chatId"])
        self.assertEqual(self.conns["Səsə çevir (TTS)"]["main"][0][0]["node"], "Audio göndər")


if __name__ == "__main__":
    unittest.main()
