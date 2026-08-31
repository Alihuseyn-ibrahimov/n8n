import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from parse_agent_output import parse_agent_output


CTX = {
    "chat_id": "42",
    "session_key": "trivia_42",
    "user_text": "Bakı",
    "source": "voice",
}


class ParseAgentOutputTest(unittest.TestCase):
    def test_structured_parser_wrapper(self):
        parsed = parse_agent_output(
            {
                "output": {
                    "status": "question",
                    "reply_text": "Düzgün. İkinci sual: Xəzər dənizi haradadır?",
                    "score": 1,
                    "question_number": 2,
                    "topic": "coğrafiya",
                    "difficulty": "orta",
                    "is_correct": True,
                    "game_over": False,
                }
            },
            CTX,
        )
        self.assertEqual(parsed["status"], "question")
        self.assertEqual(parsed["score"], 1)
        self.assertEqual(parsed["question_number"], 2)
        self.assertTrue(parsed["is_correct"])
        self.assertEqual(parsed["chat_id"], "42")
        self.assertFalse(parsed["game_over"])

    def test_fenced_json_string(self):
        raw = '```json\n{"status":"stats","reply_text":"İkinci sualdasınız, xal 1.","score":1,"question_number":2,"topic":"coğrafiya","difficulty":"orta","is_correct":null,"game_over":false}\n```'
        parsed = parse_agent_output({"output": raw}, CTX)
        self.assertEqual(parsed["status"], "stats")
        self.assertIsNone(parsed["is_correct"])
        self.assertEqual(parsed["source"], "voice")

    def test_finished_forces_game_over(self):
        parsed = parse_agent_output(
            {
                "status": "finished",
                "reply_text": "10 sualdan 7-si düzgün.",
                "score": 7,
                "question_number": 10,
                "topic": "ümumi bilik",
                "difficulty": "orta",
                "is_correct": False,
                "game_over": False,
            },
            CTX,
        )
        self.assertEqual(parsed["status"], "finished")
        self.assertTrue(parsed["game_over"])

    def test_unknown_status_falls_back_to_ask_topic(self):
        parsed = parse_agent_output({"status": "hello", "reply_text": "Salam"}, CTX)
        self.assertEqual(parsed["status"], "ask_topic")
        self.assertEqual(parsed["topic"], "ümumi bilik")
        self.assertEqual(parsed["difficulty"], "orta")

    def test_reset_clears_progress_fields_when_missing(self):
        parsed = parse_agent_output({"status": "reset", "reply_text": "Oyun sıfırlandı."}, CTX)
        self.assertEqual(parsed["status"], "reset")
        self.assertEqual(parsed["score"], 0)
        self.assertEqual(parsed["question_number"], 0)
        self.assertFalse(parsed["game_over"])


if __name__ == "__main__":
    unittest.main()
